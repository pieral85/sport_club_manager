# -*- coding: utf-8 -*-
{
    'name': "sport_club_manager",

    'summary': """
        Manage players for a sport club.""",

    'description': """
        Manage players for a sport club.
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
        'base',
        'website_form',
        'auth_signup',
        'mail',
    ],

    # always loaded
    'data': [
        # security
        'security/security.xml',
        'security/ir_rule.xml',
        'security/ir.model.access.csv',

        # views
        'views/period_views.xml',
        'views/category_views.xml',
        'views/res_users_views.xml',
        'views/res_partner_views.xml',
        'views/role_views.xml',
        'views/res_company_views.xml',
        'views/membership_views.xml',
        'views/website.xml',
        'views/mail_views.xml',
        'views/res_config_settings_views.xml',

        # actions
        'actions/membership_actions.xml',
        'actions/res_users_actions.xml',
        'actions/category_actions.xml',
        'actions/res_partner_actions.xml',
        'actions/period_actions.xml',

        # menus
        'views/menus.xml',

        # templates
        'controllers/templates.xml',

        # data
        'data/res_users_data.xml',
        'data/period_data.xml',
        'data/membership_data.xml',
    ],
    'qweb': [
    ],
    # only loaded in demonstration mode
    'demo': [
        'data/demo/period_demo.xml',
        'data/demo/category_demo.xml',
        'data/demo/player_demo.xml',
        'data/demo/role_demo.xml',
        'data/demo/period_category_demo.xml',
        'data/demo/membership_demo.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
}
