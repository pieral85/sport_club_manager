# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# import json

# import requests

from odoo import models, fields, api
# from odoo.exceptions import AccessDenied, UserError
# from odoo.addons.auth_signup.models.res_users import SignupError

# from odoo.addons import base
# base.res.res_users.USER_PRIVATE_FIELDS.append('oauth_access_token')

class ResUsers(models.Model):
    _inherit = 'res.users'
    _description = ''  # TODO

    ranking_ids = fields.One2many(
        comodel_name='ranking',
        inverse_name='member_id',
        string='Rankings History',
    )
    # current_ranking = fields.Many2one(
    #     comodel_name='ranking',
    #     string='Current Ranking',
    #     compute='_compute_current_ranking',
    #     # store=True,  # TODO Need to be stored?
    #     help='Ranking (as of today) of the player.',
    # )
    current_ranking = fields.Char(
        string='Current Ranking',
        compute='_compute_current_ranking',
        help='Ranking (as of today) of the player.',
    )

    # @api.onchange('ranking')
    @api.depends('ranking_ids')
    def _compute_current_ranking(self):
        import ipdb; ipdb.set_trace()
        for member in self:
            # TOTEST What happens if no recound found?
            ranking = member.ranking_ids.search_read(
                domain=[('member_id', '=', member.id),
                        ('start_date', '<=', fields.Date.today()),
                        ('end_date', '>=', fields.Date.today()),
                       ],
                fields=['ranking'],
                limit=1,
            )
            member.current_ranking = ranking[0]['ranking'] if ranking else ''


class Ranking(models.Model):
    _name = 'ranking'
    _description = ''  # TODO

    ranking = fields.Selection(
        selection=[
            ('D', 'D'),
            ('C2', 'C2'),
            ('C1', 'C1'),
            ('B2', 'B2'),
            ('B1', 'B1'),
            ('A', 'A'),
        ],
        string='Ranking',
        required=True,
        default='D',
        help='Ranking of the player.'
    )
    start_date = fields.Date(
        string='Start Date',
        default=fields.Date.today(),
        required=True
    )
    end_date = fields.Date(
        string='End Date',
        default=None,
        required=False
    )
    member_id = fields.Many2one(
        comodel_name='res.users',
        # inverse_name='ranking_ids',
        string='Member'
    )