# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class MemberWizard(models.TransientModel):
    _name = 'member.data.wizard'
    _description = 'Member Data Wizard'

    hide_data = fields.Boolean('Hide Data', default=True)
    membership_ids = fields.Many2many('membership', string='Memberships')

    def generate_report(self):
        self.ensure_one()
        data = {
            'hide_data': self.hide_data,
        }
        return self.env.ref('club.action_report_member_data').report_action(self.membership_ids, data={'form': data})
