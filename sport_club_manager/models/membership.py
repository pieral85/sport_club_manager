# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import uuid

from odoo import api, fields, models, exceptions, tools, _


class Membership(models.Model):
    _name = 'membership'
    _inherit = 'mail.thread'
    _description = 'Membership'
    _order = "period_id asc, member_id asc"

    @api.returns('self')
    def _default_price_due(self):
        return self.period_category_id.price_due

    @api.model
    def _default_token(self):
        return uuid.uuid4().hex

    period_category_id = fields.Many2one(
        comodel_name='period_category',
        ondelete='cascade',
        required=True,
        string='Period Category',
    )
    member_id = fields.Many2one('res.partner', string='Member',
        ondelete='restrict', required=True, domain=[('is_company', '=', False)])
    member_user_id = fields.Many2many('res.users', compute='_compute_member_user_id',
        domain=[('is_company', '=', False)])
    contact_person_id = fields.Many2one('res.partner', string='Contact Person',
        help='Contact with which all communication will happen. This is usually useful when member is a minor child.')
    user_state = fields.Selection(
        string='User Status',
        related='member_user_id.state',
        readonly=True,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env['res.company']._company_default_get(),
    )
    price_paid = fields.Monetary(
        string='Price Paid',
        currency_field='currency_id',
        track_visibility='always',
        copy=False,
    )
    price_due = fields.Monetary(
        string='Price Due',
        default=_default_price_due,
        track_visibility='always',
        store=True,
    )
    price_paid_percentage = fields.Float(
        string='Percentage Paid',
        compute='_compute_payment',
    )
    price_remaining = fields.Monetary(
        string='Price Remaining',
        currency_field='currency_id',
        compute='_compute_payment',
        store=True,
    )
    state = fields.Selection(
        [
         ('unknown', 'Unknown'),
         ('old_member', 'Old Member'),
         ('requested', 'Requested'),
         ('member', 'Member'),
         ('rejected', 'Rejected'),
        ],
        required=True,
        default='unknown',
        track_visibility='always',
        group_expand='_expand_state',
    )
    paid = fields.Boolean(
        string='Paid',
        compute='_compute_payment',
        store=True,
    )
    token = fields.Char(
        string='Invitation Token',
        default=_default_token,
        copy=False,
    )
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
        store=False,
        # readonly=True,
    )
    period_id = fields.Many2one(
        comodel_name='period',
        related='period_category_id.period_id',
        store=True,
        ondelete='cascade',
        # FIXME commented because causing a bug when trying to crete new membership (try to affiliate Administrator user as competitior for season 2017-18!!!) default=lambda self: self.env['period'].search([('current','=',True),], limit=1)
    )

    @api.multi
    @api.depends('period_id', 'member_id')
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
        vals.setdefault('period_category_id', self.env['period_category'].search([
            ('period_id.current', '=', True),
            ('default', '=', True),
            ]
        ).id)  # TODO Tester quand il n'existe pas de periode courante
        vals.setdefault('state', 'unknown')
        res = super(Membership, self).create(vals)
        # res._add_follower(vals)
        return res

    @api.multi
    def send_email_invitation(self):
        template = self.env.ref('sport_club_manager.email_template_membership_affiliation_invitation')
        memberships = self.filtered(lambda m: m.state not in ('requested', 'member', 'rejected'))
        if memberships:
            compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
            ctx = dict(
                dbname=self._cr.dbname,
                only_invitation_emails=True,
                default_model='membership',
                active_ids=memberships.ids,
                default_use_template=bool(template),
                default_template_id=template and template.id or False,
                default_composition_mode='mass_mail',
                force_email=True,
            )
            return {
                'name': _('Compose Email - Membership Invitation'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(compose_form.id, 'form')],
                'target': 'new',
                'context': ctx,
            }

    @api.multi
    def action_reset_password(self):
        import ipdb; ipdb.set_trace()
        return self.mapped('member_user_id').action_reset_password()

    @api.multi
    def do_accept(self):
        """ Marks membership invitation as Accepted. """
        res = self.write({
            'user_response': 'accepted',
            'state': 'requested',
        })
        for membership in self:
            membership.message_post(body="%s has accepted the invitation. His status has been changed to Requested." % (membership.member_id.name))
        return res

    @api.multi
    def do_decline(self):
        """ Marks membership invitation as Declined. """
        res = self.write({
            'user_response': 'declined',
            'state': 'rejected',
        })
        for membership in self:
            membership.message_post(body="%s has declined the invitation. His status has been changed to Rejected." % (membership.member_id.name))
        return res

    @api.multi
    def message_update(self, msg_dict, update_vals=None):
        return super(Membership, self).message_update(msg_dict, update_vals)

    @api.model
    def message_new(self, msg, custom_values=None):
        """ Override to updates the document according to the email. """
        vals = dict(custom_values) or {}
        period_id = vals.pop('period_id', None)
        if not period_id:
            return

        # Get period_category
        period_category = self.env['period_category'].search([('period_id.id', '=', period_id), ('default', '=', True),], limit=1,)
        if not period_category:
            period_category = self.env['period_category'].search([('period_id.id', '=', period_id),], order='create_date asc, category_id asc', limit=1,)
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

    @api.onchange('token')
    def _onchange_token(self):
        # import ipdb; ipdb.set_trace()
        for record in self:
            if record.env['membreship'].search_count([('token', '=', record.token),]) > 1:
                record.token = _default_token()

    # Let's wait what we decide to do...
    # def _add_follower(self, vals):
    #     ids = self.contact_person_id.ids if self.contact_person_id else self.member_id.ids
    #     ids.extend(self.env['res.users'].search([('secretary', '=', True),]).mapped('partner_id').ids)
    #     self.message_subscribe(partner_ids=ids)

    @api.depends('member_id')
    def _compute_member_user_id(self):
        ResUsers = self.env['res.users']
        for record in self:
            record.member_user_id = ResUsers.search([('partner_id', '=', record.member_id.id)],
                limit=1)

    @api.depends('price_paid', 'price_due')
    def _compute_payment(self):
        for record in self:
            if record.price_due <= record.price_paid or record.price_due == 0:
                record.price_paid_percentage = 100
                record.price_remaining = 0
                record.paid = True
            else:
                record.price_paid_percentage = 100.0 * record.price_paid / record.price_due
                record.price_remaining = record.price_paid - record.price_due
                record.paid = False

    def _compute_color(self):
        """ Computes color value based on the price paid (used in the Kanban view.)

        :return: None
        """
        for record in self:
            if record.state == 'member':
                record.color = 10 if record.price_paid_percentage == 100 else 9
            else:
                record.color = 12

    @api.onchange('period_category_id')
    def _calculate_price_due(self):
        for record in self:
            record.price_due = record.period_category_id.price_due if record.period_category_id else 0

    @api.onchange('category_id')
    def _onchange_category_id(self):
        for record in self:
            if record.category_id and record.period_id:
                period_category_id = self.env['period_category'].search([
                    ('period_id.id','=',record.period_id.id),
                    ('category_id.id','=',record.category_id.id),
                    ],
                    limit=1,)
                backup_category_id = record.category_id
                record.period_id = None
                record.period_category_id = period_category_id
                record.category_id = backup_category_id

    @api.onchange('period_id')
    def _onchange_period_id(self):
        for record in self:
            if record.period_id and record.category_id:
                period_category_id = self.env['period_category'].search([
                    ('period_id.id','=',record.period_id.id),
                    ('category_id.id','=',record.category_id.id),
                    ],
                    limit=1,)
                backup_period_id = record.period_id
                record.category_id = None
                record.period_category_id = period_category_id
                record.period_id = backup_period_id

    @api.one
    @api.constrains('member_id', 'period_id')
    def _check_user_period(self):
        """ Checks that the member has only one membership per period (otherwise, an exception is raised).

        :return: None
        """
        if self.env['membership'].search_count([('member_id.id', '=', self.member_id.id), ('period_id.id','=',self.period_id.id),]) > 1:
            raise exceptions.ValidationError(_("The user '%s' has already a membership for this period (%s). Please change accordingly.") % (self.member_id.name, self.period_id.name))

    @api.multi
    def validate_membership_payment(self):
        for record in self:
            record.price_paid = record.price_due

    @api.multi
    def validate_membership_affiliation(self):
        for record in self:
            record.state = 'member'

    @api.multi
    def reject_membership_affiliation(self):
        for record in self:
            record.state = 'rejected'

    @api.multi
    def send_email_confirmation(self):
        template = self.env.ref('sport_club_manager.email_template_membership_affiliation_confirmation')
        memberships = self.filtered(lambda m: m.state == 'member')
        if memberships:
            compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
            ctx = dict(
                only_confirmation_emails=True,
                default_model='membership',
                active_ids=memberships.ids,
                default_use_template=bool(template),
                default_template_id=template and template.id or False,
                default_composition_mode='mass_mail',
                force_email=True,
            )
            return {
                'name': _('Compose Email - Membership Affiliation Confirmation'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(compose_form.id, 'form')],
                'target': 'new',
                'context': ctx,
            }

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

    def _expand_state(self, states, domain, order):
        return [key for key, val in type(self).state.selection]
