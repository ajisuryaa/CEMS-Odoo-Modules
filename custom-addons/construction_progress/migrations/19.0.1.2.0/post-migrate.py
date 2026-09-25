# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """Backfill portal share for existing Site Team members."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    projects = env['project.project'].search([('cems_member_ids', '!=', False)])
    projects._cems_sync_site_team_portal_access()
