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

    def get_attendee_detail(self, meeting_ids):
        """ Return a list of dict of the given meetings with the attendees details
            Used by:
                - base_calendar.js : Many2ManyAttendee
                - calendar_model.js (calendar.CalendarModel)
        """
        if 'meeting_ids_model' in self._context and 'calendar_event_field' in self._context:
            model, field = self._context['meeting_ids_model'], self._context['calendar_event_field']
            meetings = self.env[model].browse(meeting_ids)[field]
            assert meetings._name == 'calendar.event', \
                _("Model associated to 'many2manyattendee' widget should be 'calendar.event'")
            meeting_ids = meetings.ids
        return super(ResPartner, self).get_attendee_detail(meeting_ids=meeting_ids)

    def name_get(self):
        if not self._context.get('hide_company'):
            return super().name_get()
        res = []
        for partner in self:
            res.append((partner.id, partner.name))
        return res
