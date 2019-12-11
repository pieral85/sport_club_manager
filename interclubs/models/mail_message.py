# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class Message(models.Model):
    _inherit = 'mail.message'

    mirror_message_id = fields.Many2one('mail.message', string='Mirror Message',
        help='As messages are replicated between "Event" and "Interclub Event" models, '\
        'a reference must be kept between those 2 records.')

    @api.model
    def create(self, values):
        res = super(Message, self).create(values)
        if values.get('model') in ('calendar.event', 'interclub.event') and values.get('res_id')\
           and not self.env.context.get('stop_propagation'):
            # 'calendar.event' and 'interclub.event' models are "mirrored" (through delegation inheritance),
            # thus creating a message on one of this model implies having the same creation on the mirrored model
            if values['model'] == 'calendar.event':
                mirrored_record = self.env['interclub.event'].search([('event_id', '=', values['res_id'])], limit=1)
            elif values['model'] == 'interclub.event':
                mirrored_record = self.env['interclub.event'].browse(values['res_id']).event_id

            if mirrored_record and res.body:
                values['model'] = mirrored_record._name
                values['res_id'] = mirrored_record.id
                values['mirror_message_id'] = res.id
                mirrored_message = res.with_context(stop_propagation=True).copy(default=values)
                res.mirror_message_id = mirrored_message.id
        return res

    def write(self, values):
        res = super(Message, self).write(values)
        values.pop('mirror_message_id', None)
        if not self.env.context.get('stop_propagation') and values:
            self.mapped('mirror_message_id').with_context(stop_propagation=True).write(values)
        return res

    def unlink(self):
        if not self.env.context.get('stop_propagation'):
            (self.mapped('mirror_message_id') - self).with_context(stop_propagation=True).unlink()
        return super(Message, self).unlink()
