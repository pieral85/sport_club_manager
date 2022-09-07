# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    company_type = fields.Selection(string='Company Type',
        selection=[('person', 'Individual'), ('company', 'Club')])
    club_id = fields.Many2one('res.partner', string='Club', domain=[('is_company', '=', True)], tracking=True)
    player_ids = fields.One2many('res.partner', 'club_id', string='Players')
    responsible_id = fields.Many2one('res.partner', string='Responsible',
        domain=[('is_company', '=', False)], tracking=True,
        help='Contact responsible of current contact. Usually, all communication will happen with the responsible. \
        This is usually useful for a minor child.')
    dependent_ids = fields.One2many('res.partner', 'responsible_id', string='Dependents')
    membership_ids = fields.One2many('membership', 'member_id', string='Memberships')
