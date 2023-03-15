# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class Tournament(models.Model):
    _name = 'tournament'
    _description = 'Tournament'

    name = fields.Char()
    event_id = fields.Many2one('tournament.event', string='Event')
    player1_id = fields.Many2one('res.partner', string='Player 1')
    player2_id = fields.Many2one('res.partner', string='Player 2')
    event_ids = fields.One2many('tournament.event', 'tournament_id', string='Events')
    # ...season_id = fields.Many2one('period', string='Season',
    #     required=True, ondelete='restrict',
    #     default=lambda self: self.env['period'].search([('current', '=', True)], limit=1))