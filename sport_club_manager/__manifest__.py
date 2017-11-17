# -*- coding: utf-8 -*-
{
    'name': "sport_club_manager",

    'summary': """
        Manage players for """,  # TODO

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
    'depends': ['base', 'website', 'auth_signup'],#, 'board', 'website_sale'],

    # always loaded
    'data': [
        # views
        'views/period_views.xml',
        'views/category_views.xml',
        'views/res_users_views.xml',
        'views/res_partner_views.xml',
        'views/membership_views.xml',
        'views/menus.xml',

        # actions
        'actions/membership_actions.xml',

        # templates
        'controllers/templates.xml',

        # security
        'security/security.xml',
        'security/ir.model.access.csv',

        # data
        'data/period_data.xml',
        'data/membership_data.xml',
    ],
    'qweb': [
        # 'static/src/xml/*.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'data/period_demo.xml',
        'data/category_demo.xml',
        'data/res_users_demo.xml',
        'data/membership_demo.xml',
    ],
    'installable': True,
    'application': True,
    # 'auto_install': False,
    # 'post_init_hook': '_auto_install_l10n',
}
