# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import uuid
from datetime import datetime, timedelta

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError


class Membership(models.Model):
    _name = 'membership'
    # _inherits = {
    #     'account.move': 'move_id',
    # }  # TODO move me in a seperated module
    # TODO Pas sûr que l'inherits soit nécessaire...
    # TODO Ne faudrait il pas plutot etre lié à l'aml? (afin qu'un facture puisse etre liée à plusieurs membership...)
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Membership'
    _order = 'period_id asc, member_id asc'

    @api.model
    def _get_token(self):
        return uuid.uuid4().hex

    def _default_period_id(self):
        Period = self.env['period']
        for field_name in ('current', 'upcoming'):
            period = Period.search([(field_name, '=', True),], limit=1)
            if period:
                return period
        return False

    period_category_id = fields.Many2one(
        comodel_name='period.category',
        ondelete='cascade',
        required=True,
        string='Period Category',
        tracking=True,
    )
    member_id = fields.Many2one('res.partner', string='Member',
        ondelete='restrict', required=True, domain=[('is_company', '=', False)])
    member_parent_id = fields.Many2one('res.partner', related='member_id.parent_id')
    member_tag_ids = fields.Many2many('res.partner.category', string='Member Tags', related='member_id.category_id',
        readonly=False)
    member_user_id = fields.Many2one('res.users', compute='_compute_member_user_id',
        domain=[('is_company', '=', False)])
    contact_person_id = fields.Many2one('res.partner', string='Contact Person',
        compute='_compute_contact_person_id', inverse='_inverse_contact_person_id', store=True,
        help='Contact with which all communication will happen. This is usually useful when member is a minor child.')
    company_id = fields.Many2one('res.company', string='Company', required=True,
        default=lambda self: self.env.company)
    user_state = fields.Selection(
        string='User Status',
        related='member_user_id.state',
        readonly=True,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    price_paid = fields.Monetary(
        string='Price Paid',
        currency_field='currency_id',
        tracking=True,
        copy=False,
    )
    price_due = fields.Monetary(
        string='Price Due',
        # compute='_compute_price_due',
        # inverse='_inverse_price_due',
        tracking=True,
        store=True,
    )  # --> move_id.amount_total?

# record.price_remaining = record.price_due - record.price_paid

    price_remaining = fields.Monetary(
        string='Price Remaining',
        currency_field='currency_id',
        compute='_compute_payment',
        store=True,
    )  # --> move_id.amount_residual? ou amount_residual_signed?
    paid = fields.Boolean(
        string='Paid',
        compute='_compute_payment',
        store=True,
    )
    state = fields.Selection(
        [
         ('old_member', 'Old Member'),
         ('unknown', 'Unknown'),
         ('requested', 'Prevalidated'),
         ('member', 'Member'),
         ('rejected', 'Rejected'),
        ],
        required=True,
        default='unknown',
        tracking=True,
        group_expand='_expand_state',
    )
    token = fields.Char('Invitation Token', readonly=True, copy=False)
    token_validity = fields.Datetime('Token Validity', readonly=True)  # , groups='base.group_user')
    token_is_valid = fields.Boolean('Token Is Valid', compute='_compute_token_is_valid', readonly=True)
    invitation_mail_sent = fields.Boolean(
        string='Invitation Mail Sent',
        default=False,
        copy=False,
    )
    color = fields.Integer(
        string='Color Index',
        compute='_compute_color',
        help='Color to be displayed in the kanban view.',
    )
    confirmation_mail_sent = fields.Boolean(
        string='Confirmation Mail Sent',
        default=False,
        copy=False,
    )
    user_response = fields.Selection(
        [
         ('undefined', 'Undefined'),
         ('declined', 'Declined'),
         ('accepted', 'Accepted'),
        ],
        string='User Response',
        readonly=True,
        default='undefined',
        copy=False,
        help="Membership status for user's response.")
    # partner_id = fields.Many2one(
    #     comodel_name='res.partner',
    #     related='user_id.partner_id',
    #     store=False,
    #     readonly=True,
    # )
    category_id = fields.Many2one(
        comodel_name='category',
        related='period_category_id.category_id',
        required=True,
        store=False,
        readonly=False,
        domain="[('period_category_ids.period_id', '=?', period_id)]",
    )

    period_id = fields.Many2one(
        comodel_name='period',
        related='period_category_id.period_id',
        required=False,
        store=True,
        ondelete='cascade',
        readonly=False,
        domain="[('period_category_ids.category_id', '=?', category_id)]",
        default=_default_period_id,
    )

    def name_get(self):
        """ name_get() -> [(id, name), ...]

        Returns a textual representation for the records in ``self``.
        By default this is the value of the ``display_name`` field.

        :return: list of pairs ``(id, text_repr)`` for each records
        :rtype: list(tuple)
        """
        res = []
        for record in self:
            name = '%s (%s)' % (record.period_id.name, record.member_id.name)
            res.append((record.id, name))
        return res

    @api.model
    def create(self, vals):
        self._modify_period_category_vals(vals, at_creation=True)
        res = super(Membership, self).create(vals)
        res._add_follower(vals)
        return res

    def write(self, vals):
        self._modify_period_category_vals(vals)

        if vals.get('state') == 'member':
            vals['token_validity'] = None
            # when becoming a member, the related partner should belong to the company
            self.member_id.club_id = self.company_id.partner_id

        return super(Membership, self).write(vals)

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        default.setdefault('period_category_id', self.period_category_id.id)
        default.setdefault('member_id', self.member_id.id)
        default.setdefault('currency_id', self.currency_id.id)
        default.setdefault('price_due', self.price_due)
        default.setdefault('state', self.state)
        new_membership = super(Membership, self).copy(default)
        return new_membership

    def reset_token(self):
        for membership in self:
            membership.write({
                'token': self._get_token(),
                'token_validity': datetime.now(),
                'user_response': 'undefined',
            })

    def _get_closest_lang(self):
        return self.mapped('member_id')._get_closest_lang()

    def _send_email(self, template_xmlid, composer_title, **composer_ctx):
        template = self.env.ref(template_xmlid)
        composer_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            # need to propagate this context key to the composer record
            open_records_view=self._context.get('see_records_view', False),
            active_model=self._name,  # needed to be propagated to <mail.compose.message>._onchange_template_id method
            active_ids=self.ids,
            default_use_template=bool(template),
            default_template_id=template.id if template else False,
            default_composition_mode='mass_mail',
            force_email=True,
        )
        ctx.update(composer_ctx)

        action = {
            'name': composer_title,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(composer_form.id, 'form')],
            'target': 'new',
            'context': ctx,
        }
        if len(self.mapped('member_id.lang')) <= 1:
            return action
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'warning',
                'title': _("Multiple languages detected!"),
                'message': _("Only '%s' will be used for emails.", self._get_closest_lang()),
                'sticky': False,
                'next': action,
            }
        }

    def send_email_invitation(self):
        memberships = self.filtered(lambda m: m.state in ('unknown', 'old_member'))
        if not memberships:
            raise UserError(_("The membership(s) must have state 'Unknown' or 'Old Member' in order " \
                "to send an invitation email."))
        return memberships._send_email(
            template_xmlid='club.email_template_membership_affiliation_invitation',
            composer_title=_('Compose Email - Membership Invitation'),
            only_invitation_emails=True,
        )

    def send_email_confirmation(self):
        memberships = self.filtered(lambda m: m.state == 'member')
        if not memberships:
            raise UserError(_("The membership(s) must have state 'Member' in order " \
                "to send a confirmation email."))
        return memberships._send_email(
            template_xmlid='club.email_template_membership_affiliation_confirmation',
            composer_title=_('Compose Email - Membership Affiliation Confirmation'),
            only_confirmation_emails=True,
        )

    def send_email_payment_due(self):
        return self._send_email(
            template_xmlid='club.email_template_membership_payment_due',
            composer_title=_('Compose Email - Membership with payment due'),
            only_payment_due_emails=True,
        )

    def validate_membership_payment(self):
        for record in self:
            record.price_paid = record.price_due

    def prevalidate_membership_affiliation(self):
        for record in self:
            record.state = 'requested'

    def validate_membership_affiliation(self):
        for record in self:
            record.state = 'member'

    def reject_membership_affiliation(self):
        for record in self:
            record.state = 'rejected'

    def action_reset_password(self):
        return self.mapped('member_user_id').action_reset_password()

    def do_accept(self):
        """ Marks membership invitation as Accepted. """
        res = self.write({
            'user_response': 'accepted',
            'state': 'requested',
        })
        for membership in self:
            membership.message_post(body=_("%s has accepted the invitation. His status has been changed to prevalidated.") % (membership.member_id.name))
        return res

    def do_decline(self):
        """ Marks membership invitation as Declined. """
        res = self.write({
            'user_response': 'declined',
            'state': 'rejected',
        })
        for membership in self:
            membership.message_post(body=_("%s has declined the invitation. His status has been changed to Rejected.") % (membership.member_id.name))
        return res

    def message_update(self, msg_dict, update_vals=None):
        return super(Membership, self).message_update(msg_dict, update_vals)

    @api.model
    def message_new(self, msg, custom_values=None):
        """ Override to update the document according to the email. """
        vals = dict(custom_values) or {}
        period_id = vals.pop('period_id', None)
        if not period_id:
            return

        # Get period_category
        period_category = self.env['period.category'].search([('period_id.id', '=', period_id), ('default', '=', True),], limit=1,)
        if not period_category:
            period_category = self.env['period.category'].search([('period_id.id', '=', period_id),], order='create_date asc, category_id asc', limit=1,)
        if not vals.setdefault('period_category_id', period_category.id):
            return
        vals.setdefault('price_due', period_category.price_due)

        # Get partner who sent the email (create it if was not existing)
        email = (tools.email_split(msg.get('from')) or tools.email_split(msg.get('email_from')) or [None])[0]
        name = msg.get('from').split('<')[0].strip() or msg.get('email_from').split('<')[0].strip() or None
        if not name and email:
            name = email.split("@")[0]
        if not email or not name:
            return

        if msg.get('author_id'):
            sender = self.env['res.partner'].browse(msg.get('author_id'))
        else:
            sender = self.env['res.partner'].search([('email', '=', email),])

        # TODO call <res.users>._signup_create_user(self, values) to create a  user (same rights than portal user)
        if not sender:
            sender = self.env['res.partner'].create({
                'name': name,
                'email': email,
            })

        if not vals.setdefault('member_id', sender.id):
            return

        # If a membership already exists: no need to create a new one
        membership = self.env['membership'].search([
            ('period_id.id', '=', period_id),
            ('member_id.id', '=', sender.id),
        ], limit=1)
        if not membership:
            membership = self.env['membership'].search([
                ('period_id.id', '=', period_id),
                ('contact_person_id.id', '=', sender.id),
            ], limit=1)

        vals.setdefault('state', 'unknown')
        if membership:
            # vals.setdefault('price_paid', membership.price_paid)
            return membership
        else:
            vals.setdefault('price_paid', 0)
            return super(Membership, self).message_new(msg, custom_values=vals)

    def action_view_members(self):
        action = {
            'name': _('Members'),
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
        }

        if len(self) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': self.member_id.id,
            })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', self.member_id.ids)],
            })

        return action

    def _modify_period_category_vals(self, vals, at_creation=False):
        """ Modifies the dictionary `vals` regarding its values related to "period", "category" and "period category".
        DISCLAIMER: This method modifies the object (dictionary) passed as the argument `vals`!
        If you do not want the dictionary passed as argument to be altered, copy it before calling!

        Note: This method raise a `ValidationError` if both period and category are not consistent together (both should be in a `period.category` existing record).

        :return: None
        """
        if 'period_category_id' in vals or 'period_id' in vals or 'category_id' in vals:
            if vals.get('period_category_id'):
                period_category = self.env['period.category'].browse(vals['period_category_id'])
            else:
                period_category = self.env['period.category'].search([
                    ('period_id.id', '=', vals.get('period_id', self.period_id.id)),
                    ('category_id.id', '=', vals.get('category_id', self.category_id.id)),
                ], limit=1)
            if not period_category:
                raise ValidationError(_('Fields "Period" and "Category" cannot be set together with such values.'))
            vals['period_category_id'] = period_category.id
            # Need to add `period_id` key to avoid `_default_period_id` method to be called at record creation.
            # No need to do it for `category_id` as no method has been set for `default` attribute.
            vals['period_id'] = period_category.period_id.id

        # Avoid to modify the period_category_id record w/ period and category fields. However, at record's creation,
        # we should preserve `period_id` to avoid to call method linked to `default` attribute (`_default_period_id`).
        if not at_creation:
            vals.pop('period_id', None)
            vals.pop('category_id', None)

    @api.onchange('period_id', 'category_id')
    def _onchange_period_or_category(self):
        PeriodCategory = self.env['period.category']
        for rec in self:
            period_cat = PeriodCategory.search([
                ('period_id', '=', rec.period_id.id),
                ('category_id', '=', rec.category_id.id),
            ], limit=1)
            if period_cat:
                rec.price_due = period_cat.price_due
        return {
            'warning': {'title': _("Message"), 'message': _("Price Due has changed"), 'type': 'notification'},
        }

    @api.onchange('token')
    def _onchange_token(self):
        for record in self:
            if record.token and record.env['membership'].search_count([('token', '=', record.token),]) > 1:
                record.token = self._get_token()

    def _add_follower(self, vals):
        ids = self.contact_person_id.ids or self.member_id.ids
        # Let's wait what we decide to do...
        # ids.extend(self.env['res.users'].search([('secretary', '=', True),]).mapped('partner_id').ids)
        self.message_subscribe(partner_ids=ids)

    @api.depends('member_id')
    def _compute_member_user_id(self):
        ResUsers = self.env['res.users']
        for record in self:
            record.member_user_id = ResUsers.search([('partner_id', '=', record.member_id.id)],
                limit=1)

    @api.depends('member_id')
    def _compute_contact_person_id(self):
        for record in self:
            record.contact_person_id = record.member_id.responsible_id
    def _inverse_contact_person_id(self):
        pass

    @api.depends('price_paid', 'price_due')
    def _compute_payment(self):
        for record in self:
            if record.price_due <= record.price_paid or record.price_due == 0:
                record.price_remaining = 0
                record.paid = True
            else:
                record.price_remaining = record.price_due - record.price_paid
                record.paid = False

    @api.depends('paid', 'state')
    def _compute_color(self):
        """ Computes color value based on the price paid (used in the Kanban view.)

        :return: None
        """
        for record in self:
            if record.state in ('requested', 'member'):
                record.color = 10 if record.paid else 9
            else:
                record.color = 12

    @api.depends('token_validity')
    def _compute_token_is_valid(self):
        for record in self:
            # TODO 30 should be in club parameters
            record.token_is_valid = record.token_validity and datetime.now() <= fields.Datetime.from_string(record.token_validity) + timedelta(days=30)

    # @api.depends('period_category_id')
    # def _compute_price_due(self):
    #     print('\n_compute_price_due')
    #     for record in self:
    #         record.price_due = record.period_category_id.price_due if record.period_category_id else 0

    # def _inverse_price_due(self):
    #     """ empty inverse method in order to have `price_due` field editable
    #     and not overrriden if a period_category is set after a manual
    #     modification of the price """
    #     pass

    @api.constrains('member_id', 'period_id')
    def _check_user_period(self):
        """ Checks that the member has only one membership per period (otherwise, an exception is raised).

        :return: None
        """
        Membership = self.env['membership']
        for membership in self:
            if Membership.search_count([('member_id.id', '=', membership.member_id.id),
                                        ('period_id.id', '=', membership.period_id.id),]) > 1:
                raise ValidationError(_("The user '%s' has already a membership for this period (%s). Please change accordingly.") % (membership.member_id.name, membership.period_id.name))

    @api.constrains('price_paid', 'price_due')
    def _check_price(self):
        """ Checks that the prices (paid and due) are positive.

        :return: None
        """
        for membership in self:
            if membership.price_paid < 0 or membership.price_due < 0:
                raise ValidationError(_("Prices should be positive."))

    def _expand_state(self, states, domain, order):
        return [key for key, val in type(self).state.selection]

    @api.model
    def _read_group_fill_results(self, domain, groupby, remaining_groupbys,
                                 aggregated_fields, count_field,
                                 read_group_result, read_group_order=None):
        res = super()._read_group_fill_results(domain, groupby, remaining_groupbys, aggregated_fields, count_field,
            read_group_result, read_group_order)

        if self._name != 'membership':
            # did not check this `if` statement: it could be not necessary
            return res
        for d in res:
            d['__fold'] = True if d.get('state') in ('old_member', 'rejected') else False
        return res
