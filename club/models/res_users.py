# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from re import match

# from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, Warning


class ResUsers(models.Model):
    _inherit = 'res.users'
    # TODO Test constraint
    # TODO Add @api.constrains('...')???
    _sql_constraints = [
        ('partner_uniq', 'unique(partner_id)', 'The partner should be unique!'),
    ]

    # action_id = fields.Many2one('ir.actions.actions', string='Home Action', help="If specified, this action will be opened at log on for this user, in addition to the standard menu.")
    action_id = fields.Many2one(
        comodel_name='ir.actions.actions',
        string='Home Action',
        compute='_get_action_id',
        store=True,
        help="If specified, this action will be opened at log on for this user, in addition to the standard menu."
    )
    role_ids = fields.One2many(
        comodel_name='role',
        inverse_name='user_id',
        string='Roles',
    )
    president = fields.Boolean('Is President', compute='_compute_role', store=True, readonly=True)
    secretary = fields.Boolean('Is Secretary', compute='_compute_role', store=True, readonly=True)
    treasurer = fields.Boolean('Is Treasurer', compute='_compute_role', store=True, readonly=True)
    committee_user = fields.Boolean('Is Committee User',
        compute='_compute_committee_user', inverse='_inverse_committee_user',
        help='If checked, the user will have a read access to the application Club Membership Manager.')
    committee_manager = fields.Boolean('Is Committee Manager',
        compute='_compute_committee_manager', inverse='_inverse_committee_manager',
        help='If checked, the user will have a write access to the application Club Membership Manager.\n\
        This will allow the user to manage the application.')
    # TODO Rename `committee_user` and `committee_manager` fields with `is_` prefix
    is_internal = fields.Boolean('Is Internal', compute='_compute_committee_manager')

    def modify_role(self):
        self.ensure_one()
        if not self._context.get('role_name') or not self._context.get('action'):
            return
        role_name, action = self._context['role_name'], self._context['action']
        current_role = self.role_ids.filtered(lambda r: r.current and r.name == role_name)
        if (action == 'stop' and not current_role) or (action == 'start' and current_role):
            raise Warning(_("Error while trying to %s role '%s': maybe no current role has been found!") % (action, role_name))

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
        self.write(self._get_group_vals({role_name: action == 'start'}))

    @api.onchange('login')
    def validate_email(self):
        if not self.login:
            return
        # TODO Do we really need to check email at onchange of login (can't a user login with sth != email?)
        # if not match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", self.login):
        #     raise ValidationError(_('Invalid email address. Please enter a valid one.'))
        if self.search_count([('login', '=', self.login), ]):  # TODO Mettre ça une fois qu'on sauve?
            raise ValidationError(_('This email already exists. Please enter another one.'))

    def _get_group_vals(self, vals):
        """ Updates user's groups if one of the following attributes has been changed: 'president', 'secretary' or 'treasurer'.
        i.e. vals = {'president': True, 'treasurer': False} means the user becomes president but is not treasurer anymore.

        :return: Dictionary with 'groups_id' as a key and the groups and their command numbers as values (typically ready to be used in the 'write' method argument).
        """
        new_groups = []
        status_groups = (
            ('president', 'club.group_club_president'),
            ('secretary', 'club.group_club_secretary'),
            ('treasurer', 'club.group_club_treasurer'),
        )
        committee_manager_group_todo = set()
        for status, group_name in status_groups:
            group = self.env.ref(group_name)
            if status in vals:
                if vals[status]:
                    # adds current group in user groups
                    committee_manager_group_todo.add('add')
                    if group not in self.groups_id:
                        new_groups.append((4, group.id))
                elif not vals[status] and group in self.groups_id:
                    # removes current group from user groups
                    new_groups.append((3, group.id))
                    committee_manager_group_todo.add('delete')
            elif group in self.groups_id:
                # because the user is in another group, we should not remove committee manager group
                committee_manager_group_todo.add('nothing')

        if 'add' in committee_manager_group_todo:
            new_groups.append((4, self.env.ref('club.group_club_committee_manager').id))
        elif 'nothing' in committee_manager_group_todo:
            pass
        elif 'delete' in committee_manager_group_todo:
            new_groups.append((3, self.env.ref('club.group_club_committee_manager').id))
        return {'groups_id': new_groups} if new_groups else {}


    def _compute_committee_user(self):
        for user in self:
            user.committee_user = user.has_group('club.group_club_committee_user')

    def _inverse_committee_user(self):
        ''' Edit user groups when field 'committee_user' is edited. '''
        for user in self:
            user.write({'groups_id': [(4 if user.committee_user else 3, self.env.ref('club.group_club_committee_user').id)]})

    def _compute_committee_manager(self):
        for user in self:
            user.committee_manager = user.has_group('club.group_club_committee_manager')
            user.is_internal = user.has_group('base.group_user')

    def _inverse_committee_manager(self):
        ''' Edit user groups when field 'committee_manager' is edited. '''
        for user in self:
            user.write({'groups_id': [(4 if user.committee_manager else 3, self.env.ref('club.group_club_committee_manager').id)]})

    @api.depends('role_ids', 'role_ids.current', 'role_ids.name')
    def _compute_role(self):
        for user in self:
            user.president = user.role_ids.filtered(lambda r: r.current and r.name == 'president')
            user.secretary = user.role_ids.filtered(lambda r: r.current and r.name == 'secretary')
            user.treasurer = user.role_ids.filtered(lambda r: r.current and r.name == 'treasurer')

    @api.depends('groups_id')
    def _get_action_id(self):
        """ Calculates the action that will be opened at log on for current user, based on his groups.

        :return: None
        """
        # TODO This method is called multiple times when a group is changed on the user (should be 1x)
        for record in self:
            if self.env.ref('base.group_system') in record.groups_id or \
               self.env.ref('club.group_club_committee_user') in record.groups_id:
                record.action_id = self.env.ref('club.action_membership').id
            else:
                record.action_id = None

    @api.model
    def _update_record(self, values):
        model, res_id, values = values['model'], values['browse_id'], values['write_values']
        self.env[model].browse(res_id).write(values)
