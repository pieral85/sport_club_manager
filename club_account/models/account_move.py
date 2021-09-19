# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
# from odoo.exceptions import ValidationError, UserError
# from odoo.tests.common import Form


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
        action = {
            'name': _('Memberships'),
            'res_model': 'membership',
            'type': 'ir.actions.act_window',
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
