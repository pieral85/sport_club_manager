# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api

class Period(models.Model):
    _name = 'period'
    _description = ''  # TODO
    _order = 'start_date desc, end_date desc'
    # TODO Ajouter une contrainte lors de la création d'unne période: aucune date commune ne peut interférer

    name = fields.Char(
        string='Period',
        required=True,
    )
    start_date = fields.Date(
        string='Start Date',
        default=fields.Date.today(),
        required=True,
    )
    end_date = fields.Date(
        string='End Date',
        default=None,  # TODO Should be start date + 1 year
        required=True,
    )
    active = fields.Boolean(
        string='Active',
        # compute='_compute_active',
        # store=True,
    )
    previous_period = fields.Many2one(
        comodel_name='period',
        string='Previous Period',
        compute='_compute_previous_period',
    )
    period_category_ids = fields.One2many(
        comodel_name='period_category',
        inverse_name='period_id',
        string='Period Categories',
    )
    user_ids = fields.Many2many(
        comodel_name='res.users',
        string='Members',
        compute='_compute_get_users',
    )

    # TODO This function should also be called when a record is deleted (and also maybe in other cases)
    def _update_periods(self):
        import ipdb
        if len(self) >1:
            ipdb.set_trace()
        active_period_id = self.env['period'].search(
            ['&', '&', 
             '|', ('active', '=', True), ('active', '=', False),
             ('start_date', '<=', fields.Date.today()),
             ('end_date', '>=', fields.Date.today()),
            ],
            order='start_date asc',
            limit=1,
        ).id

        for record in self.env['period'].search(['|', ('active','=',False), ('active', '=', True),]):
            if record.active != (active_period_id == record.id):
                record.active = active_period_id == record.id

    @api.multi
    def write(self, vals):
        print('\nWRITE\n', self, vals)
        res = super(Period, self).write(vals)
        if 'start_date' in vals or 'end_date' in vals:
            self._update_periods()
        return res

    @api.model
    def create(self, vals):
        # import ipdb; ipdb.set_trace()
        print('\nCREATE\n',self, vals)
        res = super(Period, self).create(vals)
        if 'start_date' in vals or 'end_date' in vals:
            res._update_periods()
        return res

    # @api.depends('period_category_ids')
    def _compute_get_users(self):
        for record in self:
            record.user_ids = self.env['res.users'].search([('membership_ids.period_category_id.period_id.id', '=', record.id),])

    def _compute_previous_period(self):
        for record in self:
            record.previous_period = self.env['period'].search(
                [('start_date', '<', record.start_date),],
                limit=1,
                order='start_date desc',
            )