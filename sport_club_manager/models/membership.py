# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, exceptions, tools


class Membership(models.Model):
    _name = 'membership'
    _inherit = 'mail.thread'
    _description = 'Membership' # TODO
    _order = "period_id asc, user_id asc"
    # TODO Investigate with @xal
    # _sql_constraints = [
    #     ('user_period_uniq', 'UNIQUE(user_id, period_category_id.period_id)', 'This user has already been set for this period!'),
    # ]

    # @api.model
    @api.returns('self')
    def _default_price_due(self):
        # print('\n_default_price_due', self, self.period_category_id, self.period_category_id.price_due)
        return self.period_category_id.price_due

    period_category_id = fields.Many2one(
        comodel_name='period_category',
        # inverse_name='membership_ids',
        string='Period Category',
        required=True,
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        # inverse_name='membership_ids',
        string='Member',  # TODO Should it be a member (<> user)?
        required=True,
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
    )
    price_due = fields.Monetary(
        string='Price Due',
        default=_default_price_due,
        store=True,
    )
    price_paid_percentage = fields.Float(
        string='Percentage Paid',
        compute='_compute_payment',  # '_compute_price_paid_percentage',
    )
    price_remaining = fields.Monetary(
        string='Price Remaining',
        currency_field='currency_id',
        compute='_compute_payment',
        store=True,
    )
    # member = fields.Boolean(
    #     string='Is a Member',
    # )
    # old_member = fields.Boolean(
        # string='Is an Old Member',
        # compute='_compute_old_member',
    # )
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
    color = fields.Integer(
        string='Color Index',
        compute='_compute_color',
        help='Color to be displayed in the kanban view.',
    )
    mail_sent = fields.Boolean(
        string='Mail Sent',
        default=False,
    )
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
        # readonly=True,
        # commented because causing a bug when trying to crete new membership (try to affiliate Administrator user as competitior for season 2017-18!!!) default=lambda self: self.env['period'].search([('current','=',True),], limit=1)
    )
    # subscription_requested = fields.Boolean(
    #     string='Subscription Requested',
    # )
#    member_ids = fields.Many2many(
#        comodel_name='res.users',
#        # domain=[('is_company', '=', False)],
#        string='Members',
#    )

    # @api.multi
    # def write(self, vals):
    #     res = super(Membership, self).write(vals)
    #     self._add_follower(vals)
    #     return res

    @api.multi
    @api.depends('period_id', 'user_id')
    def name_get(self):
        res = []
        for record in self:
            name = '%s (%s)' % (record.period_id.name, record.user_id.name)
            res.append((record.id, name))
        return res

    @api.model
    def create(self, vals):
        # import ipdb; ipdb.set_trace()
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

    @api.multi
    def message_update(self, msg_dict, update_vals=None):
        import ipdb; ipdb.set_trace()
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
        import ipdb; ipdb.set_trace()
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
                    # 'new_password': 'tuc'
                    }).id
            else:
                user_id = self.env['res.users'].create({
                    'name': 'Unknown User',
                    'login': email,
                    # 'new_password': 'tuc'
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

    def _add_follower(self, vals):
        # if vals.get('responsible_id'):
            # responsible = self.env['res.users'].browse(vals.get('responsible_id'))
            # self.message_subscribe(partner_ids=responsible.partner_id.ids)
        ids = self.user_id.partner_id.ids
        ids.extend(self.env['res.users'].search([('secretary', '=', True),]).mapped('partner_id').ids)
        self.message_subscribe(partner_ids=ids)

    @api.depends('price_paid', 'price_due')
    def _compute_payment(self):
        # TOTEST When price_paid or price_due has changed, we should go in this function only once 
        for record in self:
            if record.price_due <= record.price_paid or record.price_due == 0:
                record.price_paid_percentage = 100
                record.price_remaining = 0
                record.paid = True
            else:
                record.price_paid_percentage = 100.0 * record.price_paid / record.price_due
                record.price_remaining = record.price_paid - record.price_due
                record.paid = False
            record._compute_state()

    # #After state has been changed
    # @api.onchange('state')
    # def _onchange_state(self):
    #     if record.state == 'member':
    #         if record.price_paid < record.price_due:
    #             record.price_paid = record.price_due  # Cette ligne devrait se retrouver dans la kanban view qand on drag and drop le user sur colonne Member


    # TODO define an api.depends (ne doit etre calcule que quand il y a une nouvelle periode (via le CRON?))
    def _compute_state(self):
    # def _compute_old_member(self):
        # import ipdb; ipdb.set_trace()
        for record in self:
            if record.state not in ('member', 'requested'):
                previous_period = record.period_category_id.period_id.previous_period
                temp = self.env['membership'].search(
                    [
                     ('period_category_id.period_id', '=', previous_period.id),
                     ('user_id', '=', record.user_id.id),
                     #('user_id.active', '=', True),  # TODO Ceux qui ont été désactivés l'année précédente ne devraient plus apparaître (cette ligne est peut etre superflue alors (TOTEST))
                    ]
                )
                # TODO Remove temp and return directly the result (but check first if it is ok if None is returned)
                toto = self.env['membership'].search_count(
                    [
                     ('period_category_id.period_id', '=', previous_period.id),
                     ('user_id', '=', record.user_id.id),
                     #('user_id.active', '=', True),  # TODO Ceux qui ont été désactivés l'année précédente ne devraient plus apparaître (cette ligne est peut etre superflue alors (TOTEST))
                    ]
                )
                if toto:
                    record.state = 'old_member'
                else:
                    record.state = 'unknown'

    def _compute_color(self):
        # 1?,9!rouge   10?vert
        for record in self:
            if record.state == 'member':
                record.color = 10 if record.price_paid_percentage == 100 else 9
            else:
                record.color = 12

    # @api.multi
    @api.onchange('period_category_id')
    def _calculate_price_due(self):
        print('\n_calculate_price_due', self, self.period_category_id, self.period_category_id.price_due)
        for record in self:
            # if record.period_category_id:
            record.price_due = record.period_category_id.price_due if record.period_category_id else 0

    @api.onchange('category_id')
    def _onchange_category_id(self):
        print('\n_onchange_category_id', self, self.category_id)
        # import ipdb; ipdb.set_trace()
        for record in self:
            # import ipdb; ipdb.set_trace()
            # record.period_category_id = None
            if record.category_id and record.period_id:
                # period_category_ids = self.env['period_category'].search_read([('category_id.id','=',record.category_id.id),], ['period_id'])
                # import pprint; pprint.pprint(period_category_ids)
                # period_ids = [d['id'] for d in period_category_ids]
                # print(record.period_id, period_ids)
                # if record.period_id.id not in period_ids:
                #     record.period_id = None
                period_category_id = self.env['period_category'].search([
                    ('period_id.id','=',record.period_id.id),
                    ('category_id.id','=',record.category_id.id),
                    ],
                    limit=1,)
                backup_category_id = record.category_id
                record.period_id = None
                record.period_category_id = period_category_id
                record.category_id = backup_category_id
                # if not period_category_id:
                #     record.period_id = None
                # else:
                #     print('\nBefore changing category, period_category_id was', record.period_category_id)
                #     record.period_category_id = period_category_id
                #     print('\nAfter changing category, period_category_id is', record.period_category_id)

    # TODO To be tested when changing a period_id
    @api.onchange('period_id')
    def _onchange_period_id(self):
        print('\n_onchange_period_id', self, self.period_id)
        for record in self:
            # period_category_ids = self.env['period_category'].search_read([('period_id.id','=',record.period_id.id),], ['category_id'])
            # import ipdb; ipdb.set_trace()
            # record.period_category_id = None
            if record.period_id and record.category_id:
                # period_category_ids = self.env['period_category'].search([('period_id.id','=',record.period_id.id),]).ids
                # period_category_ids = self.env['period_category'].search_read([('period_id.id','=',record.period_id.id),], ['category_id'])
                
                # p_c_ids = [d['id'] for d in period_category_ids]
                # category_ids = [d.get('category_id',['---'])[0] for d in period_category_ids]
                # import pprint; pprint.pprint(period_category_ids)
                # print(record.category_id, category_ids)
                # if record.category_id.id not in period_category_ids:
                # if record.category_id.id not in category_ids:
                #     record.category_id = None
                # else:
                #     record.period_category_id = self.env['period_category'].search([('period_id.id','=',record.period_id.id),('category_id.id','=',record.category_id.id),], limit=1)
                period_category_id = self.env['period_category'].search([
                    ('period_id.id','=',record.period_id.id),
                    ('category_id.id','=',record.category_id.id),
                    ],
                    limit=1,)
                backup_period_id = record.period_id
                record.category_id = None
                record.period_category_id = period_category_id
                record.period_id = backup_period_id
                # if not period_category_id:
                #     record.category_id = None
                # else:
                #     print('\nBefore changing period, period_category_id was', record.period_category_id)
                #     record.period_category_id = period_category_id
                #     print('\nAfter changing period, period_category_id is', record.period_category_id)

    @api.one
    @api.constrains('user_id', 'period_id')
    def _check_user_period(self):
        if self.env['membership'].search_count([('user_id.id', '=', self.user_id.id), ('period_id.id','=',self.period_id.id),]) > 1:
            import ipdb; ipdb.set_trace()
            raise exceptions.ValidationError("The user '%s' has already a membership for this period (%s). Please change accordingly." % (self.user_id.name, self.period_id.name))

    @api.multi
    def validate_membership_payment(self):
        for record in self:
            record.price_paid = record.price_due

    # @api.model
    @api.multi
    def validate_membership_affiliation(self):
        # import ipdb; ipdb.set_trace()
        for record in self:
            record.state = 'member'
        # view_id = self.env.ref('sport_club_manager.membership_view_form_wizard').id
        # ctx = {}
        # if len(self) == 1:
        #     # ctx['default_category_id'] = self.category_id.id
        #     # ctx['default_period_id'] = self.period_id.id
        #     ctx['default_price_paid'] = self.price_paid
        #     ctx['default_price_due'] = self.price_due
        # return {
        #     'type': 'ir.actions.act_window',
        #     'name': 'Affiliate a Member',
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'res_model': 'membership_wizard',
        #     # 'res_id': self.id,
        #     'target': 'new',
        #     'views': [[view_id, 'form']],
        #     'context': ctx,
        # }

    @api.multi
    def reject_membership_affiliation(self):
        for record in self:
            record.state = 'rejected'

    @api.multi
    def send_email(self):
        for record in self:
            record.mail_sent = True
            # record.mail_sent = True  # TODO uncomment me (and delete previous line)
            template = self.env.ref('sport_club_manager.email_template_membership_affiliation_confirmation')
            ctx = {
                'company_id': self.env.user.company_id,
            }
            self.with_context(ctx).message_post_with_template(template.id)
            #template.with_context(ctx).send_mail(self.id, force_send=True)

    def copy(self, default=None):
        # import ipdb; ipdb.set_trace()
        self.ensure_one()
        default = dict(default or {})
        default.setdefault('period_category_id', self.period_category_id.id)
        default.setdefault('user_id', self.user_id.id)
        default.setdefault('currency_id', self.currency_id.id)
        default.setdefault('price_paid', 0)
        default.setdefault('price_due', self.price_due)
        default.setdefault('state', self.state)
        import pprint; pprint.pprint(default)
        new_membership = super(Membership, self).copy(default)
        print('=== Membership ===', new_membership, new_membership.period_id.name, new_membership.category_id.name)

        return new_membership

    def _expand_state(self, states, domain, order):
        return [key for key, val in type(self).state.selection]

# class Wizard(models.TransientModel):
#     _name = 'membership_wizard'
#     # _inherit = 'membership'

#     def default_get(self):
#         import pprint
#         pprint.pprint(self._context)

#     def _default_membership(self):
#         return self.env['membership'].browse(self._context.get('active_id'))

#     send_email = fields.Boolean(
#         string='Email to Member',
#         default=True,
#         help='Sends an email to the member to advise him  of its affiliation.',
#     )

#     membership_id = fields.Many2one(
#         comodel_name='membership',
#         string='Membership',
#         required=True,
#         default=_default_membership,
#     )

#     @api.multi
#     def run_affiliation(self):
#         import ipdb; ipdb.set_trace()
#         #self.session_id.attendee_ids |= self.attendee_ids
#         self.ensure_one()  # 
#         self.write({'state': 'second',
#                     'rental_date': self.rental_date,
#                     'book_ids': self.book_ids,})
#         return {
#             'type': 'ir.actions.act_window',
#             'res_model': 'librarymanagement.make_rental',
#             'view_mode': 'form',
#             'view_type': 'form',
#             'res_id': self.id,
#             'target': 'new',
#         }


#     def _warningR(self, title, message):
#         return {'warning': {
#             'title': title,
#             'message': message,
#         }}
#     @api.onchange('test')
#     def _verify_valid_seats(self):
#         if True:  # self.seats < 0:
#             return self._warningR("Incorrect 'seats' value",  "The number of available seats may not be negative")
#         else:  # if self.seats < len(self.attendee_ids):
#             return self._warningR("Too many attendees", "Increase seats or remove excess attendees")