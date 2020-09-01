# -*- coding: utf-8 -*-
{
    'name': "BC Saint-Léger Profile",

    'summary': """
        Contains all relevant data exclusive to Badminton Club of Saint-Léger.""",

    'description': """
        This module mostly contains data related to a specific club.
Therefore, it could not fit for any other club, even more if it is not related to badminton.
By installing this module, all required modules will be installed as well, so that the application will be fully installed.
Following features are included in this module:
 * website pages
 * misc static data
    """,
    'author': "pal@odoo.com",
    'category': 'Club Sport Badminton',
    'version': '0.1',
    'depends': [
        'interclubs',
        # 'badminton_be',  # Commented because this module is still under development
    ],
    'data': [
        # views - website templates
        'views/templates/website_templates.xml',
        # data
        'data/partner_data.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'application': False,
}
