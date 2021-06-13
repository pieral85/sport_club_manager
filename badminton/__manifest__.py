# -*- coding: utf-8 -*-
{
    'name': "badminton_club_manager",

    'summary': """
        Manage players for ...""",  # TODO

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
    'depends': ['club'],#, 'board', 'website', 'website_sale'],

    # always loaded
    'data': [
    ],
    'qweb': [
        # 'static/src/xml/*.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo.xml',
    ],
    'installable': True,
    'application': False,
    # 'auto_install': False,
    # 'post_init_hook': '_auto_install_l10n',
}
