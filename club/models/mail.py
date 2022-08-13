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
        kinds = []
        if self.env.context.get('only_invitation_emails'):
            kinds.append('membership_invitation')
        if self.env.context.get('only_confirmation_emails'):
            kinds.append('membership_confirmation')
        domain.append(('kind', 'in', kinds if kinds else ['standard']))

        return {'domain': {'template_id': domain}}
        # TODO log send a wrning: WARNING scm15 odoo.models: onchange method MailComposer._onchange_model returned a domain, this is deprecated

    def action_send_mail(self):
        self.ensure_one()
        model = self.env.context.get('default_model')

        if model == 'membership':
            self.env[model].browse(self.env.context['active_ids']).reset_token()

        res = super(MailComposer, self).action_send_mail()

        if model == 'membership' and self.env.context.get('active_ids'):
            vals = {}
            if self.template_id.kind == 'membership_invitation':  # TODO Test me
                vals['invitation_mail_sent'] = True
            if self.template_id.kind == 'membership_confirmation':
                vals['confirmation_mail_sent'] = True
            self.env['membership'].browse(self.env.context['active_ids']).write(vals)
            return {
                'name': _('Memberships with Mail Sent'),
                'type': 'ir.actions.act_window',
                'res_model': 'membership',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', self.env.context['active_ids'])],
            }
        return res

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
            record._onchange_template_id_wrapper()
            return _reopen(self, record.id, record.model, context=self._context)



class MailTemplate(models.Model):
    _inherit = 'mail.template'

    kind = fields.Selection([
            ('standard', 'Standard'),
            ('membership_invitation', 'Membership Invitation'),
            ('membership_confirmation', 'Membership Confirmation'),
            ('other', 'Other'),
        ], default='standard', required=True, string="Kind",
        help="Allows to classify and filter emails, mainly in the email wizards."
        " * 'Standard': standard emails (from Odoo Community/Enterprise). Do not have any specific role\n"
        " * 'Membership Invitation': emails related to the first validation stage of the membership (to know if the player will become a member or not).\n"
        " * 'Membership Confirmation': emails related to the latest validation stage of the membership: the confirmation.\n"
        " * 'Interclub': emails related to the interclubs (application 'Interclubs' needs to be installed).\n"
        " * 'Other': emails that do not belong to any of the previous value: not standard and not specific to any role.")
