# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import date

from odoo import api, fields, models, _

CONTACT_DOMAIN = lambda self: [('is_company', '=', False), ('type', '=', 'contact')]
ADDRESS_FIELDS = ('street', 'street2', 'city', 'state_id', 'zip', 'country_id', 'phone', 'mobile', 'email')


class ResPartner(models.Model):
    _inherit = 'res.partner'

    company_type = fields.Selection(string='Company Type',
        selection=[('person', 'Individual'), ('company', 'Club')])
    gender = fields.Selection(string='Gender', selection=[('male', 'Male'), ('female', 'Female')])
    birthdate = fields.Date('Birthdate')
    age = fields.Integer('Age', compute='_compute_age', help="Age (as of today)")
    club_id = fields.Many2one('res.partner', string='Club', domain=[('is_company', '=', True)], tracking=True)
    player_ids = fields.One2many('res.partner', 'club_id', string='Players')
    responsible_id = fields.Many2one('res.partner', string='Responsible',
        domain=CONTACT_DOMAIN, tracking=True, inverse='_inverse_responsible_id',
        help='Contact responsible of current contact. Usually, all communication will happen with the responsible. \
        This is usually useful for a minor child.')
    dependent_ids = fields.One2many('res.partner', 'responsible_id', string='Dependents')
    membership_ids = fields.One2many('membership', 'member_id', string='Memberships')
    membership_count = fields.Integer('Count Memberships', compute='_compute_memberships')

    street = fields.Char(inverse='_inverse_address', tracking=True)
    street2 = fields.Char(inverse='_inverse_address', tracking=True)
    city = fields.Char(inverse='_inverse_address', tracking=True)
    state_id = fields.Many2one('res.country.state', inverse='_inverse_address', tracking=True)
    zip = fields.Char(inverse='_inverse_address', tracking=True)
    country_id = fields.Many2one('res.country', inverse='_inverse_address', tracking=True)
    phone = fields.Char(inverse='_inverse_address', tracking=True)
    mobile = fields.Char(inverse='_inverse_address', tracking=True)
    email = fields.Char(inverse='_inverse_address', tracking=True)

    def _get_hierarchical_contacts(self, existing_contacts=None, exclude_contact=None):
        """ Returns (recursively) all responsible and dependents contacts related to `self` """
        if existing_contacts is None:
            existing_contacts = self.env['res.partner']
        if exclude_contact is None:
            exclude_contact = self._origin
        new_contacts = (self.responsible_id._origin | self.dependent_ids._origin) - existing_contacts
        if new_contacts:
            return new_contacts._get_hierarchical_contacts(existing_contacts | new_contacts, exclude_contact)
        else:
            return existing_contacts - exclude_contact

    def _inverse_address(self):
        for record in self:
            def has_different_address(contact):
                return any(record[field] != contact[field] for field in ADDRESS_FIELDS)

            related_contacts = self._get_hierarchical_contacts().filtered(has_different_address)
            if related_contacts:
                related_contacts.write({field: record[field] for field in ADDRESS_FIELDS})

    def _inverse_responsible_id(self):
        non_address_fields = [field for field in ('email', 'phone', 'mobile') if field in ADDRESS_FIELDS]
        # address fields: we want to update all of them or none (otherwise, updating only some of them
        # may lead to an insconsistent address (i.e. living in NY in Belgium country)).
        # However, for fields such as email, phone and mobile, they can be updated 1 by 1
        address_fields = [field for field in ADDRESS_FIELDS if field not in non_address_fields]
        for member in self:
            if not member.responsible_id:
                continue

            # 1) get non empty fields for the responsible in order to update member fields
            resp = member.responsible_id
            resp_fields = [field for field in non_address_fields if resp[field]]
            resp_address_ok = any(resp[field] for field in address_fields)
            if resp_address_ok:
                resp_fields.extend(address_fields)
            member.write({field: resp[field] for field in resp_fields})
            # 2) get non empty fields for the member in order to update responsible fields
            member_fields = [field for field in non_address_fields if member[field] and field not in resp_fields]
            member_address_ok = not resp_address_ok and any(member[field] for field in address_fields)
            if member_address_ok:
                member_fields.extend(address_fields)
            resp.write({field: member[field] for field in member_fields})

    @api.onchange('responsible_id')
    def _onchange_responsible_id(self):
        if self.responsible_id and any(self[field] != self.responsible_id[field] for field in ADDRESS_FIELDS):
            return {
                'warning': {
                    'title': _("Message"),
                    'message': _("Current data will be changed based on new responsible!"),
                    'type': 'notification',
                },
            }

    @api.onchange(*ADDRESS_FIELDS)
    def _onchange_address(self):
        def has_different_address(contact):
            return any(self[field] != contact[field] for field in ADDRESS_FIELDS)

        contacts = self._get_hierarchical_contacts()
        contacts = contacts.filtered(has_different_address)
        if contacts:
            return {
                'warning': {
                    'title': _("Message"),
                    'message': _("Related data of %s will also be modified!") % ', '.join(contacts.mapped('name')),
                    'type': 'notification',
                },
            }

    def _compute_memberships(self):
        for record in self:
            record.membership_count = len(record.membership_ids)

    @api.depends('birthdate')
    def _compute_age(self):
        today = date.today()
        for partner in self:
            if partner.birthdate:
                offset = int((today.month, today.day) < (partner.birthdate.month, partner.birthdate.day))
                partner.age = today.year - partner.birthdate.year - offset
            else:
                partner.age = 0

    def action_view_memberships(self):
        self.ensure_one()
        memberships = self.membership_ids
        action = memberships._get_dynamic_action()
        action.update({
            'name': _('Memberships'),
            'context': {'default_member_id': self.id},
        })
        return action
