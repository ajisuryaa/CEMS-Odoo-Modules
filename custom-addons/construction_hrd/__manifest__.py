{
    'name': 'CEMS Construction HRD',
    'version': '19.0.1.8.1',
    'category': 'Human Resources',
    'summary': 'Site workforce, geofence attendance portal, daily labor & gate pass',
    'description': """
CEMS Phase 2 — Construction HRD
===============================
Site workforce module for PT Dynatech Batam CEMS:

* Website homepage (/) CEMS split login (Odoo DB auth)
* Stock /web/login redirects to CEMS homepage (/)
* Portal Hub (/my) self-sufficient shell (menu via ir.http / layout C)
* Projects / Tasks / Profile (+ project & task detail) wrapped in CEMS shell
* Site assignment via project Site Team (construction_progress)
* Geofenced selfie attendance via Portal (Haversine vs project geofence)
* Daily Labor Report (DLR) — headcount by trade / hire type
* Gate Pass foundation
    """,
    'author': 'Batemtech / PT Dynatech Batam',
    'website': 'https://www.batemtech.com',
    'license': 'LGPL-3',
    'depends': [
        'hr',
        'hr_attendance',
        'mail',
        'portal',
        'project',
        'website',
        'auth_signup',
        'construction_progress',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rules.xml',
        'data/sequences.xml',
        'data/website_menu_home.xml',
        'views/hr_employee_views.xml',
        'views/hr_attendance_views.xml',
        'views/daily_labor_views.xml',
        'views/gate_pass_views.xml',
        'views/menu_items.xml',
        'views/portal_hub_templates.xml',
        'views/portal_templates.xml',
        'views/portal_shell_wrap.xml',
        'views/website_login_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'construction_hrd/static/src/js/geolocation.js',
            'construction_hrd/static/src/js/camera_selfie.js',
            'construction_hrd/static/src/js/hub_clock.js',
            'construction_hrd/static/src/js/attendance_dialog.js',
            'construction_hrd/static/src/css/portal_attendance.css',
            'construction_hrd/static/src/css/cems_login_home.css',
            'construction_hrd/static/src/css/cems_portal_hub.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
