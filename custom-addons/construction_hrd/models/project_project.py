# -*- coding: utf-8 -*-
from odoo import _, api, models


class ProjectProject(models.Model):
    """Portal + mail notifications when users join the Site Team."""

    _inherit = 'project.project'

    def _cems_notify_site_team_added(self, old_members_by_id):
        Notification = self.env['cems.portal.notification']
        for project in self:
            previous = old_members_by_id.get(project.id, self.env['res.users'])
            added = project.cems_member_ids - previous
            if not added:
                continue
            Notification._cems_notify_users(
                added,
                title=_('Added to Site Team'),
                body=_(
                    'You were added to the Site Team for project "%s".',
                    project.display_name,
                ),
                notification_type='project',
                url='/my/projects/%s' % project.id,
                res_model='project.project',
                res_id=project.id,
                mail_record=project,
                mail_subject=_('Added to Site Team: %s', project.display_name),
            )

    @api.model_create_multi
    def create(self, vals_list):
        projects = super().create(vals_list)
        if self.env.context.get('cems_skip_site_team_hooks'):
            return projects
        empty = self.env['res.users']
        old_members = {project.id: empty for project in projects}
        projects._cems_notify_site_team_added(old_members)
        return projects

    def write(self, vals):
        track = 'cems_member_ids' in vals or 'cems_engineer_ids' in vals
        skip = self.env.context.get('cems_skip_site_team_hooks')
        old_members = (
            {project.id: project.cems_member_ids for project in self}
            if track and not skip
            else {}
        )
        res = super().write(vals)
        if skip:
            return res
        if track:
            self._cems_notify_site_team_added(old_members)
        return res
