# -*- coding: utf-8 -*-
{
    'name': "Interclubs",
    'summary': "TODO",
    'description': """
TODO
    """,
    'author': "Odoo",
    'website': "http://www.odoo.com",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Sport',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': [
        'calendar',
        'club',
        'project',  # Used for some scss styling (see https://github.com/odoo/odoo/blob/13.0/addons/project/static/src/scss/project_dashboard.scss#L18)
    ],
    # always loaded
    'data': [
        # security
        'security/security.xml',
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        # views
        'views/calendar_views.xml',
        'views/interclub_views.xml',
        'views/interclub_event_views.xml',
        'views/res_config_settings_views.xml',
        # wizards
        'wizards/interclub_event_mail_wizard_views.xml',
        # actions
        'actions/interclub_actions.xml',
        'actions/interclub_event_actions.xml',
        # menus
        'views/menus.xml',
        # # templates
        # 'controllers/templates.xml',
        # data
        'data/res_users_data.xml',
        'data/interclub_event_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'interclubs/static/src/js/interclub_event_calendar.js',  # TODO Check if taken into account
            'interclubs/static/src/js/interclub.js',  # TODO Check if taken into account
        ],
    },
    'qweb': [
    ],
    # only loaded in demonstration mode
    'demo': [
        'data/demo/addreses_demo.xml',
        'data/demo/interclub_demo.xml',
        'data/demo/interclub_event_demo.xml',
    ],
    # 'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
