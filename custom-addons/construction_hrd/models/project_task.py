# -*- coding: utf-8 -*-
from odoo import _, api, models


class ProjectTask(models.Model):
    """Portal feed when a user is assigned to a task."""

    _inherit = 'project.task'

    def _cems_notify_task_assignees(self, users_per_task):
        Notification = self.env['cems.portal.notification']
        for task, users in users_per_task.items():
            added = users - self.env.user
            if not added:
                continue
            Notification._cems_notify_users(
                added,
                title=_('New task assigned'),
                body=_(
                    '%s was assigned to you.',
                    task.display_name,
                ),
                notification_type='task',
                url='/my/tasks/%s' % task.id,
                res_model='project.task',
                res_id=task.id,
                # Project already sends native assign mail; keep portal feed only.
                mail_record=None,
            )

    @api.model_create_multi
    def create(self, vals_list):
        tasks = super().create(vals_list)
        if self.env.context.get('mail_auto_subscribe_no_notify') or self.env.context.get(
            'cems_skip_portal_notify'
        ):
            return tasks
        self._cems_notify_task_assignees({
            task: task.user_ids for task in tasks
        })
        return tasks

    def write(self, vals):
        track = 'user_ids' in vals
        old_users = (
            {task.id: task.user_ids for task in self}
            if track and not self.env.context.get('cems_skip_portal_notify')
            else {}
        )
        res = super().write(vals)
        if (
            track
            and not self.env.context.get('mail_auto_subscribe_no_notify')
            and not self.env.context.get('cems_skip_portal_notify')
        ):
            self._cems_notify_task_assignees({
                task: task.user_ids - old_users.get(task.id, self.env['res.users'])
                for task in self
            })
        return res
