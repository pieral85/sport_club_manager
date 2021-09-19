# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class Category(models.Model):
    _name = 'category'
    _description = 'Category'
    _sql_constraints = [
       ('name_uniq', 'unique(name)', 'The name of the category must be unique!'),
    ]

    name = fields.Char(
        string='Category',
        required=True,
    )
    description = fields.Char(string='Description')
    period_category_ids = fields.One2many(
        comodel_name='period.category',
        inverse_name='category_id',
        string='Period Categories',
    )
    period_ids = fields.Many2many('period', string='Periods',
        compute='_compute_period_ids')
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
        store=False,
    )
    active = fields.Boolean('Active', default=True)
    member_ids = fields.Many2many('res.partner', string='Members',
        compute='_compute_membership_ids')
    membership_ids = fields.Many2many(
        comodel_name='membership',
        string='Memberships',
        compute='_compute_membership_ids',
    )
    count_members = fields.Integer(
        string='Active Members',
        compute='_compute_membership_ids',
    )
    total_price_paid = fields.Monetary(
        string='Total Members Price Paid',
        currency_field='currency_id',
        compute='_compute_prices',
    )
    total_price_due = fields.Monetary(
        string='Total Members Due Price',
        currency_field='currency_id',
        compute='_compute_prices',
    )
    total_remaining_price_due = fields.Monetary(
        string='Total Remaining Members Due Price',
        currency_field='currency_id',
        compute='_compute_prices',
    )

    @api.depends('period_category_ids', 'period_category_ids.period_id')
    def _compute_period_ids(self):
        for record in self:
            record.period_ids = record.period_category_ids.mapped('period_id')

    def _compute_membership_ids(self):
        for record in self:
            record.membership_ids = self.env['membership'].search([('period_category_id.category_id.id', '=', record.id or False),])
            record.count_members = len(record.membership_ids.filtered(lambda m: m.state == 'member'))
            record.member_ids = record.membership_ids.mapped('member_id')

    @api.depends('membership_ids')
    def _compute_prices(self):
        for record in self:
            paid, due, remaining = 0, 0, 0
            for membership_id in record.membership_ids:
                if membership_id.state == 'member':
                    paid += membership_id.price_paid
                    due += membership_id.price_due
                    remaining += membership_id.price_remaining
            record.total_price_paid = paid
            record.total_price_due = due
            record.total_remaining_price_due = remaining

    @api.constrains('name')
    def _check_name_unique(self):
        """ Checks that the name of the category is unique.

        :return: None
        """
        for category in self:
            if self.search_count([('name', '=', category.name)]) > 1:
                raise ValidationError(_('The name of the category must be unique! Please change it accordingly.'))
