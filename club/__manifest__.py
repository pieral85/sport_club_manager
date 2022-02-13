# -*- coding: utf-8 -*-
{
# TODO Review this file
    'name': "Club Membership Manager",

    'summary': """
        Manage memberships for any kind of club.""",

    'description': """
        This module allows management of members.
Following features are included in this module:
 * periods: range of dates during which membership occurs
 * categories: allows to assign multiple categories
 * prices: allows to defines prices for members in each category and period
 * memberships: allows to manage members lifecycle, regarding the period, category and price defined
    """,
    'author': "pal@odoo.com",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Club Membership',
    'version': '0.2',
    'depends': [
        'base',
        'website',
        'auth_signup',
        'mail',
    ],
    'data': [
        # security
        'security/security.xml',
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        # views
        'views/period_views.xml',
        'views/category_views.xml',
        'views/period_category_views.xml',
        'views/res_users_views.xml',
        'views/role_views.xml',
        'views/res_company_views.xml',
        'views/membership_views.xml',
        'views/mail_views.xml',
        'views/res_config_settings_views.xml',
        # views - website templates
        'views/templates/membership_portal_templates.xml',
        'views/templates/membership_templates.xml',
        'views/templates/period_templates.xml',
        'views/templates/website_templates.xml',
        # wizards
        'wizards/period_wizard_views.xml',
        # actions
        'actions/membership_actions.xml',
        'actions/res_users_actions.xml',
        'actions/category_actions.xml',
        'actions/period_category_actions.xml',
        'actions/res_partner_actions.xml',
        'actions/period_actions.xml',
        # menus
        'views/menus.xml',
        # data
        'data/res_users_data.xml',
        'data/membership_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'club/static/src/less/membership.less',
        ],
    },
    'qweb': [
    ],
    'demo': [
        'data/demo/period_demo.xml',
        'data/demo/category_demo.xml',
        'data/demo/member_demo.xml',
        'data/demo/role_demo.xml',
        'data/demo/period_category_demo.xml',
        'data/demo/membership_demo.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
}
