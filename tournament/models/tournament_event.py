# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class TournamentEvent(models.Model):
    _name = 'tournament.event'
    _description = 'Event'

    # name = fields.Char()
    # value = fields.Integer()
    # value2 = fields.Float(compute="_value_pc", store=True)
    # description = fields.Text()
    tournament_id = fields.Many2one('tournament', string='Tournament')
    entry_ids = fields.One2many('tournament.entry', 'event_id', string='Entries')
    gender = fields.Selection([('men', 'Men'), ('women', 'Women'), ('mixed', 'Mixed')], string='Gender')

    # @api.depends('value')
    # def _value_pc(self):
    #     for record in self:
    #         record.value2 = float(record.value) / 100
