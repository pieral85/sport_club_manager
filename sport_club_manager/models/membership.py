# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class Membership(models.Model):
    _name = 'membership'
    _inherit = 'mail.thread'
    _description = 'Description'

    # @api.model
    @api.returns('self')
    def _default_price_due(self):
        # print('\n_default_price_due', self, self.period_category_id, self.period_category_id.price_due)
        return self.period_category_id.price_due

    period_category_id = fields.Many2one(
        comodel_name='period_category',
        # inverse_name='membership_ids',
        string='Period Category',
        required=True,
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        # inverse_name='membership_ids',
        string='Member',  # TODO Should it be a member (<> user)?
        required=True,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env['res.company']._company_default_get(),
    )
    price_paid = fields.Monetary(
        string='Price Paid',
        currency_field='currency_id',
    )
    price_due = fields.Monetary(
        string='Price Due',
        default=_default_price_due,
        store=True,
    )
    price_paid_percentage = fields.Float(
        string='Percentage Paid',
        compute='_compute_payment',  # '_compute_price_paid_percentage',
    )
    price_remaining = fields.Monetary(
        string='Price Remaining',
        currency_field='currency_id',
        compute='_compute_payment',
    )
    # member = fields.Boolean(
    #     string='Is a Member',
    # )
    # old_member = fields.Boolean(
        # string='Is an Old Member',
        # compute='_compute_old_member',
    # )
    status = fields.Selection(
        [
         ('not_member', 'Not a Member'),
         ('requested', 'Requested'),
         ('member', 'Member'),
         ('old_member', 'Old Member'),
        ],
        required=True,
        default='not_member'
    )
    paid = fields.Boolean(
        string='Paid',
        compute='_compute_payment',
    )
    color = fields.Integer(string='Color Index')
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        related='user_id.partner_id',
        store=False,
        readonly=True,
    )
    category_id = fields.Many2one(
        comodel_name='category',
        related='period_category_id.category_id',
        store=False,
        # readonly=True,
    )
    period_id = fields.Many2one(
        comodel_name='period',
        related='period_category_id.period_id',
        store=False,
        # readonly=True,
        default=lambda self: self.env['period'].search([('active','=',True),], limit=1)
    )
    # subscription_requested = fields.Boolean(
    #     string='Subscription Requested',
    # )
#    member_ids = fields.Many2many(
#        comodel_name='res.users',
#        # domain=[('is_company', '=', False)],
#        string='Members',
#    )

    # @api.multi
    # def write(self, vals):
    #     res = super(Membership, self).write(vals)
    #     self._add_follower(vals)
    #     return res

    @api.multi
    @api.depends('period_id', 'user_id')
    def name_get(self):
        res = []
        for record in self:
            name = '%s (%s)' % (record.period_id.name, record.user_id.name)
            res.append((record.id, name))
        return res

    @api.model
    def create(self, vals):
        res = super(Membership, self).create(vals)
        res._add_follower(vals)
        return res

    def _add_follower(self, vals):
        # if vals.get('responsible_id'):
            # responsible = self.env['res.users'].browse(vals.get('responsible_id'))
            # self.message_subscribe(partner_ids=responsible.partner_id.ids)
        ids = self.user_id.partner_id.ids
        ids.extend(self.env['res.users'].search([('secretary', '=', True),]).mapped('partner_id').ids)
        self.message_subscribe(partner_ids=ids)

    @api.depends('price_paid', 'price_due')
    def _compute_payment(self):
        # TOTEST When price_paid or price_due has changed, we should go in this function only once 
        for record in self:
            if record.price_due <= record.price_paid or record.price_due == 0:
                record.price_paid_percentage = 100
                record.price_remaining = 0
                record.paid = True
            else:
                record.price_paid_percentage = 100.0 * record.price_paid / record.price_due
                record.price_remaining = record.price_due - record.price_paid
                record.paid = False
            record._compute_status()

    # #After status has been changed
    # @api.onchange('status')
    # def _onchange_status(self):
    #     if record.status == 'member':
    #         if record.price_paid < record.price_due:
    #             record.price_paid = record.price_due  # Cette ligne devrait se retrouver dans la kanban view qand on drag and drop le user sur colonne Member


    # TODO define an api.depends (ne doit etre calcule que quand il y a une nouvelle periode (via le CRON?))
    def _compute_status(self):
    # def _compute_old_member(self):
        # import ipdb; ipdb.set_trace()
        for record in self:
            if record.status not in ('member', 'requested'):
                previous_period = record.period_category_id.period_id.previous_period
                temp = self.env['membership'].search(
                    [
                     ('period_category_id.period_id', '=', previous_period.id),
                     ('user_id', '=', record.user_id.id),
                     #('user_id.active', '=', True),  # TODO Ceux qui ont été désactivés l'année précédente ne devraient plus apparaître (cette ligne est peut etre superflue alors (TOTEST))
                    ]
                )
                # TODO Remove temp and return directly the result (but check first if it is ok if None is returned)
                toto = self.env['membership'].search_count(
                    [
                     ('period_category_id.period_id', '=', previous_period.id),
                     ('user_id', '=', record.user_id.id),
                     #('user_id.active', '=', True),  # TODO Ceux qui ont été désactivés l'année précédente ne devraient plus apparaître (cette ligne est peut etre superflue alors (TOTEST))
                    ]
                )
                if toto:
                    record.status = 'old_member'
                else:
                    record.status = 'not_member'

    # @api.multi
    @api.onchange('period_category_id')
    def _calculate_price_due(self):
        print('\n_calculate_price_due', self, self.period_category_id, self.period_category_id.price_due)
        import ipdb; ipdb.set_trace()
        for record in self:
            if record.period_category_id:
                record.price_due = record.period_category_id.price_due

    @api.onchange('category_id')
    def _onchange_category_id(self):
        # print('\n_onchange_category_id', self, self.category_id)
        for record in self:
            # import ipdb; ipdb.set_trace()
            # record.period_category_id = None
            if record.category_id and record.period_id:
                # period_category_ids = self.env['period_category'].search_read([('category_id.id','=',record.category_id.id),], ['period_id'])
                # import pprint; pprint.pprint(period_category_ids)
                # period_ids = [d['id'] for d in period_category_ids]
                # print(record.period_id, period_ids)
                # if record.period_id.id not in period_ids:
                #     record.period_id = None
                period_category_id = self.env['period_category'].search([('period_id.id','=',record.period_id.id),('category_id.id','=',record.category_id.id),])
                if not period_category_id:
                    record.period_id = None
                else:
                    record.period_category_id = period_category_id

    # TODO To be tested when changing a period_id
    @api.onchange('period_id')
    def _onchange_period_id(self):
        # print('\n_onchange_period_id', self, self.period_id)
        for record in self:
            # period_category_ids = self.env['period_category'].search_read([('period_id.id','=',record.period_id.id),], ['category_id'])
            # import ipdb; ipdb.set_trace()
            # record.period_category_id = None
            if record.period_id and record.category_id:
                # period_category_ids = self.env['period_category'].search([('period_id.id','=',record.period_id.id),]).ids
                # period_category_ids = self.env['period_category'].search_read([('period_id.id','=',record.period_id.id),], ['category_id'])
                
                # p_c_ids = [d['id'] for d in period_category_ids]
                # category_ids = [d.get('category_id',['---'])[0] for d in period_category_ids]
                # import pprint; pprint.pprint(period_category_ids)
                # print(record.category_id, category_ids)
                # if record.category_id.id not in period_category_ids:
                # if record.category_id.id not in category_ids:
                #     record.category_id = None
                # else:
                #     record.period_category_id = self.env['period_category'].search([('period_id.id','=',record.period_id.id),('category_id.id','=',record.category_id.id),], limit=1)
                period_category_id = self.env['period_category'].search([('period_id.id','=',record.period_id.id),('category_id.id','=',record.category_id.id),])
                if not period_category_id:
                    record.category_id = None
                else:
                    record.period_category_id = period_category_id