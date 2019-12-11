# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, exceptions, _


class PeriodCategory(models.Model):
    _name = 'period.category'
    _description = 'Period Category'
    _order = 'period_id asc'

    period_id = fields.Many2one(
        comodel_name='period',
        ondelete='cascade',
        required=True,
        string='Period',
    )
    category_id = fields.Many2one(
        comodel_name='category',
        ondelete='cascade',
        required=True,
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
        help="Expected price to pay for the member.",
    )
    default = fields.Boolean(
        string='Default',
        default=False,
        help='When a request is done on a given period without knowing the category, the default category is set. Per period, only one default Category can be set.',
    )
    membership_ids = fields.One2many(
        comodel_name='membership',
        inverse_name='period_category_id',
        string='Memberships',
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

    @api.constrains('period_id', 'category_id', 'default')
    def _check_default_unique(self):
        """ Checks that each category within a single period must be unique (otherwise, an exception is raised).
        Also checks that each category has only one period_category with 'default' attribute set to True (otherwise, an exception is raised).

        :return: None
        """
        for pc in self:
            if len(pc.period_id.period_category_ids.filtered(lambda _pc: _pc.category_id.id == pc.category_id.id)) > 1:
                raise exceptions.ValidationError(_("For the period '%s', the category '%s' must be unique. Please change it accordingly.") % (pc.period_id.name, pc.category_id.name))
            if len(pc.period_id.period_category_ids.filtered(lambda _pc: _pc.default)) > 1:
                raise exceptions.ValidationError(_("For the period '%s', you cannot have multiple period categories with the attribute 'default' set to true. Please change it accordingly.") % (pc.period_id.name))

    @api.depends('period_id', 'category_id')
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id , '%s (%s)' % (record.period_id.name, record.category_id.name)))
        return result

    def copy(self, default=None):
        """ Does a 'smart' duplication of self, including its membership_ids.

        :param dict default: values for the newly created record.
        :return: New period.category created.
        """
        self.ensure_one()
        default = dict(default or {})
        default.setdefault('period_id', self.period_id.id)
        default.setdefault('category_id', self.category_id.id)
        default.setdefault('currency_id', self.currency_id.id)
        default.setdefault('price_due', self.price_due)
        new_period_category = super(PeriodCategory, self).copy(default)
        for membership_id in self.membership_ids:
            if membership_id.state == 'member':
                membership_state = 'old_member'
            elif membership_id.state == 'rejected':
                continue
            else:
                membership_state = 'unknown'
            membership_id.copy({
                'period_category_id': new_period_category.id,
                'period_id': default.get('period_id'),
                'state': membership_state,
            })
        return new_period_category
