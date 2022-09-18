# -*- coding: utf-8 -*-
{
    'name': "Badminton Bertrix Club 92 Profile",
    'summary': "Contains all relevant data exclusive to Badminton Club of Bertrix.",
    'description': """
This module mostly contains data related to a specific club.
Therefore, it could not fit for any other club, even more if it is not related to badminton.
By installing this module, all required modules will be installed as well, so that the application will be fully installed.
Following features are included in this module:
- website pages
- misc static data
    """,
    'author': "pieral85@hotmail.com",
    'category': 'Club Sport Badminton',
    'version': '0.1',
    'depends': [
        # Custom dependencies:
        'club_account',
        'interclubs',
        # Standard dependencies:
        'contacts',
        'l10n_be',  # Belgium accounting (depends on `account`)
        'website_event',
    ],
    'data': [
        # menus
        'views/menus.xml',
        # data
        'data/mail_template_data.xml',
        'data/partner_data.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'application': False,
    'post_init_hook': 'post_init_hook',
    'license': 'LGPL-3',
}
