# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    company_type = fields.Selection(string='Company Type',
        selection=[('person', 'Individual'), ('company', 'Club')])
    responsible_id = fields.Many2one('res.partner', string='Responsible',
        help='Contact responsible of current contact. Usually, all communication will happen with the responsible. \
        This is usually useful for a minor child.')
    membership_ids = fields.One2many('membership', 'member_id', string='Memberships')
