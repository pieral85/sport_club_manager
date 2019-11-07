# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# from re import match

from odoo import api, fields, models, exceptions, _


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

    # @api.multi
    # def _stop_role(self):
    #     import ipdb; ipdb.set_trace()
    #     for role in self:
    #         ole

    @api.one
    @api.constrains('start_date', 'end_date', 'name')
    def _check_dates(self):
        """ Checks that no other role has been defined in a common period for current user (otherwise, an exception is raised).
        Also checks that the start date is lower than the end date (otherwise, an exception is raised).

        :return: None
        """
        _domain = [
            ('user_id.id', '=', self.user_id.id),
            ('name', '=', self.name),
            '|', ('end_date', '=', False), ('end_date', '>', self.start_date),
            ]
        if self.end_date:
            _domain.append(('start_date', '<', self.end_date))
        count_common_roles = self.env['role'].search_count(_domain) - 1
        if count_common_roles:
            # TODO As self.name is a selection field, it should display its "correct" value (eg 'President' instead of 'president')
            raise exceptions.ValidationError(_("The role '%s' you are trying to assign to user '%s' has already been defined within this period. Please change it accordingly.") % (self.name, self.user_id.name))
        if self.end_date and (not self.start_date or self.start_date >= self.end_date):
            raise exceptions.ValidationError(_('The end date should be higher than the start date. Please change it accordingly.'))
