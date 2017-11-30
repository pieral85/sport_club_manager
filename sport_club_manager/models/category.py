# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, exceptions


# TODO Should create a list of Category in badminton module (Recreant, Competiteur, ...)


class Category(models.Model):
    _name = 'category'
    _description = ''  # TODO

    name = fields.Char(
        string='Category',
        required=True,
    )
    # period_ids = fields.Many2many(
    #     comodel_name='period',
    #     relation='period_category',
    #     column1='category',
    #     column2='period',
    #     string='Periods',
    # )
    period_category_ids = fields.One2many(
        comodel_name='period_category',
        inverse_name='category_id',
        string='Period Categories',
    )