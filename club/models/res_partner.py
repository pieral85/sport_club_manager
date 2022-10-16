# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    company_type = fields.Selection(string='Company Type',
        selection=[('person', 'Individual'), ('company', 'Club')])
    gender = fields.Selection(string='Gender', selection=[('male', 'Male'), ('female', 'Female')])
    birthdate = fields.Date('Birthdate')
    club_id = fields.Many2one('res.partner', string='Club', domain=[('is_company', '=', True)], tracking=True)
    player_ids = fields.One2many('res.partner', 'club_id', string='Players')
    responsible_id = fields.Many2one('res.partner', string='Responsible',
        domain=[('is_company', '=', False)], tracking=True,
        help='Contact responsible of current contact. Usually, all communication will happen with the responsible. \
        This is usually useful for a minor child.')
    dependent_ids = fields.One2many('res.partner', 'responsible_id', string='Dependents')
    membership_ids = fields.One2many('membership', 'member_id', string='Memberships')
    membership_count = fields.Integer('Count Memberships', compute='_compute_memberships')

    def _compute_memberships(self):
        for record in self:
            record.membership_count = len(record.membership_ids)

    def action_view_memberships(self):
        self.ensure_one()
        action = {
            'name': _('Memberships'),
            'res_model': 'membership',
            'type': 'ir.actions.act_window',
            'context': {'default_member_id': self.id},
        }
        membership_ids = self.membership_ids.ids
        if len(membership_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': membership_ids[0],
            })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', membership_ids)],
            })
        return action
