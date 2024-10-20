{
    'name': "Mutual",
    'summary': "From a mutual document, this modules allows a member and a committee member to sign it.",
    'description': """
TODO
    """,
    'author': "pieral85@hotmail.com",
    'website': "https://www.bcsaintleger.be",
    'category': 'Sport',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': [
        'club_account',
        'sign',
    ],
    # always loaded
    'data': [
        'views/membership_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
