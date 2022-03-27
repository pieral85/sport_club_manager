# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class Meeting(models.Model):
    _inherit = 'calendar.event'

    item_color = fields.Char('Item Color',
        help='Color of the item in the calendar view')


class CalendarInterclubs(models.Model):
    _name = 'calendar.interclubs'
    _description = 'Calendar Interclubs'

    user_id = fields.Many2one('res.users', 'Me', required=True, default=lambda self: self.env.user)
    interclub_id = fields.Many2one('interclub', 'Interclub', required=True)
    active = fields.Boolean('Active', default=True)
    interclub_checked = fields.Boolean('Checked', default=True,
        help="This field is used to know if the interclub is checked in the filter of the calendar view for "\
        "the interclub_id.")

    _sql_constraints = [
        ('user_id_interclub_id_unique', 'UNIQUE(user_id, interclub_id)', 'A user cannot have the same interclub twice.')
    ]
