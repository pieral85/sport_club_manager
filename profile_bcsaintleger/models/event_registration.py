from random import randint

from odoo import api, fields, models, _


class EventRegistrationTag(models.Model):
    _description = 'Event Registration Tag'
    _name = 'event.registration.tag'
    _order = 'name'
    _parent_store = True

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(string='Tag Name', required=True, translate=True)
    color = fields.Integer(string='Color', default=_get_default_color)
    parent_id = fields.Many2one('event.registration.tag', string='Parent Tag', index=True, ondelete='cascade')
    child_ids = fields.One2many('event.registration.tag', 'parent_id', string='Child Tags')
    active = fields.Boolean(default=True, help="The active field allows you to hide the tag without removing it.")
    parent_path = fields.Char(index=True)
    registration_ids = fields.Many2many('event.registration', column1='tag_id', column2='registration_id',
        string='Registrations', copy=False)

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_('You can not create recursive tags.'))

    def name_get(self):
        """ Return the tags display name, including their direct
            parent by default.

            If ``context['registration_tag_display']`` is ``'short'``, the short
            version of the tag name (without the direct parent) is used.
            The default is the long version.
        """
        if self._context.get('registration_tag_display') == 'short':
            return super().name_get()

        res = []
        for tag in self:
            names = []
            current = tag
            while current:
                names.append(current.name)
                current = current.parent_id
            res.append((tag.id, ' / '.join(reversed(names))))
        return res

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if name:
            # Be sure name_search is symetric to name_get
            name = name.split(' / ')[-1]
            args = [('name', operator, name)] + args
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)


class EventRegistration(models.Model):
    _inherit = 'event.registration'

    tag_ids = fields.Many2many('event.registration.tag', column1='registration_id',
                                    column2='tag_id', string='Tags')
