# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# from re import match

from odoo import api, fields, models, exceptions, _
from odoo.exceptions import ValidationError


# TODO Add a daily CRON which computes 'current' field (use '_compute_current' fonction?)
# Modify and create demo datas with some roles
class Role(models.Model):
    _name = 'role'
    _description = 'Role'
    _order = 'end_date desc'
    _sql_constraints = [
       ('dates_check', 'CHECK(start_date < end_date)',
        'The end date should be higher than the start date. Please change it accordingly.'),
    ]

    name = fields.Selection(
        string='Role',
        selection=[
         ('president', 'President'),
         ('secretary', 'Secretary'),
         ('treasurer', 'Treasurer'),
        ],
        required=True,
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        ondelete='cascade',
        required=True,
        string='User',
    )
    start_date = fields.Date(
        string='Start Date',
        default=fields.Date.today(),
        required=True,
    )
    end_date = fields.Date(
        string='End Date',
        default=None,
    )
    current = fields.Boolean(
        string='Is Current',
        compute='_compute_current',
        store=True,
        readonly=True,
    )

    @api.depends('start_date', 'end_date')
    def _compute_current(self):
        today = fields.Date.today()
        for role in self:
            role.current = role.start_date <= today and (not role.end_date or role.end_date > today)

    # def _stop_role(self):
    #     import ipdb; ipdb.set_trace()
    #     for role in self:
    #         ole

    @api.constrains('start_date', 'end_date', 'name')
    def _check_dates(self):
        """ Checks that no other role has been defined in a common period for current user (otherwise, an exception is raised).
        Also checks that the start date is lower than the end date (otherwise, an exception is raised).

        :return: None
        """
        for role in self:
            _domain = [
                ('user_id.id', '=', role.user_id.id),
                ('name', '=', role.name),
                '|', ('end_date', '=', False), ('end_date', '>', role.start_date),
                ]
            if role.end_date:
                _domain.append(('start_date', '<', role.end_date))
            count_common_roles = role.env['role'].search_count(_domain) - 1
            if count_common_roles:
                # TODO As role.name is a selection field, it should display its "correct" value (eg 'President' instead of 'president')
                raise ValidationError(_("The role '%s' you are trying to assign to user '%s' has already been defined within this period. Please change it accordingly.") % (role.name, role.user_id.name))
            if role.end_date and (not role.start_date or role.start_date >= role.end_date):
                raise ValidationError(_('The end date should be higher than the start date. Please change it accordingly.'))
