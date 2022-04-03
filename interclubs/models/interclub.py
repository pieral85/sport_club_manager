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

    def _compute_events_count(self):
        for interclub in self:
            interclub.events_count = len(interclub.event_ids)

    def _compute_is_favorite(self):
        for interclub in self:
            interclub.is_favorite = self.env.user in interclub.favorite_user_ids

    def _inverse_is_favorite(self):
        favorite_interclubs = not_fav_interclubs = self.env['interclub'].sudo()
        for interclub in self:
            if self.env.user in interclub.favorite_user_ids:
                favorite_interclubs |= interclub
            else:
                not_fav_interclubs |= interclub

        # Interclub User has no write access for interclub
        not_fav_interclubs.write({'favorite_user_ids': [(4, self.env.uid)]})
        favorite_interclubs.write({'favorite_user_ids': [(3, self.env.uid)]})

    def _get_default_favorite_user_ids(self):
        return [(6, 0, [self.env.uid])]

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
    events_count = fields.Integer(compute='_compute_events_count', string='Events Count')

    favorite_user_ids = fields.Many2many(
        'res.users', 'interclub_favorite_user_rel', 'interclub_id', 'user_id',
        default=_get_default_favorite_user_ids,
        string='Favorite Users')
    is_favorite = fields.Boolean(compute='_compute_is_favorite', inverse='_inverse_is_favorite',
        string='Show Interclub on dashboard',
        help='Whether this Interclub should be displayed on your dashboard.')

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

    def action_view_events(self):
        sudo_self = self.with_context(active_id=self.id, active_ids=self.ids).sudo()
        action = sudo_self.env.ref('interclubs.action_interclub_event_active_interclub').read()[0]
        action['display_name'] = self.name
        return action
