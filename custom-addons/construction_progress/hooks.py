# -*- coding: utf-8 -*-


def post_init_hook(env):
    """After install: Site Engineers → Site Team + portal share."""
    projects = env['project.project'].search([])
    projects._cems_sync_engineers_into_members()
    projects._cems_sync_site_team_portal_access()
