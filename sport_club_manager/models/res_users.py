# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# import json

# import requests
from re import match

from odoo import api, fields, models, exceptions
# from odoo.exceptions import AccessDenied, UserError
# from odoo.addons.auth_signup.models.res_users import SignupError

# from odoo.addons import base
# base.res.res_users.USER_PRIVATE_FIELDS.append('oauth_access_token')
# TODO Mettre un help= à tous les fields qui le nécessitent


class ResUsers(models.Model):
    _inherit = 'res.users'

    # TODO Should move to membership? (and merged into staus field?)
    secretary = fields.Boolean('Is Secretary', default=False)
    treasurer = fields.Boolean('Is Treasurer', default=False)
    president = fields.Boolean('Is President', default=False)
    administrator = fields.Boolean('Is Administrator', default=False)
    # TODO When secretary, treasurer or president is set ==> should be automatically administrator
    # status = fields.Selection(
    #     [
    #      ('not_member', 'Not a Member'),
    #      ('requested', 'Requested'),
    #      ('member', 'Member'),
    #      ('old_member', 'Old Member'),
    #     ],
    #     #required=True,
    #     default='member'
    # )

    membership_ids = fields.One2many(
        comodel_name='membership',
        inverse_name='user_id',
        # domain=[('is_company', '=', False)],
        string='Memberships',
    )

    @api.onchange('secretary')
    def _on_change_secretary(self):
        if self.secretary:
            self.administrator = True

    @api.onchange('treasurer')
    def _on_change_treasurer(self):
        if self.treasurer:
            self.administrator = True

    @api.onchange('president')
    def _on_change_president(self):
        if self.president:
            self.administrator = True

    @api.onchange('login')
    def validate_email(self):
        # import ipdb; ipdb.set_trace()
        if not self.login:
            return
        if not match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", self.login):
            raise exceptions.ValidationError('Invalid email address. Please enter a valid one.')
        if self.search_count([('login','=',self.login),]):
            raise exceptions.ValidationError('This email already exists. Please ')

    # @api.onchange('secretary')
    # def _onchange_status(self):
    #     self.groups_id = self.env['res.groups']
    #     #default_user or self.env['res.users']).sudo().groups_id
    #     # self.env['account.full.reconcile'].create({
    #     #     'partial_reconcile_ids': [(6, 0, partial_rec_ids)],
    #     #     'reconciled_line_ids': [(6, 0, self.ids)],
    #     #     'exchange_move_id': exchange_move.id if exchange_move else False,
    #     # })