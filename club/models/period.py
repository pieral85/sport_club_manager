# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import ast
import logging
from datetime import date

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Period(models.Model):
    _name = 'period'
    _inherit = ['mail.thread', 'mail.alias.mixin']
    _description = 'Period'
    _order = 'current DESC, upcoming DESC, start_date DESC'
    _sql_constraints = [
       ('dates_check', 'CHECK(start_date < end_date)',
        'The end date should be higher than the start date. Please change it accordingly.'),
       ('name_uniq', 'unique(name)', 'The name of the period must be unique!'),
    ]

    name = fields.Char('Period', required=True, translate=True)
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
    category_ids = fields.Many2many('category', string='Categories',
        compute='_compute_category_ids')
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
        string='Total Paid Price',
        currency_field='currency_id',
        compute='_compute_prices',
    )
    total_price_due = fields.Monetary(
        string='Total Due Price',
        currency_field='currency_id',
        compute='_compute_prices',
    )
    total_remaining_price_due = fields.Monetary(
        string='Total Remaining Due Price',
        currency_field='currency_id',
        compute='_compute_prices',
    )
    year = fields.Integer('Year', compute='_compute_year', search='_search_year',
        help="Year (for search only)")

    # TODO This is a test function ==> delete me if not needed
    # @api.model_cr
    # def _register_hook(self):
    #     import ipdb; ipdb.set_trace()
    #     if not self.env['ir.config_parameter'].sudo().get_param('use.gmail.as.mail.server'):
    #         self.env['ir.config_parameter'].sudo().set_param('use.gmail.as.mail.server', ...):
    #     if not self.env['ir.config_parameter'].sudo().get_param('mail.local.part'):
    #         self.env['ir.config_parameter'].sudo().set_param('mail.local.part', ...):
    #     return super(Period, self)._register_hook()

    def _alias_get_creation_values(self):
        values = super(Period, self)._alias_get_creation_values()
        values['alias_model_id'] = self.env['ir.model']._get('membership').id
        if self.id:
            values['alias_defaults'] = defaults = ast.literal_eval(self.alias_defaults or "{}")
            defaults['period_id'] = self.id
        return values

    @api.autovacuum
    def _update_periods(self):
        """ Updates 'active', 'current' and 'incoming' attributes of self, based on their 'start_date' and 'end_date' attributes.

        :return: None
        """
        if self.env.context.get('stop_propagation'):
            return None
        Period = self.env['period']
        today = fields.Date.today()
        current_period_id = Period.search([('start_date', '<=', today), ('end_date', '>=', today)],
            order='start_date asc', limit=1).id
        upcoming_period_ids = Period.search([('start_date', '>', today)], order='start_date asc').ids
        upcoming_period_id = upcoming_period_ids[0] if upcoming_period_ids else []
        _logger.info("Update periods: current is #%d; upcoming are #%s",
            current_period_id, ','.join(str(p_id) for p_id in upcoming_period_ids))

        for period in Period.search([]):
            period.write({
                'current': period.id == current_period_id,
                'upcoming': period.id == upcoming_period_id,
            })

    def _compute_year(self):
        raise NotImplementedError(_("Field 'Year' cannot be computed. Its only purpose is to be searched."))

    @api.model
    def _search_year(self, operator, operand):
        if operator in ('like', 'ilike'):
            min_date = '{}-01-01'.format(operand)
            max_date = '{}-12-31'.format(operand)
            return ['start_date', '<=', max_date], ['end_date', '>=', min_date]
        else:
            raise NotImplementedError(_("The operator '%s' is not supported when searching field 'Year'.") \
                % operator)

    def prepare_duplication_wizard(self, default=None):
        self.ensure_one()
        ctx = self._context.copy()
        ctx['default_period_id'] = self.id
        start_date = Period._add_years(self.start_date, 1)
        end_date = Period._add_years(self.end_date, 1)
        ctx['default_start_date'] = start_date
        ctx['default_end_date'] = end_date
        ctx['default_name'] = self._get_new_name(start_date, end_date)
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
        self._update_periods()
        return new_period

    def send_email_invitations(self):
        # TODO:
        #  * Ouvrir un wizard qui propose la liste des memberships à qui on veut envoyer ça
        #  * Ouvre ensuite un template d'email
        #  * Créer le template d'email qui doit contenir deux boutons: un pour accepter et un pour refuser
        pass

    def regenerate_alias_name(self):
        self.alias_name = self._get_alias_name()

    @api.model
    def create(self, vals):
        vals.update(self._get_alias_name_dict(vals, force_get=True))
        res = super(Period, self).create(vals)
        res._update_periods()
        return res

    def write(self, vals):
        vals.update(self._get_alias_name_dict(vals))
        res = super(Period, self).write(vals)
        if 'start_date' in vals or 'end_date' in vals:
            self._update_periods()
        return res

    @api.depends('period_category_ids', 'period_category_ids.category_id')
    def _compute_category_ids(self):
        for record in self:
            record.category_ids = record.period_category_ids.mapped('category_id')

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

    def _get_new_name(self, new_start_date, new_end_date):
        """ Basically replaces year occurences of the period name with the years coming from `new_start_date`
            and `new_end_date` dates.

        i.e. Let's pretend period name is "Super season 2023-24" and new_start_date and new_end_date are respectively
             datetime.date(2024, 9, 1) and datetime.date(2025, 6, 30).
             The string returned will be "Super season 2024-25".
             Note: To identify start/end date years ('2023' and '24'), the method assumes period `start_date`
                   and `end_date` are "consistant" (datetime.date(2023, x, x) and datetime.date(2024, x, x)).

        :return: new period name based on current one.
        :rtype: str
        """
        self.ensure_one()

        def replace_date_year(name, old_date, new_date):
            old_year_str, new_year_str = str(old_date.year), str(new_date.year)
            if old_year_str in name:
                return name.replace(old_year_str, new_year_str)
            if old_year_str[-2:] in name:
                return name.replace(old_year_str[-2:], new_year_str[-2:])
            return name
        new_name = replace_date_year(self.name, self.end_date, new_end_date)
        if self.start_date.year != self.end_date.year:
            new_name = replace_date_year(new_name, self.start_date, new_start_date)
        return new_name

    @staticmethod
    def _add_years(dte, years_offset):
        """Return a date that's `years_offset` years after the date (or datetime)
        object `dte` (of type fields.Date). Return the same calendar date (month and day) in the
        destination year, if it exists, otherwise use the following day
        (thus changing February 29 to March 1).

        Code found on https://stackoverflow.com/questions/15741618/add-one-year-in-current-date-python
        """
        d = fields.Date.from_string(dte)
        try:
            return d.replace(year = d.year + years_offset)
        except ValueError:
            return d + (date(d.year + years_offset, 1, 1) - date(d.year, 1, 1))

    def _get_alias_name(self, name=''):
        if not name:
            name = self.name
        local_part = self.env['ir.config_parameter'].sudo().get_param('mail_local_part') or ''
        return f'{local_part}{"+" if local_part else ""}{name}'

    def _get_alias_name_dict(self, vals, force_get=False):
        if 'name' not in vals or 'alias_name' in vals and not force_get:
            return {}
        return {'alias_name': self._get_alias_name(vals['name'])}

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """ Checks that the start date is lower than the end date (otherwise, an exception is raised).

        :return: None
        """
        for period in self:
            if not period.start_date or not period.end_date or period.start_date > period.end_date:
                raise ValidationError(_('The end date should be higher than the start date. Please change it accordingly.'))

    @api.constrains('name')
    def _check_name_unique(self):
        """ Checks that the name of the period is unique.

        :return: None
        """
        for period in self:
            if self.search_count([('name', '=', period.name)]) > 1:
                raise ValidationError(_('The name of the period must be unique! Please change it accordingly.'))
