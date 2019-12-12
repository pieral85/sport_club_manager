# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, exceptions


class Category(models.Model):
    _name = 'category'
    _description = 'Category'

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
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env['res.company']._company_default_get(),
        store=False,
    )
    member_ids = fields.Many2many('res.partner', string='Members',
        compute='_compute_get_members')
    membership_ids = fields.Many2many(
        comodel_name='membership',
        string='Memberships',
        compute='_compute_get_memberships',
    )
    count_members = fields.Integer(
        string='Active Members',
        compute='_count_members',
    )
    total_price_paid = fields.Monetary(
        string='Total Members Price Paid',
        currency_field='currency_id',
        compute='_total_price_paid',
    )
    total_price_due = fields.Monetary(
        string='Total Members Due Price',
        currency_field='currency_id',
        compute='_total_price_due',
    )
    total_remaining_price_due = fields.Monetary(
        string='Total Remaining Members Due Price',
        currency_field='currency_id',
        compute='_total_remaining_price_due',
    )

    def _compute_get_members(self):
        for record in self:
            record.member_ids = self.env['res.partner'].search([('membership_ids.period_category_id.category_id.id', '=', record.id),])

    def _compute_get_memberships(self):
        for record in self:
            record.membership_ids = self.env['membership'].search([('period_category_id.category_id.id', '=', record.id),])

    @api.depends('membership_ids')
    def _count_members(self):
        for record in self:
            record.count_members = len(record.membership_ids.filtered(lambda m: m.state == 'member'))

    @api.depends('membership_ids')
    def _total_price_paid(self):
        for record in self:
            total_price_paid = 0
            for membership_id in record.membership_ids:
                if membership_id.state == 'member':
                    total_price_paid += membership_id.price_paid
            record.total_price_paid = total_price_paid

    @api.depends('membership_ids')
    def _total_price_due(self):
        for record in self:
            total_price_due = 0
            for membership_id in record.membership_ids:
                if membership_id.state == 'member':
                    total_price_due += membership_id.price_due
            record.total_price_due = total_price_due

    @api.depends('membership_ids')
    def _total_remaining_price_due(self):
        for record in self:
            total_remaining_price_due = 0
            for membership_id in record.membership_ids:
                if membership_id.state == 'member':
                    total_remaining_price_due += membership_id.price_remaining
            record.total_remaining_price_due = total_remaining_price_due