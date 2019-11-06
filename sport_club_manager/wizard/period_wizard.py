# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# from datetime import date

from odoo import models, fields, api, exceptions


class PeriodWizard(models.TransientModel):
    _name = 'period_wizard'
    _description = 'Period Wizard'

    period_id = fields.Many2one(
        comodel_name='period',
        string="Period",
        required=True
    )
    name = fields.Char(
        string='Name',
        required=True,
    )
    start_date = fields.Date(
        string='Start Date',
        default=fields.Date.today(),
        required=True,
    )
    end_date = fields.Date(
        string='End Date',
        default=None,
        required=True,
    )

    @api.multi
    def duplicate(self):
        self.ensure_one()
        vals = {
            'name': self.name,
            'start_date': self.start_date,
            'end_date': self.end_date,
        }
        new_period_id = self.period_id.copy(vals)
        return {
            "type": "ir.actions.act_window",
            "res_model": "period",
            "views": [[False, "form"]],
            "res_id": new_period_id.id,
        }
