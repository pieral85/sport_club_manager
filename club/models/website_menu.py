# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class WebsiteMenu(models.Model):
    _inherit = 'website.menu'

    def _get_website_and_parent(self, website_id, parent_id):
        """ Get data more consistant regarding 'website_id' and 'parent_id' fields.

        When installing/updating module with some website menu records (coming from xml files),
        there were sometimes some strange behaviours:
         - If a record did not have any 'website_id' defined, it was set as a "root menu",
           even if a 'parent_id' menu was defined on the record.
         - It was possible to define a record on a website A, with a parent menu coming from
           website B. With this inherit, we try to associate the record with a similar
           parent menu coming from the same website A.

        :return: updated website and menu parent
        :rtype: dict(['website_id': int][, 'parent_id': int])
        """
        new_vals = {}
        if not self._context.get('install_mode'):
            # When created/updated manually (not at the module install/update),
            # we trust the user and let him do what he wants
            return new_vals

        Menu = self.env['website.menu']
        website_id = website_id or self._context.get('website_id') or False
        if website_id:
            if parent_id:
                # Try to retrieve the parent menu identical to `parent_id`
                # but coming from the same website as the one of `website_id`
                initial_parent = Menu.browse(parent_id)
                if initial_parent.website_id.id != website_id:
                    new_parent = Menu.search([
                        ('website_id', '=', website_id),
                        ('url', '=', initial_parent.url),
                    ], limit=1)
                    if new_parent and new_parent != initial_parent:
                        new_vals['parent_id'] = new_parent.id
            else:
                # When no parent menu is set, take the default one of the website
                new_vals['parent_id'] = self.env['website'].browse(website_id).menu_id.id
        elif parent_id:
            # When no website is set, assign the website of the parent menu
            new_vals['website_id'] = Menu.browse(parent_id).website_id.id
        return new_vals

    @api.model
    def create(self, vals):
        updated_vals = self._get_website_and_parent(vals.get('website_id'), vals.get('parent_id'))
        vals.update(updated_vals)
        return super(WebsiteMenu, self).create(vals)

    def write(self, vals):
        updated_vals = self._get_website_and_parent(vals.get('website_id'), vals.get('parent_id'))
        vals.update(updated_vals)
        return super(WebsiteMenu, self).write(vals)
