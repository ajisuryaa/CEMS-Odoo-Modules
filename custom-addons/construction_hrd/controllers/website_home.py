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


class CemsWebsiteHome(Website):
    """Serve the CEMS split login layout as the website homepage (`/`)."""

    @http.route('/', type='http', auth='public', website=True, sitemap=True)
    def index(self, **kw):
        # Logged-in users: go to portal hub (this page is the pre-login gateway)
        if request.session.uid and request.env.user and not request.env.user._is_public():
            return request.redirect('/my')

        return request.render(
            'construction_hrd.cems_login_homepage',
            _cems_login_values(
                login=request.params.get('login', ''),
                error=request.params.get('error'),
                redirect=request.params.get('redirect') or '/my',
            ),
        )


class CemsWebsiteLogin(Home):
    """Authenticate against the Odoo DB; stay on CEMS homepage on failure."""

    def _cems_prepare_public_env(self):
        """Ensure a public env when the session has no uid yet."""
        if request.env.uid is not None:
            return
        if request.session.uid is None:
            request.env['ir.http']._auth_method_public()
        else:
            request.update_env(user=request.session.uid)

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
        redirect = redirect or '/my'

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
