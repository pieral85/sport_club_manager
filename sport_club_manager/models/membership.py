# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import uuid

from odoo import api, fields, models, exceptions, tools


class Membership(models.Model):
    _name = 'membership'
    _inherit = 'mail.thread'
    _description = 'Membership'
    _order = "period_id asc, user_id asc"

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
    user_id = fields.Many2one(
        comodel_name='res.users',
        ondelete='cascade',
        required=True,
        string='User',
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
        copy=False,
    )
    price_due = fields.Monetary(
        string='Price Due',
        default=_default_price_due,
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
    mail_sent = fields.Boolean(
        string='Mail Sent',
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
        help="Membership status of the user's response.")
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        related='user_id.partner_id',
        store=False,
        readonly=True,
    )
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
    @api.depends('period_id', 'user_id')
    def name_get(self):
        """ name_get() -> [(id, name), ...]

        Returns a textual representation for the records in ``self``.
        By default this is the value of the ``display_name`` field.

        :return: list of pairs ``(id, text_repr)`` for each records
        :rtype: list(tuple)
        """
        res = []
        for record in self:
            name = '%s (%s)' % (record.period_id.name, record.user_id.name)
            res.append((record.id, name))
        return res

    @api.model
    def create(self, vals):
        vals.setdefault('user_id', self.env.uid)
        vals.setdefault('period_category_id', self.env['period_category'].search([
            ('period_id.current', '=', True),
            ('default', '=', True),
            ]
        ))
        vals.setdefault('state', 'requested')
        res = super(Membership, self).create(vals)
        res._add_follower(vals)
        return res

    def send_email_invitation(self):
        invitation_template = self.env.ref('sport_club_manager.email_template_membership_affiliation_request')
        ctx = {
            'company_id': self.env.user.company_id,
            'dbname': self._cr.dbname,
        }
        invitation_template.with_context(ctx).send_mail(self.id)
        self.invitation_mail_sent = True
        return True

    @api.multi
    def do_accept(self):
        """ Marks membership invitation as Accepted. """
        res = self.write({
            'user_response': 'accepted',
            'state': 'requested',
        })
        for membership in self:
            membership.message_post(body="%s has accepted the invitation. His status has been changed to Requested." % (membership.partner_id.name))
        return res

    @api.multi
    def do_decline(self):
        """ Marks membership invitation as Declined. """
        res = self.write({
            'user_response': 'declined',
            'state': 'rejected',
        })
        for membership in self:
            membership.message_post(body="%s has declined the invitation. His status has been changed to Rejected." % (membership.partner_id.name))
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

        # Get user who sent the email (create it if was not existing)
        email = (tools.email_split(msg.get('from')) or tools.email_split(msg.get('email_from')) or [None])[0]
        if not email:
            return
        if msg.get('author_id'):
            partner = self.env['res.partner'].browse(msg.get('author_id'))
        else:
            partner = self.env['res.partner'].search([('email', '=', email),])
        user_id = self.env['res.users'].search([('login', '=', email),]).id

        if not user_id:
            if partner:
                user_id = self.env['res.users'].create({
                    'name': partner.name,
                    'login': partner.email,
                    }).id
            else:
                user_id = self.env['res.users'].create({
                    'name': 'Unknown User',
                    'login': email,
                    }).id
        if not vals.setdefault('user_id', user_id):
            return

        # If a membership already exists: no need to create a new one
        membership = self.env['membership'].search([
            ('period_id.id', '=', period_id),
            ('user_id.id', '=', user_id),
            ],
        )
        vals.setdefault('state', 'requested')
        if membership:
            vals.setdefault('price_paid', membership.price_paid)
            return membership.message_update(msg, update_vals=vals)
        else:
            vals.setdefault('price_paid', 0)
            return super(Membership, self).message_new(msg, custom_values=vals)

    @api.onchange('token')
    def _onchange_token(self):
        import ipdb; ipdb.set_trace()
        for record in self:
            if record.env['membreship'].search_count([('token', '=', record.token),]) > 1:
                record.token = _default_token()

    def _add_follower(self, vals):
        ids = self.user_id.partner_id.ids
        ids.extend(self.env['res.users'].search([('secretary', '=', True),]).mapped('partner_id').ids)
        self.message_subscribe(partner_ids=ids)

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
    @api.constrains('user_id', 'period_id')
    def _check_user_period(self):
        """ Checks that the user has only one membership per period (otherwise, an exception is raised).

        :return: None
        """
        if self.env['membership'].search_count([('user_id.id', '=', self.user_id.id), ('period_id.id','=',self.period_id.id),]) > 1:
            raise exceptions.ValidationError("The user '%s' has already a membership for this period (%s). Please change accordingly." % (self.user_id.name, self.period_id.name))

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
    def send_email(self):
        for record in self:
            record.mail_sent = True
            template = self.env.ref('sport_club_manager.email_template_membership_affiliation_confirmation')
            ctx = {
                'company_id': self.env.user.company_id,
            }
            self.with_context(ctx).message_post_with_template(template.id)

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        default.setdefault('period_category_id', self.period_category_id.id)
        default.setdefault('user_id', self.user_id.id)
        default.setdefault('currency_id', self.currency_id.id)
        default.setdefault('price_due', self.price_due)
        default.setdefault('state', self.state)
        new_membership = super(Membership, self).copy(default)
        return new_membership

    def _expand_state(self, states, domain, order):
        return [key for key, val in type(self).state.selection]
