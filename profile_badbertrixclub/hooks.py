# -*- coding: utf-8 -*-

import base64

from odoo import api, tools, SUPERUSER_ID
from odoo.modules.module import get_resource_path

def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    def get_binary(file_name, module='profile_badbertrixclub', path='static/img'):
        file_path = get_resource_path(module, path, file_name)
        with tools.file_open(file_path, 'rb') as f:
            return base64.b64encode(f.read())

    # modify some fields for default website
    env.ref('website.default_website').write({
        'name': 'Bad Bertrix Club',
        'logo': get_binary('bbc92_logo_notext_white_small.jpg'),
    })

    # modify some fields for default contact company
    # TODO Fill other useful fields for this record (+ <res.config.settings>.favicon)
    env.ref('base.main_partner').write({
        'name': 'Bad Bertrix Club',
        'email': 'badbertrixclub92@gmail.com',
        'image_1920': get_binary('bbc92_logo.jpg'),
    })
    env.ref('base.main_company').write({
        'account_sale_tax_id': False,
    })