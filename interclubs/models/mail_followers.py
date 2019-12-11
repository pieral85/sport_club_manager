# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, exceptions


class Followers(models.Model):
    _inherit = 'mail.followers'

    mirror_follower_id = fields.Many2one('mail.followers', string='Mirror Follower',
        help='As followers are replicated between "Event" and "Interclub Event" models, '\
        'a reference must be kept between those 2 records.')

    @api.model
    def create(self, values):
        res = super(Followers, self).create(values)
        if values.get('res_model') in ('calendar.event', 'interclub.event') and values.get('res_id')\
           and not self.env.context.get('stop_propagation'):
            # 'calendar.event' and 'interclub.event' models are "mirrored" (through delegation inheritance),
            # thus creating a follower on one of this model implies having the same creation on the mirrored model
            if values['res_model'] == 'calendar.event':
                mirrored_record = self.env['interclub.event'].search([('event_id', '=', values['res_id'])], limit=1)
            elif values['res_model'] == 'interclub.event':
                mirrored_record = self.env['interclub.event'].browse(values['res_id']).event_id

            if mirrored_record:
                mirrored_follower = mirrored_record.message_follower_ids.filtered(
                    lambda mf: mf.partner_id.id == res.partner_id.id)
                # we duplicate follower on the "mirrored record" only if we are sure no other follower
                # already exist with the same partner (otherwise a psycopg2.IntegrityError is raised)
                if not mirrored_follower:
                    values['res_model'] = mirrored_record._name
                    values['res_id'] = mirrored_record.id
                    values['mirror_follower_id'] = res.id
                    mirrored_follower = res.with_context(stop_propagation=True).copy(default=values)
                else:
                    mirrored_follower.mirror_follower_id = res.id
                res.mirror_follower_id = mirrored_follower.id
        return res

    def write(self, values):
        res = super(Followers, self).write(values)
        values.pop('mirror_follower_id', None)
        if not self.env.context.get('stop_propagation') and values:
            self.mapped('mirror_follower_id').with_context(stop_propagation=True).write(values)
        return res

    def unlink(self):
        if not self.env.context.get('stop_propagation'):
            (self.mapped('mirror_follower_id') - self).with_context(stop_propagation=True).unlink()
        return super(Followers, self).unlink()
