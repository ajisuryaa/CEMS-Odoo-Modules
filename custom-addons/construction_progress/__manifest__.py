{
    'name': 'CEMS Construction Progress',
    'version': '19.0.1.4.2',
    'category': 'Construction',
    'summary': 'WBS, geofence, EVM foundation for CEMS',
    'description': """
CEMS Phase 1 — Construction Progress
====================================
Foundation module for PT Dynatech Batam Construction & Engineering
Management Suite (CEMS):

* CEMS security groups (res.groups)
* Project geofence + Site Team assignment
* Leaflet / OpenStreetMap geofence map widget
* Task WBS, weightage, physical progress (assignees limited to Site Team)
* Project-level EVM (BAC, PV, EV, SPI, P_total)
* Record rules for multi-project isolation
    """,
    'author': 'Batemtech / PT Dynatech Batam',
    'website': 'https://www.batemtech.com',
    'license': 'LGPL-3',
    'depends': [
        'project',
        'hr_timesheet',
        'web',
    ],
    'data': [
        'security/cems_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rules.xml',
        'data/res_currency_idr.xml',
        'views/project_views_inherit.xml',
        'views/project_task_views_inherit.xml',
        'views/menu_items.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # Leaflet CSS in bundle; JS loaded at runtime via loadJS() for window.L.
            'construction_progress/static/lib/leaflet/leaflet.css',
            'construction_progress/static/src/components/geofence_map/geofence_map.css',
            'construction_progress/static/src/components/geofence_map/geofence_map.js',
            'construction_progress/static/src/components/geofence_map/geofence_map.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',
}
