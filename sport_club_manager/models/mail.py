# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import uuid

from odoo import api, fields, models, _
from odoo.addons.mail.wizard.mail_compose_message import _reopen


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.onchange('model')
    def _onchange_model(self):
        domain = [('model', '=', self.model)]
        if self.env.context.get('only_invitation_emails'):
            domain.append(('is_membership_invitation_mail', '=', True))
        if self.env.context.get('only_confirmation_emails'):
            domain.append(('is_membership_confirmation_mail', '=', True))

        return {'domain': {'template_id': domain}}

    @api.multi
    def send_mail(self, auto_commit=False):
        self.ensure_one()
        model = self.env.context.get('default_model')

        if model == 'membership':
            self.env[model].browse(self.env.context['active_ids']).reset_token()

        res = super(MailComposer, self).send_mail(auto_commit)

        if model == 'membership' and self.env.context.get('active_ids'):
            vals = {}
            if self.template_id.is_membership_invitation_mail:
                vals['invitation_mail_sent'] = True
            if self.template_id.is_membership_confirmation_mail:
                vals['confirmation_mail_sent'] = True
            self.env['membership'].browse(self.env.context['active_ids']).write(vals)
            return {
                'name': _('Memberships with Mail Sent'),
                'type': 'ir.actions.act_window',
                'res_model': 'membership',
                'view_mode': 'tree,form',
                'view_type': 'form',
                'domain': [('id', 'in', self.env.context['active_ids'])],
            }
        return res

    @api.multi
    def save_as_template(self):
        """ Override parent method that was only doing a shallow copy of the template.
            Parent method comment:
            hit save as template button: current form value will be a new
            template attached to the current document. """
        for record in self:
            template = record.template_id.copy({
                'subject': record.subject or False,
                'body_html': record.body or False,
                'attachment_ids': [(6, 0, [att.id for att in record.attachment_ids])],
            })
            # generate the saved template
            record.write({'template_id': template.id})
            record.onchange_template_id_wrapper()
            return _reopen(self, record.id, record.model, context=self._context)



class MailTemplate(models.Model):
    _inherit = "mail.template"

    is_membership_invitation_mail = fields.Boolean('Is A Membership Invitation Mail',
        help='If True, memberships sent with this email template will be marked with an invitation mail as sent.')
    is_membership_confirmation_mail = fields.Boolean('Is A Membership Confirmation Mail',
        help='If True, memberships sent with this email template will be marked with a confirmation mail as sent.')
