{
    'name': 'CEMS Construction HRD',
    'version': '19.0.1.2.0',
    'category': 'Human Resources',
    'summary': 'Site workforce, geofence attendance portal, daily labor & gate pass',
    'description': """
CEMS Phase 2 — Construction HRD
===============================
Site workforce module for PT Dynatech Batam CEMS:

* Site assignment via project Site Team (construction_progress)
* Geofenced selfie attendance via Portal (Haversine vs project geofence)
* Daily Labor Report (DLR) — headcount by trade / hire type
* Gate Pass foundation model
    """,
    'author': 'Batemtech / PT Dynatech Batam',
    'website': 'https://www.batemtech.com',
    'license': 'LGPL-3',
    'depends': [
        'hr',
        'hr_attendance',
        'mail',
        'portal',
        'website',
        'construction_progress',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rules.xml',
        'data/sequences.xml',
        'views/hr_employee_views.xml',
        'views/hr_attendance_views.xml',
        'views/daily_labor_views.xml',
        'views/gate_pass_views.xml',
        'views/menu_items.xml',
        'views/portal_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'construction_hrd/static/src/js/geolocation.js',
            'construction_hrd/static/src/js/camera_selfie.js',
            'construction_hrd/static/src/css/portal_attendance.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
