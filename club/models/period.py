# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import date

from odoo import models, fields, api, exceptions, _


class Period(models.Model):
    _name = 'period'
    _inherit = ['mail.thread', 'mail.alias.mixin']
    _description = 'Period'
    _order = 'start_date asc'
    _sql_constraints = [
       ('dates_check', 'CHECK(start_date < end_date)',
        'The end date should be higher than the start date. Please change it accordingly.'),
       ('name_uniq', 'unique(name)', 'The name of the period must be unique!'),
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
        default=None,
        required=True,
    )
    active = fields.Boolean(
        string='Active Period(s)',
        default=True,
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
        store=False,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
        store=False,
    )
    period_category_ids = fields.One2many(
        comodel_name='period.category',
        inverse_name='period_id',
        string='Period Categories',
    )
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

    def toggle_active(self):
        for template in self:
            template.active = not template.active

    # TODO This is a test function ==> delete me if not needed
    # @api.model_cr
    # def _register_hook(self):
    #     import ipdb; ipdb.set_trace()
    #     if not self.env['ir.config_parameter'].sudo().get_param('use.gmail.as.mail.server'):
    #         self.env['ir.config_parameter'].sudo().set_param('use.gmail.as.mail.server', ...):
    #     if not self.env['ir.config_parameter'].sudo().get_param('mail.local.part'):
    #         self.env['ir.config_parameter'].sudo().set_param('mail.local.part', ...):
    #     return super(Period, self)._register_hook()

    def get_alias_model_name(self, vals):
        """ Specify the model that will get created when the alias receives a message.

        :param dict vals: values of the newly created record that will holding the alias.
        :return: the model name for the alias.
        """
        return 'membership'

    def get_alias_values(self):
        """

        :return: values to create an alias, or to write on the alias after its creation.
        """
        values = super(Period, self).get_alias_values()
        values['alias_defaults'] = {'period_id': self.id}
        return values

    def update_periods(self):
        """ Updates 'active', 'current' and 'incoming' attributes of self, based on their 'start_date' and 'end_date' attributes.

        :return: None
        """
        if self.env.context.get('stop_propagation'):
            return None
        Period = self.env['period'].with_context(active_test=False)
        today = fields.Date.today()
        current_period_id = Period.search([('start_date', '<=', today), ('end_date', '>=', today)],
            order='start_date asc', limit=1).id
        upcoming_period_ids = Period.search([('start_date', '>', today)], order='start_date asc').ids
        upcoming_period_id = upcoming_period_ids[0] if upcoming_period_ids else []

        for period in Period.search([]):
            period.write({
                'active': period.id == current_period_id or period.id in upcoming_period_ids,
                'current': period.id == current_period_id,
                'upcoming': period.id == upcoming_period_id,
            })

    def prepare_duplication_wizard(self, default=None):
        ctx = self._context.copy()
        ctx['default_period_id'] = self.id
        most_recent_period = self.env['period'].search(['|', ('active', '=', False), ('active', '=', True),], order='start_date desc', limit=1)
        start_date = Period._add_years(most_recent_period.start_date, 1)
        end_date = Period._add_years(most_recent_period.end_date, 1)
        ctx['default_start_date'] = start_date
        ctx['default_end_date'] = end_date
        ctx['default_name'] = 'Season %s' % start_date.year
        if start_date.year != end_date.year:
            ctx['default_name'] += ' - %s' % end_date.year
        return {
            'name': 'Duplicate a period',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'src_model': 'period',
            'res_model': 'period.wizard',
            'view_id': self.env.ref('club.period_wizard_form_view').id,
            'context': ctx,
            'target': 'new',
        }

    def copy(self, default=None):
        """ Does a 'smart' duplication of self, including its period_category_ids and membership_ids.

        :param dict default: values for the newly created record.
        :return: New period created.
        """
        default = dict(default or {})
        default.setdefault('name', '%s (new)' % self.name)
        default.setdefault('start_date', Period._add_years(self.start_date, 1))
        default.setdefault('end_date', Period._add_years(self.end_date, 1))
        default.setdefault('active', True)
        new_period = super(Period, self).copy(default)

        for period_category_id in self.period_category_ids:
            default = {
                'period_id': new_period.id,
            }
            period_category_id.copy(default)
        self.update_periods()
        return new_period

    def send_email_invitations(self):
        # TODO:
        #  * Ouvrir un wizard qui propose la liste des memberships à qui on veut envoyer ça
        #  * Ouvre ensuite un template d'email
        #  * Créer le template d'email qui doit contenir deux boutons: un pour accepter et un pour refuser
        pass

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        # TODO It would be great if this search method would be invoked from the membership views
        for i, domain in enumerate(args):
            if domain[0] == 'name' and domain[2].isdigit():
                args.insert(i, '|')
                year = domain[2]
                min_date = '{}-01-01'.format(year)
                max_date = '{}-12-31'.format(year)
                args += ['&', ['start_date', '<=', max_date], ['end_date', '>=', min_date]]
                break
        return super(Period, self).search(args, offset, limit, order, count=count)

    @api.model
    def create(self, vals):
        vals.update(self._get_alias_name(vals))
        res = super(Period, self).create(vals)
        res.update_periods()
        return res

    def write(self, vals):
        vals.update(self._get_alias_name(vals))
        res = super(Period, self).write(vals)
        if 'start_date' in vals or 'end_date' in vals:
            self.update_periods()
        return res

    def _compute_membership_ids(self):
        for record in self:
            record.membership_ids = self.env['membership'].search([('period_category_id.period_id.id', '=', record.id or False),])
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

    def _get_alias_name(self, vals):
        if 'name' in vals and not 'alias_name' in vals:
            local_part = self.env['ir.config_parameter'].sudo().get_param('mail_local_part') or ''
            return {'alias_name': '{}+{}'.format(local_part, vals['name'])}
        return {}

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """ Checks that the start date is lower than the end date (otherwise, an exception is raised).

        :return: None
        """
        for period in self:
            if not period.start_date or not period.end_date or period.start_date > period.end_date:
                raise exceptions.ValidationError(_('The end date should be higher than the start date. Please change it accordingly.'))

    @api.constrains('name')
    def _check_name_unique(self):
        """ Checks that the name of the period is unique.

        :return: None
        """
        for period in self:
            if self.search_count([('name', '=', period.name)]) > 1:
                raise exceptions.ValidationError(_('The name of the period must be unique! Please change it accordingly.'))
