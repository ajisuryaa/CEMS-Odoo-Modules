# -*- coding: utf-8 -*-
import logging

import odoo
import odoo.exceptions
import werkzeug
from odoo import http
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.web.controllers.home import CREDENTIAL_PARAMS
from odoo.addons.web.controllers.utils import ensure_db
from odoo.addons.web.models.res_users import SKIP_CAPTCHA_LOGIN
from odoo.addons.website.controllers.main import Website
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools.translate import _
from werkzeug.urls import url_encode

_logger = logging.getLogger(__name__)


def _cems_login_values(login='', error=None, redirect='/my'):
    """QWeb values for the CEMS login homepage."""
    return {
        'login': login or '',
        'error': error,
        'redirect': redirect or '/my',
    }


def _cems_sanitize_redirect(redirect):
    """Keep post-login redirect on-site; default to portal hub."""
    if not redirect or not isinstance(redirect, str):
        return '/my'
    redirect = redirect.strip()
    # Reject absolute / protocol-relative URLs (open-redirect)
    if redirect.startswith('//') or '://' in redirect:
        return '/my'
    if not redirect.startswith('/'):
        return '/my'
    return redirect


class CemsWebsiteHome(Website):
    """Serve the CEMS split login layout as the website homepage (`/`)."""

    @http.route('/', type='http', auth='public', website=True, sitemap=True)
    def index(self, **kw):
        redirect = _cems_sanitize_redirect(request.params.get('redirect') or '/my')
        # Logged-in users: go to intended page (or portal hub)
        if request.session.uid and request.env.user and not request.env.user._is_public():
            return request.redirect(redirect)

        return request.render(
            'construction_hrd.cems_login_homepage',
            _cems_login_values(
                login=request.params.get('login', ''),
                error=request.params.get('error'),
                redirect=redirect,
            ),
        )


class CemsWebsiteLogin(AuthSignupHome):
    """CEMS login divert + disable public signup + themed reset password.

    Inherits ``AuthSignupHome`` (which inherits ``Home``) so signup / reset
    routes stay on one controller and do not shadow ``/web/login``.
    """

    def _cems_prepare_public_env(self):
        """Ensure a public env when the session has no uid yet."""
        if request.env.uid is not None:
            return
        if request.session.uid is None:
            request.env['ir.http']._auth_method_public()
        else:
            request.update_env(user=request.session.uid)

    @http.route(
        '/web/login',
        type='http',
        auth='none',
        readonly=False,
        sitemap=False,
    )
    def web_login(self, redirect=None, **kw):
        """Override stock login: always use CEMS homepage at ``/``."""
        ensure_db()
        redirect = _cems_sanitize_redirect(redirect or request.params.get('redirect'))

        # Already authenticated → honour redirect (same idea as core GET behaviour)
        if request.session.uid:
            return request.redirect(redirect)

        query = {'redirect': redirect}
        login = request.params.get('login')
        error = request.params.get('error')
        if login:
            query['login'] = login
        if error:
            query['error'] = error
        return request.redirect_query('/', query=query, code=303)

    @http.route(
        '/cems/login',
        type='http',
        auth='public',
        methods=['POST'],
        website=True,
        sitemap=False,
        csrf=True,
    )
    def cems_login(self, redirect='/my', **post):
        ensure_db()
        self._cems_prepare_public_env()

        login = (post.get('login') or '').strip()
        redirect = _cems_sanitize_redirect(redirect or post.get('redirect') or '/my')

        try:
            credential = {
                key: value
                for key, value in post.items()
                if key in CREDENTIAL_PARAMS and value
            }
            credential.setdefault('type', 'password')
            if request.env['res.users']._should_captcha_login(credential):
                request.env['ir.http']._verify_request_recaptcha_token('login')
            auth_info = request.session.authenticate(request.env, credential)
            _logger.info('CEMS portal login success for login=%s uid=%s', login, auth_info.get('uid'))
            return request.redirect(
                self._login_redirect(auth_info['uid'], redirect=redirect)
            )
        except odoo.exceptions.AccessDenied as err:
            if err.args == odoo.exceptions.AccessDenied().args:
                error = _('Wrong login/password')
            else:
                error = err.args[0]
            _logger.warning('CEMS portal login denied for login=%s', login)
            return request.render(
                'construction_hrd.cems_login_homepage',
                _cems_login_values(login=login, error=error, redirect=redirect),
            )
        except Exception:
            _logger.exception('CEMS portal login unexpected error for login=%s', login)
            return request.render(
                'construction_hrd.cems_login_homepage',
                _cems_login_values(
                    login=login,
                    error=_('An unexpected error occurred. Please try again.'),
                    redirect=redirect,
                ),
            )

    # --- Point 9 ---
    @http.route(
        '/web/signup',
        type='http',
        auth='public',
        website=True,
        sitemap=False,
    )
    def web_auth_signup(self, *args, **kw):
        return request.redirect('/')

    # --- Point 10 ---
    @http.route(
        '/web/reset_password',
        type='http',
        auth='public',
        website=True,
        sitemap=False,
        captcha='password_reset',
    )
    def web_auth_reset_password(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()

        if not qcontext.get('token') and not qcontext.get('reset_password_enabled'):
            raise werkzeug.exceptions.NotFound()

        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                if qcontext.get('token'):
                    self.do_signup(qcontext, do_login=False)
                    request.update_context(skip_captcha_login=SKIP_CAPTCHA_LOGIN)
                    qcontext['message'] = _("Your password has been reset successfully.")
                else:
                    login = qcontext.get('login')
                    assert login, _("No login provided.")
                    _logger.info(
                        "CEMS password reset attempt for <%s> by user <%s> from %s",
                        login,
                        request.env.user.login,
                        request.httprequest.remote_addr,
                    )
                    request.env['res.users'].sudo().reset_password(login)
                    qcontext['message'] = _(
                        "Password reset instructions sent to your email address."
                    )
            except UserError as e:
                qcontext['error'] = e.args[0]
            except SignupError:
                qcontext['error'] = _("Could not reset your password")
                _logger.exception('CEMS error when resetting password')
            except Exception as e:
                qcontext['error'] = str(e)

        elif 'signup_email' in qcontext:
            user = request.env['res.users'].sudo().search(
                [('email', '=', qcontext.get('signup_email')), ('state', '!=', 'new')],
                limit=1,
            )
            if user:
                return request.redirect(
                    '/web/login?%s' % url_encode({'login': user.login, 'redirect': '/my'})
                )

        response = request.render('construction_hrd.cems_reset_password', qcontext)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response

    def get_auth_signup_config(self):
        config = super().get_auth_signup_config()
        # Workers are provisioned via Access Type — never enable public signup UI.
        config['signup_enabled'] = False
        return config
