# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# from datetime import date

from odoo import models, fields, api


class InterclubEventMailWizard(models.TransientModel):
    _name = 'interclub.event.mail.wizard'
    _description = 'Interclub Event Mail Wizard'
    # TODO Add an inheritance on 'mail.compose.message'???

    interclub_event_id = fields.Many2one('interclub.event', string='Interclub Event', required=True)

    send_to_attendees = fields.Boolean('Send Email to Players', default=True)
    attendee_ids = fields.Many2many('calendar.attendee', 'interclub_event_mail_wizard_attendee_rel',
        column1='wizard_id', column2='attendee_id', string='Attendees', domain="[('id', 'in', event_attendee_ids)]")#,        domain=lambda self: [('is_company', '=', True), ('id', '!=', self.env.user.company_id.partner_id.id)], **WRITABLE_STATES) # 'event_id', 'Participant')#, ondelete='cascade')
    # player_ids = fields.Many2many('res.partner', 'interclub_event_mail_wizard_player_rel',
    #     column1='wizard_id', column2='player_id', string='Players')  # TODO Add a default
    players_template_id = fields.Many2one('mail.template', string='Mail Template',
        domain=[('model', '=', 'calendar.attendee')],
        default=lambda self: self.env.ref('calendar.calendar_template_meeting_invitation'))
    # subject = fields.Char()  # TODO
    mail_body_TEST = fields.Html('Mail Body', default='', sanitize_style=True)#, readonly=True)


    send_to_other_partners = fields.Boolean('Send to Other Partners', default=True)
    others_composer_id = fields.Many2one('mail.compose.message', string='Composer for Other Partners', ondelete='cascade')
    other_partner_ids = fields.Many2many('res.partner', 'interclub_event_mail_wizard_other_partner_rel', string='Other partners')
    OLD_others_partner_ids = fields.Many2many('res.partner', string='OLD Partners', related='others_composer_id.partner_ids')  # TODO Add default
    others_subject = fields.Char(related='others_composer_id.subject')#'Subject', default=False)
    others_body = fields.Html(related='others_composer_id.body', default='', sanitize_style=True)  # 'Contents', default='', sanitize_style=True)
    # others_template_id = fields.Many2one('mail.template', related='others_composer_id.template_id',
    #     domain=[('model', '=', 'calendar.attendee')], readonly=False)  # domain devrait être un autre model # 'mail.template', 'Use template', index=True,
        # domain="[('model', '=', model)]")
    # other_contact_ids = fields.Many2many('res.partner', 'interclub_event_mail_wizard_player_rel',
    #     column1='wizard_id', column2='player_id', string='Players')  # TODO Add a default (referee + IC admin)
    other_contacts_template_id = fields.Many2one('mail.template', string='..TEST TEMPLATE',
        domain=[('model', '=', 'interclub.event')],
        default=lambda self: self.env.ref('interclubs.email_template_interclub_event_opening'))  # TODO Delete if not needed



    # Calendar Event related fields
    # calendar_event_id = fields.Many2one('calendar.event', related='interclub_event_id.event_id', string='TEST Calendar Event')  # testing...
    event_attendee_ids = fields.One2many('calendar.attendee', related='interclub_event_id.attendee_ids', string='Event Attendees')
# fields.Many2many('res.partner', related='event_id.partner_ids',
    #     domain=lambda self: [('is_company', '=', False), ('id', 'child_of', self.env.user.company_id.partner_id.id), ('type', '=', 'contact')], readonly=False)
# domain="[('partner_id','=', company_partner_id)]"

    @api.model
    def default_get(self, fields):
        from pprint import pprint as pp
        print('\n')
        pp(self.env.context)
        pp(fields)
        res = super(InterclubEventMailWizard, self).default_get(fields)
        if self.env.context.get('active_model') == 'interclub.event' and self.env.context.get('active_id'):
            ic_event = self.env['interclub.event'].browse(self.env.context['active_id'])
            partners = ic_event.referee_id | ic_event.interclub_id.responsible_id
        # res_ids = self._context.get('active_ids')
        self.env.context.get('active_id')
        # import ipdb; ipdb.set_trace()
# TODO Add notif_layout for composition_mode=='comment'?
        if self.env.get('active_model') != 'interclub.event':
            pass  # TODO Raise error
        composer = self.env['mail.compose.message'].create({
            'composition_mode': 'mass_mail', #1) 'mass_mail'# if len(res_ids) == 1 else 'mass_mail',
            # 'composition_mode': 'comment',# if len(res_ids) == 1 else 'mass_mail',


'model': 'interclub.event',  # 1) 'calendar.attendee',
# !!!'active_ids': self.env['active_ids'],  # 1) self.attendee_ids.ids
#'no_auto_thread': False,  # @pal to avoid required field 'reply_to'
# !!!'use_template': bool(self.other_contacts_template_id),  # 1) bool(self.players_template_id)
'template_id': self.other_contacts_template_id and self.other_contacts_template_id.id or False,  # 1) self.players_template_id
# ???force_email=True,


        })
        res.update({
            'interclub_event_id': ic_event.id,
            # 'invoice_ids': res_ids,
            'others_composer_id': composer.id,
            # 'other_contacts_template_id': self.env.ref('calendar.calendar_template_meeting_reminder').id,  # TODO Should be changed into sth more custom
            # 'others_template_id': self.env.ref('calendar.calendar_template_meeting_reminder').id,  # TODO Should be changed into sth more custom
            'other_partner_ids': partners.ids,
            # 'others_partner_ids': partners.ids,  NOT WORKING --> must be replaced by other_partner_ids 
        })
        return res

    # @api.onchange('others_template_id')
    @api.multi
    @api.onchange('other_contacts_template_id')
    def onchange_other_contacts_template_id(self):
        self.ensure_one()
        if self.others_composer_id:
            # import ipdb; ipdb.set_trace()
            self.others_composer_id.template_id = self.other_contacts_template_id
            # self.others_composer_id.template_id = self.others_template_id
            self.others_composer_id.onchange_template_id_wrapper()

    @api.onchange('other_partner_ids')
    def onchange_other_partner_ids(self):
        import ipdb; ipdb.set_trace()
        if self.others_composer_id:
            self.others_composer_id.partner_ids = self.other_partner_ids

    @api.multi
    def open_event(self):
        # self.send_mail()  # TODO
        self.ensure_one()
        self.interclub_event_id.open_interclub_event()
        import ipdb; ipdb.set_trace()
        self.others_composer_id.send_mail()
        template_ext_ident = self.other_contacts_template_id.get_external_id()[self.other_contacts_template_id.id]
        from pprint import pprint as pp
        # TODO Problè!me: il faudrait envoyer le contenu du body, pas le template lui-même
# self.attendee_ids._send_mail_to_attendees(template_ext_ident)
        # self. action_sendmail
        return {'type': 'ir.actions.act_window_close'}#, 'infos': 'mail_sent'}

    @api.onchange('interclub_event_id')
    def _onchange_interclub_event_id(self):
        print(self.event_attendee_ids)
        self.attendee_ids = self.event_attendee_ids


class InterclubEventMailPartner(models.TransientModel):
    _name = 'interclub.event.mail.partner'
    _description = 'Interclub Event Mail Partner'

    interclub_event_id = fields.Many2one('interclub.event', string='Interclub Event', required=True)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    # player_ids = fields.Many2many('res.partner', 'interclub_event_mail_wizard_player_rel',
    #     column1='wizard_id', column2='player_id', string='Players')  # TODO Add a default


