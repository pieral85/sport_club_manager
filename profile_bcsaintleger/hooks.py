# -*- coding: utf-8 -*-

import base64

from odoo import api, tools, SUPERUSER_ID
from odoo.modules.module import get_resource_path

def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    def get_binary(file_name, module='profile_bcsaintleger', path='static/img'):
        file_path = get_resource_path(module, path, file_name)
        with tools.file_open(file_path, 'rb') as f:
            return base64.b64encode(f.read())

    # modify some fields for default website
    env.ref('website.default_website').write({
        'name': 'BC Saint-Léger',
        'logo': get_binary('bc_saint_leger_logo_notext_white_small.png'),
    })

    # modify some fields for default contact company
    # TODO Fill other useful fields for this record (+ <res.config.settings>.favicon)
    env.ref('base.main_partner').write({
        'name': 'BC Saint-Léger',
        'email': 'badsl@live.be',
        'image_1920': get_binary('bc_saint_leger_logo.png'),
    })
    env.ref('base.main_company').write({
        'account_sale_tax_id': False,
    })