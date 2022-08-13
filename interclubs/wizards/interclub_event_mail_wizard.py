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

        template_id = self.env.context.get('template_id',
            self.env.ref('interclubs.email_template_interclub_event_opening').id)
        composer = self.env['mail.compose.message'].create({
            'composition_mode': 'mass_mail',
            'template_id': template_id,
        })
        # For some unknown reason, writing the 'model' in the 'create' method may lead to a create access error.
        # Thus, it has been moved to the 'write' method below
        composer.write({
            'model': 'calendar.attendee',
        })
        # TODO Add notif_layout for composition_mode=='comment'?
        others_composer = self.env['mail.compose.message'].create({
            'composition_mode': 'comment',
            'res_id': self.env.context['active_id'],
            'model': self.env.context['active_model'],
            'template_id': template_id,
        })
        res.update({
            'interclub_event_id': ic_event.id,
            'composer_id': composer.id,
            'others_composer_id': others_composer.id,
            'send_to_players': self.env.context.get('send_mail_to_players', False),
            'others_send_to_partners': self.env.context.get('send_mail_to_others', False),
        })
        return res

    @api.onchange('template_id')
    def onchange_template_id(self):
        self.ensure_one()
        if self.composer_id:
            self.composer_id.template_id = self.template_id
            self.composer_id._onchange_template_id_wrapper()
            self.subject = self.composer_id.subject if self.template_id else ''
            self.body = self.composer_id.body

    @api.onchange('others_template_id')
    def onchange_others_template_id(self):
        self.ensure_one()
        if self.others_composer_id:
            if not self.others_partner_ids:
                players = self.default_attendee_ids.filtered(lambda a: a.state not in ('needsAction', 'tentative'))\
                    .mapped('partner_id')
                self.others_partner_ids = self.interclub_event_id.referee_id \
                    | self.interclub_event_id.interclub_id.responsible_id | players
            self.others_composer_id.template_id = self.others_template_id
            self.others_composer_id._onchange_template_id_wrapper()
            self.others_subject = self.others_composer_id.subject if self.others_template_id else ''
            self.others_body = self.others_composer_id.body

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

        if self.send_to_players:
            ctx = {
                'dbname': self._cr.dbname,
                'active_ids': self.attendee_ids.ids,
            }
            self.with_context(**ctx).composer_id.action_send_mail()

        if self.others_send_to_partners:
            subject = self.others_subject
            body = self.others_body
            self.others_composer_id._onchange_template_id_wrapper()
            # As method '_onchange_template_id_wrapper' overrided wizard's subject/body with template's subject/body,
            # we need need to keep the original subject/body of the wizard (which could have been modified by the user)
            self.others_subject = subject
            self.others_body = body
            self.others_composer_id.action_send_mail()

        return {'type': 'ir.actions.act_window_close'}
