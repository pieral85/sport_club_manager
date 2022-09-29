# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import uuid

from odoo import api, fields, models, tools, _
from odoo.addons.mail.wizard.mail_compose_message import _reopen


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.model
    def _default_season_id(self):
        if self._context.get('for_new_season_mail'):
            return self.env['period'].search([('current', '=', True)], limit=1) or \
                    self.env['period'].search([('upcoming', '=', True)], limit=1)
        return False

    template_id = fields.Many2one('mail.template', domain="[('id', 'in', allowed_template_ids)]")
    allowed_template_ids = fields.One2many('mail.template', compute='_compute_allowed_template_ids')
    season_id = fields.Many2one('period', string='Season', default=_default_season_id)

    @api.onchange('season_id')
    def _onchange_season_id(self):
        if not self._context.get('for_new_season_mail'):
            return
        if self.season_id:
            if self.season_id.alias_name:
                email = '%s@%s' % (self.season_id.alias_name, self.season_id.alias_domain)
                self.reply_to = tools.formataddr((_('New Season') or u"False", email or u"False"))
            if not self.template_id:
                # should fetch 'club.email_template_new_season' record if no other template has been created afterwards
                tmpl = self.env['mail.template'].search([('kind', '=', 'new_season')], order='id desc', limit=1)
                self.template_id = tmpl
        else:
            self.reply_to = ''
            self.template_id = False

    @api.depends('model')
    def _compute_allowed_template_ids(self):
        MailTemplate = self.env['mail.template']
        kinds = []
        if self.env.context.get('only_invitation_emails'):
            kinds.append('membership_invitation')
        if self.env.context.get('only_confirmation_emails'):
            kinds.append('membership_confirmation')
        if self.env.context.get('for_new_season_mail'):
            kinds.append('new_season')
        base_domain = [('kind', 'in', kinds if kinds else ['standard'])]

        for rec in self:
            allowed_templates = MailTemplate.search_read([('model', '=', rec.model)] + base_domain, ['id'])
            if allowed_templates:
                rec.allowed_template_ids = [mtpl['id'] for mtpl in allowed_templates]
            else:
                rec.allowed_template_ids = False

    def _onchange_template_id(self, template_id, composition_mode, model, res_id):
        """ force default lang of subject/body mail composer """
        # changing the lang of the context allows to use the correct lang for the mail template itself
        if 'active_model' in self._context and 'active_ids' in self._context:
            _model, _ids = self._context['active_model'], self._context['active_ids']
            closest_lang = self.env[_model].browse(_ids)._get_closest_lang()
            self = self.with_context(lang=closest_lang)
        return super(MailComposer, self)._onchange_template_id(template_id, composition_mode, model, res_id)

    def _action_send_mail(self, auto_commit=False):
        if self.model == 'res.partner':
            self = self.with_context(mailing_document_based=True)
        if self.env.context.get('for_new_season_mail'):
            self = self.with_context(season_id=self.season_id)
        return super(MailComposer, self)._action_send_mail(auto_commit=auto_commit)

    def action_send_mail(self):
        self.ensure_one()
        if 'active_model' not in self._context or 'active_ids' not in self._context:
            return super(MailComposer, self).action_send_mail()
        model, ids = self._context['active_model'], self._context['active_ids']
        records = self.env[model].browse(ids)

        if model == 'membership':
            records.reset_token()

        if self.composition_mode == 'mass_mail':
            # allows to translate variables in the mail template
            self = self.with_context(lang=records._get_closest_lang())
        res = super(MailComposer, self).action_send_mail()

        if model == 'membership':
            vals = {}
            if self.template_id.kind == 'membership_invitation':
                vals['invitation_mail_sent'] = True
            if self.template_id.kind == 'membership_confirmation':
                vals['confirmation_mail_sent'] = True
            records.write(vals)

        if self.env.context.get('open_records_view') and 'active_domain' in self._context:
            action = {
                'name': _('Records with Mail Sent'),
                'type': 'ir.actions.act_window',
                'res_model': model,
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
            ('new_season', 'New Season'),
            ('other', 'Other'),
        ], default='standard', required=True, string="Kind",
        help="Allows to classify and filter emails, mainly in the email wizards."
        " * 'Standard': standard emails (from Odoo Community/Enterprise). Do not have any specific role.\n"
        " * 'Membership Invitation': emails related to the first validation stage of the membership (to know if the player will become a member or not).\n"
        " * 'Membership Confirmation': emails related to the latest validation stage of the membership: the confirmation.\n"
        " * 'New Season': emails sent at the beginning of a new season, from a contact view.\n"
        " * 'Interclub': emails related to the interclubs (application 'Interclubs' needs to be installed).\n"
        " * 'Other': emails that do not belong to any of the previous value: not standard and not specific to any role.")

    def _get_sent_mail_message(self, contacts):
        self.ensure_one()
        def record_link(rec):
            s = "<a href=# data-oe-model={r_model} data-oe-id={r_id}>{r_name}</a>"
            return s.format(r_model=rec._name, r_id=rec.id, r_name=rec.name)

        contacts_link = ''.join("<li>{}</li>".format(record_link(c)) for c in contacts)
        mail_link = record_link(self)
        return _("Email <i>%(template)s</i> has been sent to the following contacts:<ul>%(contacts)s</ul>",
            template=mail_link, contacts=contacts_link)
