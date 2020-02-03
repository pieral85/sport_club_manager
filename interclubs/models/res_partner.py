# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def get_attendee_detail_multi_model(self, meeting_id, model):
        """ Get attendees details event if the model is not 'calendar.event' (which can happen in case of delegation inheritance).
        """
        _models_fields = {
            'interclub.event': 'event_id',
        }
        if model == 'calendar.event':
            real_meeting_id = meeting_id
        else:
            if model not in _models_fields:
                raise NotImplementedError('Model "{}" not supported in method get_attendee_detail_multi_model.'.format(model))
            calendar_event_field = _models_fields[model]
            real_meeting_id = self.env[model].browse(meeting_id)[calendar_event_field].id
        return super(ResPartner, self).get_attendee_detail(real_meeting_id)
