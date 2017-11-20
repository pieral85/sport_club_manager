# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import date

from odoo import models, fields, api, exceptions

class Period(models.Model):
    _name = 'period'
    _description = ''  # TODO
    _order = 'start_date desc, end_date desc'
    # TODO Ajouter une contrainte lors de la création d'unne période: aucune date commune ne peut interférer

    _sql_constraints = [
       ('dates_check', 'CHECK(start_date < end_date)',
        'The End Date should be higher than the Start Date. Please change it accordingly.'),
    ]

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
        string='Active Period(s)',
        default=True,
        # compute='_compute_active',
        # store=True,
    )
    current = fields.Boolean(
        string='Current Period',
    )
    upcoming = fields.Boolean(
        string='Upcoming Period',
    )
    previous_period = fields.Many2one(
        comodel_name='period',
        string='Previous Period',
        compute='_compute_previous_period',
    )
    # category_ids = fields.Many2many(
    #     comodel_name='category',
    #     relation='period_category',
    #     column1='period',
    #     column2='category',
    #     string='Categories',
    # )
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

    @api.multi
    def toggle_active(self):
        for template in self:
            template.active = not template.active

    # TODO This function should also be called when a record is deleted (and also maybe in other cases)
    # TODO when creating/modifying a period, start date should always be < end date
    def _update_periods(self):
        import ipdb
        if len(self) >1:
            ipdb.set_trace()
        current_period_id = self.env['period'].search(
            ['&', '&', 
             '|', ('active', '=', True), ('active', '=', False),
             ('start_date', '<=', fields.Date.today()),
             ('end_date', '>=', fields.Date.today()),
            ],
            order='start_date asc',
            limit=1,
        ).id
        upcoming_period_id = self.env['period'].search(
            ['&',
             '|', ('active', '=', True), ('active', '=', False),
             ('start_date', '>', fields.Date.today()),
            ],
            order='start_date asc',
            limit=1,
        ).id

        for record in self.env['period'].search(['|', ('active','=',False), ('active', '=', True),]):
            # if record.active != (record.active in (current_period_id, upcoming_period_id)):
            record.active = record.id in (current_period_id, upcoming_period_id)
            # if record.current != (current_period_id == record.id):
            record.current = record.id == current_period_id
            record.upcoming = record.id == upcoming_period_id

    @api.multi
    def write(self, vals):
        # import ipdb; ipdb.set_trace()
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

    # # Code found in sale.py: is it better in proceed with this method?
    # @api.multi
    # def copy_data(self, default=None):
    #     if default is None:
    #         default = {}
    #     if 'order_line' not in default:
    #         default['order_line'] = [(0, 0, line.copy_data()[0]) for line in self.order_line.filtered(lambda l: not l.is_downpayment)]
    #     return super(SaleOrder, self).copy_data(default)  
    def copy(self, default=None):
        default = dict(default or {})
        default.setdefault('name', '%s (new)' % self.name)
        default.setdefault('start_date', Period._add_years(self.start_date, 1))
        default.setdefault('end_date', Period._add_years(self.end_date, 1))
        default.setdefault('active', True)
        # import ipdb; ipdb.set_trace()
        new_period = super(Period, self).copy(default)
        print('=== Period ===', new_period, new_period.name)
        for period_category_id in self.period_category_ids:
            # import ipdb; ipdb.set_trace()
            default = {
                'period_id': new_period.id,
            }
            period_category_id.copy(default)
        # return {
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'period',
        #     'view_mode': 'form',  # Should always be 'form'
        #     'view_type': 'form',  # Can be'tree', 'tree,form,kanban', 'tree,form', ...
        #     'res_id': new_period.id,
        #     #'target': 'new',  # Opens in a pop-up window
        # }
        return new_period


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

    @staticmethod
    def _add_years(dte, years):
        """Return a date that's `years` years after the date (or datetime)
        object `dte` (of type fields.Date). Return the same calendar date (month and day) in the
        destination year, if it exists, otherwise use the following day
        (thus changing February 29 to March 1).
        
        Code found on https://stackoverflow.com/questions/15741618/add-one-year-in-current-date-python
        """
        d = fields.Date.from_string(dte)
        try:
            return d.replace(year = d.year + years)
        except ValueError:
            return d + (date(d.year + years, 1, 1) - date(d.year, 1, 1))

    # def _warning(self, title, message):
    #     return {'warning': {
    #         'title': title,
    #         'message': message,
    #         },
    #     }

    # @api.onchange('start_date', 'end_date')
    # def _check_dates(self):
    #     print(self.start_date, type(self.start_date), self.end_date)
    #     if self.start_date and self.end_date and self.start_date > self.end_date:
    #         return self._warning('Incorrect date', 'The End Date should be higher than the Start Date. Please change it accordingly.')

    @api.one
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        count_common_periods = self.env['period'].search_count([
            '&', '&',
            '|', ('active', '=', True), ('active', '=', False),
            ('start_date', '<=', self.end_date),
            ('end_date', '>=', self.start_date),
            ]) - 1
        if count_common_periods:
            raise exceptions.ValidationError("The period from %s to %s has at least one day in common with %d other period(s) already defined. Please change it accordingly." % (self.start_date, self.end_date, count_common_periods))
        if not self.start_date or not self.end_date or self.start_date > self.end_date:
            raise exceptions.ValidationError('The End Date should be higher than the Start Date. Please change it accordingly.') 

