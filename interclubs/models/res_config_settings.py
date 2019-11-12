# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    interclub_event_duration = fields.Integer('Interclub Event Duration', default=3,
        help='Default duration for an interclub event (in hours).', config_parameter='interclub.event.duration')
    event_opening_days = fields.Integer('Event Opening Days', default=10,
        help='Number of days before the event from which it must be opened.', config_parameter='event.opening.days')
    event_auto_open = fields.Boolean('Event Automatic Opening', default=False,
        help='If true, the event is automatically opened when today is X days before the event starts ("X" is defined by the "Event Opening Days" parameter).', config_parameter='event.auto.open')
    event_confirmation_days = fields.Integer('Event Confirmation Days', default=5,
        help='Number of days before the event from which it must be confirmed.', config_parameter='event.confirmation.days')
    event_auto_close = fields.Boolean('Event Automatic Closing', default=False,
        help='If true, the event is automatically closed once its end date is reached.', config_parameter='event.auto.close')

    @api.one
    @api.constrains('event_opening_days', 'event_confirmation_days')
    def _check_days(self):
        """ Checks that the opening days is always higher than the confirmation days. Both must also be positive (otherwise, an exception is raised).

        :return: None
        """
        if self.event_opening_days < 0:
            raise ValidationError(_('The "Event Opening Days" must be positive. Please change it accordingly.'))
        if self.event_confirmation_days < 0:
            raise ValidationError(_('The "Event Confirmation Days" must be positive. Please change it accordingly.'))
        if self.event_opening_days < self.event_confirmation_days:
            raise ValidationError(_('The "Event Opening Days" must be higher than the "Event Confirmation Days". Please change them accordingly.'))
