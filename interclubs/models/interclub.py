# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, exceptions, tools, _

CONTACT_DOMAIN = lambda self: [
    ('is_company', '=', False),
    ('id', 'child_of', self.env.user.company_id.partner_id.id),
    ('type', '=', 'contact')
]

class Interclub(models.Model):
    _name = 'interclub'
    _description = 'Interclub'
    _order = 'season_id asc, kind asc'

    name = fields.Char(string='Name', required=True)
    event_ids = fields.One2many('interclub.event', 'interclub_id',
        string='Interclub Events')
    kind = fields.Selection([('men', 'Men'), ('women', 'Women'), ('mixed', 'Mixed')],
        string='Kind', required=True, default='men')
    season_id = fields.Many2one('period', string='Season',
        required=True, ondelete='restrict',
        default=lambda self: self.env['period'].search([('current', '=', True)], limit=1))
    player_ids = fields.Many2many('res.partner', 'interclub_player_rel',
        column1='interclub_id', column2='player_id', string='Players',
        domain=CONTACT_DOMAIN)
    responsible_id = fields.Many2one('res.partner', string='Responsible',
        domain=CONTACT_DOMAIN)
    location_id = fields.Many2one('res.partner', string='Location',
        domain=lambda self: [('parent_id', '=', self.env.user.company_id.partner_id.id), ('type', '!=', 'contact')])
    referee_ids = fields.Many2many('res.partner', 'interclub_referee_rel',
        column1='interclub_id', column2='referee_id', string='Referees',
        domain=CONTACT_DOMAIN)
    event_items_color = fields.Char('Event Items Color',
        help='Color of the interclub event items in the calendar view')  # TODO Rename with events_color?

    def write(self, vals):
        if 'event_items_color' in vals:
            self.event_ids.mapped('event_id').write({'item_color': vals['event_items_color']})
        return super(Interclub, self).write(vals)

    def unlink(self):
        # even if "ondelete='cascade'" has been activated on field <interclub.event>.interclub_id,
        # we need to explicitly call the "ondelete" method on the event_ids,
        # so that their calendar_events will  also be deleted
        self.event_ids.unlink()
        return super(Interclub, self).unlink()

    @api.onchange('kind', 'season_id')
    def _onchange_kind_season(self):
        vals = []
        if self.kind:
            vals.append(dict(self.env['interclub']._fields['kind']._description_selection(self.env))[self.kind])
        if self.season_id:
            vals.append(self.season_id.name)
        if vals:
            self.name = ' - '.join(vals)
