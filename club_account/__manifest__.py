# -*- coding: utf-8 -*-
{
# TODO Review this file
    'name': "Accounting for Club",
    'summary': "Add invoicing mechanism for the club management.",
    'description': """
This module adds the accounting for the management of members.

Following features are included in this module:
- invoicing: an invoice is created every time a membership is also created and lives alongside
    """,
    'author': "pieral85@hotmail.com",
    'website': "https://www.bcsaintleger.be",
    'category': 'Club Membership Accounting/Accounting',
    'version': '0.2',
    'depends': [
        'account',
        'club',
    ],
    'data': [
        # security
        'security/ir.model.access.csv',
        'security/security.xml',
        # views
        'views/account_move_views.xml',
        'views/category_views.xml',
        'views/membership_views.xml',
        'views/period_category_views.xml',
        'views/period_views.xml',
        'views/product_views.xml',
        'views/product_attribute_value_views.xml',
        # actions
        'actions/account_move_actions.xml',
        # data
        'data/club_account_data.xml',
    ],
    'qweb': [
    ],
    'demo': [
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'license': 'LGPL-3',
}
