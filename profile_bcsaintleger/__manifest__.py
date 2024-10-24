# -*- coding: utf-8 -*-
{
    'name': "BC Saint-Léger Profile",
    'summary': "Contains all relevant data exclusive to Badminton Club of Saint-Léger.",
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
    'version': '0.2',
    'depends': [
        # Custom dependencies:
        # 'badminton_be',
        'club_account',
        'interclubs',
        # Standard dependencies:
        'contacts',
        'l10n_be',  # Belgium accounting (depends on `account`)
        'mass_mailing',
        'theme_treehouse',
        'website_event',
    ],
    'data': [
        # security
        'security/ir.model.access.csv',
        'security/security.xml',
        # views - website templates
        'views/templates/website_footer.xml',
        'views/templates/website_homepage.xml',
        'views/templates/website_membership_information.xml',
        'views/templates/website_practical_information.xml',
        # menus / views
        'views/event_registration_views.xml',
        'views/registration_tag_views.xml',
        'views/menus.xml',
        # data
        'data/mail_template_data.xml',
        'data/partner_data.xml',
        'data/website_data.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'application': False,
    'post_init_hook': 'post_init_hook',
    'license': 'LGPL-3',
}
