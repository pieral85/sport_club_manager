# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from re import match

# from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, exceptions, _


class ResUsers(models.Model):
    _inherit = 'res.users'

    # action_id = fields.Many2one('ir.actions.actions', string='Home Action', help="If specified, this action will be opened at log on for this user, in addition to the standard menu.")
    action_id = fields.Many2one(
        comodel_name='ir.actions.actions',
        string='Home Action',
        compute='_get_action_id',
        help="If specified, this action will be opened at log on for this user, in addition to the standard menu."
    )
    membership_ids = fields.One2many(
        comodel_name='membership',
        inverse_name='user_id',
        string='Memberships',
    )
    role_ids = fields.One2many(
        comodel_name='role',
        inverse_name='user_id',
        string='Roles',
    )
    president = fields.Boolean('Is President', compute='_compute_role', store=True, readonly=True)
    secretary = fields.Boolean('Is Secretary', compute='_compute_role', store=True, readonly=True)
    treasurer = fields.Boolean('Is Treasurer', compute='_compute_role', store=True, readonly=True)
    manager = fields.Boolean('Is Manager', default=False)

    @api.depends('role_ids', 'role_ids.current', 'role_ids.name')
    def _compute_role(self):
        print('\n_compute_role', self)
        for user in self:
            user.president = user.role_ids.filtered(lambda r: r.current and r.name == 'president')
            user.secretary = user.role_ids.filtered(lambda r: r.current and r.name == 'secretary')
            user.treasurer = user.role_ids.filtered(lambda r: r.current and r.name == 'treasurer')

    @api.onchange('secretary')
    def _on_change_secretary(self):
        if self.secretary:
            self.manager = True

    @api.onchange('treasurer')
    def _on_change_treasurer(self):
        if self.treasurer:
            self.manager = True

    @api.onchange('president')
    def _on_change_president(self):
        if self.president:
            self.manager = True

    @api.multi
    def modify_role(self):
        self.ensure_one()
        role_name = self._context.get('role_name', '')
        current_role = self.role_ids.filtered(lambda r: r.current and r.name == role_name)
        action = self._context.get('action', '')
        if (action == 'stop' and not current_role) or (action == 'start' and current_role):
            raise exceptions.Warning(_("Error while trying to %s role '%s': maybe no current role has been found!") % (action, role_name))

        if action == 'start':
            self.role_ids.create({
                'name': role_name,
                'user_id': self.id,
                })
        elif action == 'stop':
            if current_role.start_date >= fields.Date.today():
                current_role.unlink()
            else:
                current_role.end_date = fields.Date.today()
        # return {'type': 'ir.actions.act_window_close'}

    @api.onchange('login')
    def validate_email(self):
        if not self.login:
            return
        if not match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", self.login):
            raise exceptions.ValidationError(_('Invalid email address. Please enter a valid one.'))
        if self.search_count([('login', '=', self.login), ]):
            raise exceptions.ValidationError(_('This email already exists. Please enter another one.'))

    @api.multi
    def write(self, vals):
        self._update_groups(vals)
        return super(ResUsers, self).write(vals)

    @api.model
    def create(self, vals):
        self._update_groups(vals)
        return super(ResUsers, self).create(vals)

    def _update_groups(self, vals):
        """ Updates user's groups if one of the following attributes has been changed: 'president', 'secretary', 'treasurer' or 'manager'.

        :return: None
        """
        new_groups = vals.get('groups_id', [])
        status_groups = (
            ('president', 'sport_club_manager.group_sport_club_manager_president'),
            ('secretary', 'sport_club_manager.group_sport_club_manager_secretary'),
            ('treasurer', 'sport_club_manager.group_sport_club_manager_treasurer'),
            ('manager', 'sport_club_manager.group_sport_club_manager_manager'),
        )
        committee_group_action = ''
        for status, group_name in status_groups:
            group = self.env.ref(group_name)
            if status in vals:
                # adds current group in user groups
                if vals[status] and group not in self.groups_id:
                    new_groups.append((4, group.id))
                    committee_group_action = 'preserve'
                # removes current group from user groups
                elif not vals[status] and group in self.groups_id:
                    new_groups.append((3, group.id))
                    if not committee_group_action:
                        committee_group_action = 'delete'
            elif group in self.groups_id:
                committee_group_action = 'preserve'

        # removes group 'group_sport_club_manager_committee' from user groups
        if committee_group_action == 'delete':
            new_groups.append((3, self.env.ref('sport_club_manager.group_sport_club_manager_committee').id))
        vals['groups_id'] = new_groups

    @api.depends('groups_id')
    def _get_action_id(self):
        """ Calculates the action that will be opened at log on for current user, based on his groups.

        :return: None
        """
        for record in self:
            if self.env.ref('base.group_system') in record.groups_id or \
               self.env.ref('sport_club_manager.group_sport_club_manager_committee') in record.groups_id:
                record.action_id = self.env.ref('sport_club_manager.action_membership').id
            else:
                record.action_id = None
