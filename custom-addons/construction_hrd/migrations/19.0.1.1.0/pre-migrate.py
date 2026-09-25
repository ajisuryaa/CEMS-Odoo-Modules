# -*- coding: utf-8 -*-
"""Migrate legacy employee.cems_project_id into project Site Team members."""


def migrate(cr, version):
    if not version:
        return
    cr.execute(
        """
        SELECT 1
          FROM information_schema.columns
         WHERE table_name = 'hr_employee'
           AND column_name = 'cems_project_id'
        """
    )
    if not cr.fetchone():
        return
    # Ensure member relation table exists (created when construction_progress upgraded)
    cr.execute(
        """
        SELECT 1
          FROM information_schema.tables
         WHERE table_name = 'project_cems_member_rel'
        """
    )
    if not cr.fetchone():
        return
    cr.execute(
        """
        INSERT INTO project_cems_member_rel (project_id, user_id)
        SELECT e.cems_project_id, e.user_id
          FROM hr_employee e
         WHERE e.cems_project_id IS NOT NULL
           AND e.user_id IS NOT NULL
           AND NOT EXISTS (
                SELECT 1 FROM project_cems_member_rel m
                 WHERE m.project_id = e.cems_project_id
                   AND m.user_id = e.user_id
           )
        """
    )
