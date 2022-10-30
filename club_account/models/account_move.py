# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    membership_ids = fields.Many2many('membership', string='Memberships', compute='_compute_memberships')
    membership_count = fields.Integer('Count Memberships', compute='_compute_memberships')

    def _compute_memberships(self):
        for record in self:
            record.membership_ids = record.invoice_line_ids.membership_ids.ids
            record.membership_count = len(record.membership_ids)

    def action_view_memberships(self):
        self.ensure_one()
        memberships = self.membership_ids
        action = memberships._get_dynamic_action()
        action.update({
            'name': _('Memberships'),
        })
        return action
