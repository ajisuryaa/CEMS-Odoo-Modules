# -*- coding: utf-8 -*-
import logging

import odoo
import odoo.exceptions
from odoo import http
from odoo.http import request
from odoo.tools.translate import _

from odoo.addons.web.controllers.home import CREDENTIAL_PARAMS, Home
from odoo.addons.web.controllers.utils import ensure_db
from odoo.addons.website.controllers.main import Website

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


class CemsWebsiteLogin(Home):
    """Authenticate against the Odoo DB; stay on CEMS homepage on failure.

    Also divert the stock ``/web/login`` page to the CEMS homepage so
    session-expired redirects land on the branded portal login.
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
