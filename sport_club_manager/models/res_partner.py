# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.partner'

    company_type = fields.Selection(string='Company Type',
        selection=[('person', 'Contact'), ('company', 'Location')],
        compute='_compute_company_type', inverse='_write_company_type')
