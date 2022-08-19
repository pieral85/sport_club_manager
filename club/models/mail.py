# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import uuid

from odoo import api, fields, models, _
from odoo.addons.mail.wizard.mail_compose_message import _reopen


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    template_id = fields.Many2one('mail.template', domain="[('id', 'in', allowed_template_ids)]")
    allowed_template_ids = fields.One2many('mail.template', compute='_compute_allowed_template_ids')

    @api.depends('model')
    def _compute_allowed_template_ids(self):
        MailTemplate = self.env['mail.template']
        kinds = []
        if self.env.context.get('only_invitation_emails'):
            kinds.append('membership_invitation')
        if self.env.context.get('only_confirmation_emails'):
            kinds.append('membership_confirmation')
        base_domain = [('kind', 'in', kinds if kinds else ['standard'])]

        for rec in self:
            allowed_templates = MailTemplate.search_read([('model', '=', rec.model)] + base_domain, ['id'])
            if allowed_templates:
                rec.allowed_template_ids = [mtpl['id'] for mtpl in allowed_templates]
            else:
                rec.allowed_template_ids = False

    def _onchange_template_id(self, template_id, composition_mode, model, res_id):
        # force default lang of subject/body mail composer
        lang = self._context.get('forced_lang', 'en_US')
        if lang:
            self = self.with_context(lang=lang)
        return super(MailComposer, self)._onchange_template_id(template_id, composition_mode, model, res_id)

    def _action_send_mail(self, auto_commit=False):
        if self.model == 'res.partner':
            self = self.with_context(mailing_document_based=True)
        return super(MailComposer, self)._action_send_mail(auto_commit=auto_commit)

    def action_send_mail(self):
        self.ensure_one()
        model = self.env.context.get('default_model')

        if model == 'membership':
            self.env[model].browse(self.env.context['active_ids']).reset_token()

        res = super(MailComposer, self).action_send_mail()

        if model == 'membership' and self.env.context.get('active_ids'):
            vals = {}
            if self.template_id.kind == 'membership_invitation':
                vals['invitation_mail_sent'] = True
            if self.template_id.kind == 'membership_confirmation':
                vals['confirmation_mail_sent'] = True
            self.env['membership'].browse(self.env.context['active_ids']).write(vals)

        if self.env.context.get('open_records_view'):
            ids = self.env.context['active_ids']
            action = {
                'name': _('Memberships with Mail Sent'),
                'type': 'ir.actions.act_window',
                'res_model': 'membership',
            }
            if len(ids) == 1:
                action.update({
                    'view_mode': 'form',
                    'res_id': ids[0],
                })
            else:
                action.update({
                    'view_mode': 'tree,form',
                    'domain': [('id', 'in', ids)],
                })
            return action
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
        " * 'Standard': standard emails (from Odoo Community/Enterprise). Do not have any specific role.\n"
        " * 'Membership Invitation': emails related to the first validation stage of the membership (to know if the player will become a member or not).\n"
        " * 'Membership Confirmation': emails related to the latest validation stage of the membership: the confirmation.\n"
        " * 'Interclub': emails related to the interclubs (application 'Interclubs' needs to be installed).\n"
        " * 'Other': emails that do not belong to any of the previous value: not standard and not specific to any role.")
