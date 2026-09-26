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


class CemsWebsiteHome(Website):
    """Serve the CEMS split login layout as the website homepage (`/`)."""

    @http.route('/', type='http', auth='public', website=True, sitemap=True)
    def index(self, **kw):
        # Logged-in users: go to portal hub (this page is the pre-login gateway)
        if request.session.uid and request.env.user and not request.env.user._is_public():
            return request.redirect('/my')

        values = {
            'login': request.params.get('login', ''),
            'error': request.params.get('error'),
            'redirect': request.params.get('redirect') or '/my',
        }
        return request.render('construction_hrd.cems_login_homepage', values)


class CemsWebsiteLogin(Home):
    """Authenticate against the Odoo DB and return to the CEMS homepage on failure."""

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

        if request.env.uid is None:
            if request.session.uid is None:
                request.env['ir.http']._auth_method_public()
            else:
                request.update_env(user=request.session.uid)

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
            return request.redirect(
                self._login_redirect(auth_info['uid'], redirect=redirect)
            )
        except odoo.exceptions.AccessDenied as err:
            if err.args == odoo.exceptions.AccessDenied().args:
                error = _('Wrong login/password')
            else:
                error = err.args[0]
            return request.render(
                'construction_hrd.cems_login_homepage',
                {
                    'login': login,
                    'error': error,
                    'redirect': redirect,
                },
            )
