# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


# TODO Should create a list of Category in badminton module (Recreant, Competiteur, ...)


class Category(models.Model):
    _name = 'category'
    _description = ''  # TODO

    name = fields.Char(
        string='Category',
        required=True,
    )
    period_category_ids = fields.One2many(
        comodel_name='period_category',
        inverse_name='category_id',
        string='Period Categories',
    )


class PeriodCategory(models.Model):
    _name = 'period_category'
    _description = ''  # TODO
    # TODO D'une année à l'autre, un (smart?) bouton devrait permettre de dupliquer toutes les PeriodCategory (et tout ce qui est utile)

    period_id = fields.Many2one(
        comodel_name='period',
        string='Period',
    )
    category_id = fields.Many2one(
        comodel_name='category',
        string='Category',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env['res.company']._company_default_get(),
    )
    price_due = fields.Monetary(
        string='Due Price',
        currency_field='currency_id',
    )
    membership_ids = fields.One2many(
        comodel_name='membership',
        inverse_name='period_category_id',
        # domain=[('is_company', '=', False)],
        string='Memberships',
    )

    @api.multi
    @api.depends('period_id','category_id')
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id , '%s (%s)' % (record.period_id.name, record.category_id.name)))
        return result
