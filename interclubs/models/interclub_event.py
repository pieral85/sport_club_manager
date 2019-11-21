# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# TODO By default, no email should be sent to an attendee when he is created
# TODO Add a field 'state' on 'interclub.event' (+ on 'interclub'?):
#  * values (to be discussed): 'draft', 'confirmed', 'done', 'cancelled'
#  * when draft, some fields are editable (i.e. partner_ids, ...)
#  * once confirmed, an email should be sent to attendees (with a wizard first..but maybe not...)
#    with module 'badminton' installed, we should confirmed onmy if >=4 players accepted the event
#  * if state 'confirmed' --> 'cancelled', an other email should be sent
#  * remove automatic email sent when creating an attendee
# TODO Add chatter in this model instead of 'calendar.event' (shit, calendar.event is standard)?
# TODO Add global parameters (+ inherited per interclub):
#   'opened_days'=10: days before interclub.event for which it must be confirmed
#   'auto_confirm'=False: confirm interclub.event when today + opened_days >= record.start (must be in a batch)
#   'auto_close'=False: close interclub.event when record.start > today (must be in a batch)
# TODO Add a check that forbids to create an event not in the range of the season_id
# TODO When loading demo data 1st time, calculation of current period is not triggered
# TODO Maybe we should replace button "calculation of current period" by an action
# TODO In calendar view, default attendees checked should at least incluse "Everybody's calendars"
# TODO In interclub.event, add a filter "Waiting Action"
# TODO When creatin an interclub.event (from calendar view and all other cases), a domain
#      should be applied on season_id (related to selected date)

from datetime import datetime, timedelta
from dateutil import parser
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT

WRITABLE_STATES = dict(readonly=True, states={'draft': [('readonly', False)], 'opened': [('readonly', False)]})

class InterclubEvent(models.Model):
    _name = 'interclub.event'
    _inherits = {'calendar.event': 'event_id'}
    _inherit = ['mail.thread']
    _description = 'Interclub Event'
    _order = 'start asc, id asc'

    state = fields.Selection([
             ('draft', 'Draft'),
             ('opened', 'Opened'),
             ('confirmed', 'Confirmed'),
             ('done', 'Done'),
             ('cancelled', 'Cancelled'),
        ], string='State', required=True, default='draft', track_visibility='always', readonly=True,
        help=" * The 'Draft' status is used at the creation on the event. In this state, the event can be modified without any restriction. None of the players will be warned of the change.\n"
             " * Once 'Opened', the players linked to the event will be advised of the event. In this state, they are invited to define their availability. In the meantime, modifications on the event are still possible. This state should be triggered enough days/weeks before the event occurs, so that players have enough time to give their availability.\n"
             " * Once 'Confirmed', the players receive an email summarizing the information related to the event. In this state, the record is locked, so that no modification is possible. This state should be triggered a few days before the event and remain until it occurs.\n"
             " * The 'Done' status should be set only after the event occured.\n"
             " * The 'Cancelled' status is used when the event won't happen and therefore, must be cancelled.")
    interclub_id = fields.Many2one('interclub', string='Interclub',
        required=True, ondelete='cascade', **WRITABLE_STATES)
    item_color = fields.Char(compute='_compute_item_color', store=False,
        help='Color of the item in the calendar view')
    at_home = fields.Boolean('At Home', **WRITABLE_STATES)
    referee_id = fields.Many2one('res.partner', string='Referee', **WRITABLE_STATES)
    event_id = fields.Many2one('calendar.event', string='Calendar Event',
        required=True, ondelete='restrict', readonly=True)
    opponent_id = fields.Many2one('res.partner', string='Opponent', required=True,
        domain=lambda self: [('is_company', '=', True), ('id', '!=', self.env.user.company_id.partner_id.id)], **WRITABLE_STATES)
    action_required = fields.Selection([
        ('nothing', 'Nothing'),
        ('nothing_cancelled', 'Nothing'),
        ('need_opening', 'Need Opening'),
        ('need_opening_overdue', 'Need Opening (overdue)'),
        ('need_confirmation', 'Need Confirmation'),
        ('need_confirmation_overdue', 'Need Confirmation (overdue)'),
        ('need_close', 'Need to Close'),
    ], string='Action Required', compute='_compute_action_required')

    # Interclub related fields
    interclub_player_ids = fields.Many2many('res.partner', related='interclub_id.player_ids', readonly=True)
    interclub_referee_ids = fields.Many2many('res.partner', related='interclub_id.referee_ids', readonly=True)
    season_id = fields.Many2one('period', related='interclub_id.season_id', readonly=True, store=True)

    # Calendar Event related fields
    # As writing '**WRITABLE_STATES' on a related field is not working, the equivalent domain must be written
    # in view(s) where this field appears
    partner_ids = fields.Many2many('res.partner', related='event_id.partner_ids',
        domain=lambda self: [('is_company', '=', False), ('id', 'child_of', self.env.user.company_id.partner_id.id), ('type', '=', 'contact')], readonly=False)

    @api.multi
    def action_open_interclub_event(self):
        return self.get_formview_action()

    @api.multi
    @api.depends('opponent_id', 'interclub_id')
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id , '{}: {}'.format(record.interclub_id.name, record.opponent_id.name)))
        return result

    @api.model
    def create(self, values):
        if 'interclub_id' not in values or 'opponent_id' not in values:
            raise UserError(_('You cannot create an event without being attached to an interclub.'))
        interclub = self.env['interclub'].browse(values['interclub_id'])
        if 'name' not in values:
            opponent_name = self.env['res.partner'].browse(values['opponent_id']).name
            values['name'] = '{}: {}'.format(interclub.name, opponent_name)

        ret = super(InterclubEvent, self.with_context(no_mail_to_attendees=True)).create(values)
        if 'res_model_id' not in values and 'res_id' not in values:
            ret.write({
                'res_model_id': self.env['ir.model'].search([('model', '=', 'interclub.event')], limit=1).id,
                'res_id': ret.id,
            })
        ret.event_id.write({'item_color': interclub.event_items_color})
        return ret

    @api.multi
    def write(self, values):
        if 'partner_ids' in values:
            self = self.with_context(no_mail_to_attendees=True)
        return super(InterclubEvent, self).write(values)

    @api.multi
    def unlink(self):
        ''' Delete related calendar event '''
        calendar_events = self.mapped('event_id')
        ret = super(InterclubEvent, self).unlink()
        calendar_events.unlink()
        return ret

    @api.multi
    def prepare_interclub_event_wizard(self):
        ctx = self._context.copy()
        # ctx['default_interclub_event_id'] = self.id  # TODO I don't think it is required
        # most_recent_period = self.env['period'].search(['|', ('active', '=', False), ('active', '=', True),], order='start_date desc', limit=1)
        # start_date = Period._add_years(most_recent_period.start_date, 1)
        # end_date = Period._add_years(most_recent_period.end_date, 1)
        # ctx['default_start_date'] = start_date
        # ctx['default_end_date'] = end_date
        # ctx['default_name'] = 'Season %s' % start_date.year
        # if start_date.year != end_date.year:
        #     ctx['default_name'] += ' - %s' % end_date.year
        return {
            'name': 'TEST!!!',  # TODO Rename
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'src_model': 'interclub.event',
            'res_model': 'interclub.event.mail.wizard',
            'view_id': self.env.ref('interclubs.interclub_event_mail_wizard_form_view').id,
            'context': ctx,
            'target': 'new',
        }

    @api.multi
    def open_interclub_event(self):
        # for record in self:
        #     # TODO
        #     # self.event_id.action_sendmail()
        #     record.action_sendmail()
        #     # record.state = 'draft'  # TODO must be 'opened'
        self.write({'state': 'draft'})  # TODO must be 'opened'
        # return self.action_sendmail()  # TODO Delete if not needed

    @api.multi
    def confirm_interclub_event(self):
        for record in self:
            # TODO Add a check: only record.intervlub_id.responsible_id or interclubs.group_interclubs_interclub_manager can do it (otherwise: error)
            # TODO only from state 'draft'
            # TODO Send an email to attendees
            # TODO Do the same for other methods
            record.state = 'confirmed'

    @api.multi
    def close_interclub_event(self):
        for record in self:
            # TODO
            record.state = 'done'

    @api.multi
    def cancel_interclub_event(self):
        for record in self:
            # TODO
            record.state = 'cancelled'

    @api.multi
    def set_draft_interclub_event(self):
        for record in self:
            # TODO
            record.state = 'draft'

    def update_states(self, auto_mail=False):
        today = datetime.today()
        auto_open = bool(self.env['ir.config_parameter'].sudo().get_param('event.auto.open', default=False))
        if auto_open:
            opening_days = int(self.env['ir.config_parameter'].sudo().get_param('event.opening.days', default=10))
            expected_opening_date = today + timedelta(days=opening_days)
            self.env['interclub.event'].search([
                ('state', '=', 'draft'),
                ('start', '<=', expected_opening_date),
                ('start', '>', today),
            ]).open_interclub_event()
            # ]).with_context(send_automatically=auto_mail).open_interclub_event()
        auto_close = bool(self.env['ir.config_parameter'].sudo().get_param('event.auto.close', default=False))
        if auto_close:
            events_to_close = self.env['interclub.event'].search([
                ('state', '=', 'confirmed'),
                ('stop', '<=', today),
            ]).close_interclub_event()

    # TODO As a more generic method, we should extend 'DateField' and 'search_inputs.Field' JS widget instead
    # It would do the job for all date/datetime objects
    # @api.model
    # def search(self, args, offset=0, limit=None, order=None, count=False):
    #     new_domain = []
    #     for i, domain in enumerate(args):
    #         if domain[0] == 'start':
    #             # import ipdb; ipdb.set_trace()
    #             try:
    #                 start_date = parser.parse(domain[2]).date()#, fuzzy=True)
    #                 end_date = start_date + relativedelta(days=1)
    #                 # args = [['start', '=', '2009-01-24 19:19:00']]
    #                 # TODO if domain[2] starts with year, dayfirst should be False (format ~= yyyy/mm/dd)
    #                 # otherwise, dayfirst should be True (format ~= dd/mm/yyyy)
    #                 # new_domain.extend(['&', ['start', '>=', start_date], ['start', '<', end_date]])
    #                 # TODO We should consider timezone!!! Otherwise there is an offset of 2 hours
    #                 # import ipdb; ipdb.set_trace()
    #                 test = fields.Date.to_date(start_date)
    #                 new_domain.extend(['&', ['start', '>=', start_date.strftime(DATE_FORMAT)], ['start', '<', end_date.strftime(DATE_FORMAT)]])
    #                 continue

    #             except ValueError as tmp:
    #                 print(tmp)
    #                 pass
    #         new_domain.append(domain)
    #     print('\n', args)
    #     print(new_domain)
    #     return super(InterclubEvent, self).search(new_domain, offset, limit, order, count=count)

    # TODO
    @api.multi
    def action_sendmail(self):
        from pprint import pprint as pp
        print(self)
        pp(self.env.context)
        # if self.env.context.get('send_automatically'):
        #     # return self.event_id.action_sendmail()
        #     return self.mapped('event_id').action_sendmail()
        #     # return super(InterclubEvent, self).action_sendmail()
        self.ensure_one()
        # TODO Investigate why the layout of the generated email is different than the one following line:
        # return self.event_id.action_sendmail()
        # looking at 'custom_layout' could help
# attention, self peut etre multi!
        template = self.env.ref('calendar.calendar_template_meeting_invitation')
        # memberships = self.filtered(lambda m: m.state not in ('requested', 'member', 'rejected'))
        attendees = self.attendee_ids
        from pprint import pprint as pp
        pp(attendees)

# <mail.template>.send_mail(..., notif_layout='...')

        if attendees:
            compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
            ctx = dict(
# @pal base_url=self.env['ir.config_parameter'].sudo().get_param('web.base.url', default='http://localhost:8069'),
custom_layout='mail.mail_notification_light',  # @pal
                # send_mail_kwargs={'custom_layout': 'mail.mail_notification_light'},
                dbname=self._cr.dbname,  # USEFULL
# @pal only_invitation_emails=True,
            default_res_id=attendees.ids[0],  # USEFULL
            # @pal default_partner_ids=attendees.mapped('partner_id').ids,  # mail recipients  # USEFULL
                default_model='calendar.attendee',
                active_ids=attendees.ids,
default_no_auto_thread=False,  # @pal to avoid required field 'reply_to'
                default_use_template=bool(template),
                default_template_id=template and template.id or False,
                default_composition_mode='comment',
                force_email=True,
            )
# ===== @pal =====
# use_active_domain: True
# 'default_use_active_domain': True,
# 'active_domain': [('name', 'in', ['%s' % self.test_record.name, '%s' % test_record_2.name])],
# ===== /@pal =====
            pp(ctx)
            # template = template.with_context(ctx)
            # import ipdb; ipdb.set_trace()
            return {
                'name': _('Compose Email - Interclub Event Invitation'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(compose_form.id, 'form')],
                'target': 'new',
                'context': ctx,
            }


# Backup avec mass.mail
#     # TODO
#     @api.multi
#     def action_sendmail(self):
#         from pprint import pprint as pp
#         print(self)
#         pp(self.env.context)
#         # if self.env.context.get('send_automatically'):
#         #     # return self.event_id.action_sendmail()
#         #     return self.mapped('event_id').action_sendmail()
#         #     # return super(InterclubEvent, self).action_sendmail()
#         self.ensure_one()
#         # TODO Investigate why the layout of the generated email is different than the one following line:
#         # return self.event_id.action_sendmail()
#         # looking at 'custom_layout' could help
# # attention, self peut etre multi!
#         template = self.env.ref('calendar.calendar_template_meeting_invitation')
#         # memberships = self.filtered(lambda m: m.state not in ('requested', 'member', 'rejected'))
#         attendees = self.attendee_ids
#         from pprint import pprint as pp
#         pp(attendees)

# # <mail.template>.send_mail(..., notif_layout='...')

#         if attendees:
#             compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
#             ctx = dict(
# # @pal colors={
# #     'needsAction': 'red',
# #     'accepted': 'yellow',  #'green',
# #     'tentative': '#FFAA11',
# #     'declined': 'red'
# # },
# # @pal base_url=self.env['ir.config_parameter'].sudo().get_param('web.base.url', default='http://localhost:8069'),
# custom_layout='mail.mail_notification_light',  # @pal
#                 # send_mail_kwargs={'custom_layout': 'mail.mail_notification_light'},
#                 dbname=self._cr.dbname,  # USEFULL
# # @pal only_invitation_emails=True,
#             # @pal default_res_id=attendees.ids[0],  # USEFULL
#             # @pal default_partner_ids=attendees.mapped('partner_id').ids,  # mail recipients  # USEFULL
#                 default_model='calendar.attendee',
#                 active_ids=attendees.ids,
# default_no_auto_thread=False,  # @pal to avoid required field 'reply_to'
#                 default_use_template=bool(template),
#                 default_template_id=template and template.id or False,
#                 default_composition_mode='mass_mail',  #@pal: must be in ('mass_mail', 'mass_post')  # old: 'comment'
#                 force_email=True,
#             #@pal default_use_active_domain=True,  #@pal
#             )
# # ===== @pal =====
# # use_active_domain: True
# # 'default_use_active_domain': True,
# # 'active_domain': [('name', 'in', ['%s' % self.test_record.name, '%s' % test_record_2.name])],
# # ===== /@pal =====
#             pp(ctx)
#             # template = template.with_context(ctx)
#             # import ipdb; ipdb.set_trace()
#             return {
#                 'name': _('Compose Email - Interclub Event Invitation'),
#                 'type': 'ir.actions.act_window',
#                 'view_mode': 'form',
#                 'res_model': 'mail.compose.message',
#                 'views': [(compose_form.id, 'form')],
#                 'target': 'new',
#                 'context': ctx,
#             }

    @api.depends('interclub_id.event_items_color')
    def _compute_item_color(self):
        for ic_event in self:
            ic_event.item_color = ic_event.interclub_id.event_items_color

    def _compute_action_required(self):
        today = datetime.today()
        opening_days = int(self.env['ir.config_parameter'].sudo().get_param('event.opening.days', default=10))
        expected_opening_date = today + timedelta(days=opening_days)
        confirmation_days = int(self.env['ir.config_parameter'].sudo().get_param('event.confirmation.days', default=5))
        expected_confirmation_date = today + timedelta(days=confirmation_days)
        for ic_event in self:
            in_opening_period = expected_opening_date >= ic_event.start
            in_confirmation_period = expected_confirmation_date >= ic_event.start
            event_past = today >= ic_event.start
            if ic_event.state == 'draft':
                if event_past or in_confirmation_period:
                    ic_event.action_required = 'need_opening_overdue'
                elif in_opening_period:
                    ic_event.action_required = 'need_opening'
                else:
                    ic_event.action_required = 'nothing'
            elif ic_event.state == 'opened':
                if event_past:
                    ic_event.action_required = 'need_confirmation_overdue'
                elif in_confirmation_period:
                    ic_event.action_required = 'need_confirmation'
                else:
                    ic_event.action_required = 'nothing'
            elif ic_event.state == 'confirmed':
                if event_past:
                    ic_event.action_required = 'need_close'
                else:
                    ic_event.action_required = 'nothing'
            elif ic_event.state == 'cancelled':
                ic_event.action_required = 'nothing_cancelled'
            else:  # elif ic_event.state == 'done':
                ic_event.action_required = 'nothing'

    @api.onchange('start')
    def _onchange_start(self):
        if self.start:
            event_duration = int(self.env['ir.config_parameter'].sudo().get_param('interclub.event.duration', default=3))
            self.stop = self.start + timedelta(hours=event_duration)
