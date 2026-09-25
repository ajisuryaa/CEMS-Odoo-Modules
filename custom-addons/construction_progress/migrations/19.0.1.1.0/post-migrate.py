# -*- coding: utf-8 -*-
"""Copy Site Engineers into Site Team after ORM created the M2M table."""


def migrate(cr, version):
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
        SELECT 1
          FROM information_schema.tables
         WHERE table_name = 'project_cems_engineer_rel'
        """
    )
    if not cr.fetchone():
        return
    cr.execute(
        """
        INSERT INTO project_cems_member_rel (project_id, user_id)
        SELECT project_id, user_id
          FROM project_cems_engineer_rel
         WHERE NOT EXISTS (
            SELECT 1 FROM project_cems_member_rel m
             WHERE m.project_id = project_cems_engineer_rel.project_id
               AND m.user_id = project_cems_engineer_rel.user_id
         )
        """
    )
