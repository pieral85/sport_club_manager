# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class Club(models.Model):
    _inherit = 'res.company'
    # _name = 'club'
    _description = 'New description of the company (club)'  # TODO

    # currency_id = fields.Many2one(
    #     comodel_name='res.currency',
    #     string='Currency',
    #     required=True,
    #     default=''
    # )