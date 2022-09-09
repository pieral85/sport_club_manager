# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class InterclubEventMailWizard(models.TransientModel):
    _name = 'interclub.event.mail.wizard'
    _description = 'Interclub Event Mail Wizard'

    interclub_event_id = fields.Many2one('interclub.event', string='Interclub Event',
        required=True, ondelete='cascade')

    # === fields related to 1st email, for players ===
    send_to_players = fields.Boolean('Send to Players', default=True)
    default_attendee_ids = fields.One2many('calendar.attendee', related='interclub_event_id.attendee_ids',
        string='Default Players')
    attendee_ids = fields.Many2many('calendar.attendee', 'interclub_event_mail_wizard_attendee_rel',
        column1='wizard_id', column2='attendee_id', string='Players', domain="[('id', 'in', default_attendee_ids)]")
    composer_id = fields.Many2one('mail.compose.message', string='Composer (Players)', ondelete='cascade')
    # composer related fields
    template_id = fields.Many2one('mail.template', string='Mail Template',
        related='composer_id.template_id', readonly=False,
        domain=[('model', '=', 'calendar.attendee'), ('kind', '=', 'interclub')])
    subject = fields.Char(related='composer_id.subject', string='Subject (Players)', readonly=False)
    body = fields.Html(related='composer_id.body', string='Body (Players)', readonly=False)

    # === fields related to 2nd email, for partners other than players (referee and responsible by default) ===
    others_send_to_partners = fields.Boolean('Send to Others', default=False)
    others_composer_id = fields.Many2one('mail.compose.message', string='Composer (Others)',
        ondelete='cascade')
    others_include_followers = fields.Boolean('Include Followers', default=False)
    others_include_players = fields.Boolean('Include Players', default=False)
    # composer related fields
    others_partner_ids = fields.Many2many('res.partner', related='others_composer_id.partner_ids', readonly=False)
    others_subject = fields.Char(related='others_composer_id.subject', string='Subject (Others)',
        readonly=False)
    others_body = fields.Html(related='others_composer_id.body', string='Body (Others)', readonly=False)
    others_template_id = fields.Many2one('mail.template', string='Mail Template (Others)',
        related='others_composer_id.template_id', readonly=False,
        domain=[('model', '=', 'interclub.event'), ('kind', '=', 'interclub')])

    @api.model
    def default_get(self, fields):
        res = super(InterclubEventMailWizard, self).default_get(fields)
        if self.env.context.get('active_model') == 'interclub.event' and self.env.context.get('active_id'):
            ic_event = self.env['interclub.event'].browse(self.env.context['active_id'])
        else:
            raise NotImplementedError(_('Only the model "interclub.event" is supported for this mail wizard. '\
                'Current model: "{}".').format(self.env.context.get('active_model', '')))

        composer = self.env['mail.compose.message'].create({
            'composition_mode': 'mass_mail',
            'template_id': self.env.context.get('template_id', False),
        })
        # - For some unknown reason, writing the 'model' in the 'create' method may lead to a create access error.
        #   Thus, it has been moved to the 'write' method below
        # - Must be `calendar.attendee` model, because we set the `self.attendee_ids` as `active_ids` (in method
        #   `change_event_state`)
        composer.write({'model': 'calendar.attendee'})
        others_composer = self.env['mail.compose.message'].create({
            'composition_mode': 'comment',
            'template_id': self.env.ref('interclubs.email_template_interclub_event_viewer').id,
            'subtype_id': self.env.ref('interclubs.mt_interclub_event_communication').id,
        })

        # by default, others_composer.model == 'interclub.event'
        res.update({
            'interclub_event_id': ic_event.id,
            'composer_id': composer.id,
            'others_composer_id': others_composer.id,
            'send_to_players': self.env.context.get('send_mail_to_players', False),
            'others_send_to_partners': self.env.context.get('send_mail_to_others', False),
            'others_partner_ids': ic_event.referee_id | ic_event.interclub_id.responsible_id,
            'others_include_players': not self.env.context.get('show_mail_to_players', True),
        })
        return res

    @api.onchange('template_id')
    def _onchange_template_id(self):
        self.ensure_one()
        if self.composer_id:
            self.composer_id.template_id = self.template_id
            self.composer_id._onchange_template_id_wrapper()
            self.subject = self.composer_id.subject if self.template_id else ''
            self.body = self.composer_id.body

    @api.onchange('others_template_id')
    def _onchange_others_template_id(self):
        self.ensure_one()
        if self.others_composer_id:
            self.others_composer_id.template_id = self.others_template_id
            self.others_composer_id._onchange_template_id_wrapper()
            self.others_subject = self.others_composer_id.subject if self.others_template_id else ''
            self.others_body = self.others_composer_id.body

    @api.onchange('others_include_followers')
    def _onchange_others_include_followers(self):
        self.ensure_one()
        followers = self.interclub_event_id.message_follower_ids.partner_id
        if self.others_include_followers:
            self.others_partner_ids += followers
        else:
            self.others_partner_ids = self.others_partner_ids._origin - followers

    @api.onchange('others_include_players')
    def _onchange_others_include_players(self):
        self.ensure_one()
        players = self.default_attendee_ids.partner_id
        if self.others_include_players:
            self.others_partner_ids += players
        else:
            self.others_partner_ids = self.others_partner_ids._origin - players

    @api.onchange('interclub_event_id')
    def _onchange_interclub_event_id(self):
        self.attendee_ids = self.default_attendee_ids.filtered(lambda a: a.state in ('needsAction', 'tentative'))

    def change_event_state(self):
        self.ensure_one()
        role = self.env.context.get('role')
        if role == 'to_open':
            self.interclub_event_id.action_open()
        elif role == 'to_confirm':
            self.interclub_event_id.action_confirm()
        elif role == 'to_cancel':
            self.interclub_event_id.action_cancel()

        msgs = []

        def get_subtype_msg(composer):
            sub_type = composer.subtype_id
            if not sub_type or composer.composition_mode == 'mass_mail':
                return ''
            msg = _("and to subscribers of <a href=# data-oe-model={r_model} data-oe-id={r_id}>{r_name}</a>")
            return msg.format(r_model=sub_type._name, r_id=sub_type.id, r_name=sub_type.name)

        if self.send_to_players:
            ctx = {
                'active_model': self.attendee_ids._name,
                'active_ids': self.attendee_ids.ids,
            }
            self.with_context(**ctx).composer_id.action_send_mail()
            msg = self.template_id._get_sent_mail_message(self.attendee_ids.partner_id)
            msg += get_subtype_msg(self.composer_id)
            msgs.append(msg)

        if self.others_send_to_partners:
            other_ctx = {
                'active_ids': self.others_partner_ids.ids,  # TODO 2022-07-02 a l'air sans effet
                'mail_create_nosubscribe': True,  # do not add author as follower
            }
            subject = self.others_subject
            body = self.others_body
            self.others_composer_id._onchange_template_id_wrapper()
            # As method '_onchange_template_id_wrapper' overrided wizard's subject/body with template's subject/body,
            # we need need to keep the original subject/body of the wizard (which could have been modified by the user)
            self.others_subject = subject
            self.others_body = body
            self.with_context(**other_ctx).others_composer_id.action_send_mail()
            msg = self.others_template_id._get_sent_mail_message(self.others_partner_ids)
            msg += get_subtype_msg(self.others_composer_id)
            msgs.append(msg)

        if msgs:
            ic_event = self.env['interclub.event'].browse(self.env.context['active_id'])
            ic_event.message_post(body='<br>'.join(msgs))

        return {'type': 'ir.actions.act_window_close'}
