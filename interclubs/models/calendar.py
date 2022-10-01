# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class Meeting(models.Model):
    _inherit = 'calendar.event'

    item_color = fields.Char('Item Color',
        help='Color of the item in the calendar view')

    def message_notify(self, *, partner_ids=False, parent_id=False, model=False, res_id=False,
                       author_id=None, email_from=None, body='', subject=False, **kwargs):
        if 'forced_email_layout_xmlid' in self._context:
            kwargs['email_layout_xmlid'] = self._context['forced_email_layout_xmlid']
        super().message_notify(
           partner_ids=partner_ids, parent_id=parent_id, model=model, res_id=res_id,
           author_id=author_id, email_from=email_from, body=body, subject=subject, **kwargs)

class Attendee(models.Model):
    _inherit = 'calendar.attendee'

    def _get_closest_lang(self):
        return self.mapped('partner_id')._get_closest_lang()


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
