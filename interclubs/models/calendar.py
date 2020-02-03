# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class Meeting(models.Model):
    _inherit = 'calendar.event'

    item_color = fields.Char('Item Color',
        help='Color of the item in the calendar view')
