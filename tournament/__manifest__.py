# -*- coding: utf-8 -*-
{
    'name': "tournament",

    'summary': """
        Helper for organizing a sport tournament.""",

    'description': """
        This module allows to create a tournament for any kind of sport. Main features are:
         - manage entries within a tournament; an entry is 1 (or 2) players within 1 category
         - allows to create multiple tournaments
    """,

    'author': "pieral85@hotmail.com",
    'website': "https://www.bcsaintleger.be",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Club Membership',
    'version': '0.1',
    'depends': [
        'club',
    ],
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
