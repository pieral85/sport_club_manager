# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class WebsiteMenu(models.Model):
    _inherit = 'website.menu'

    @api.model
    def create(self, vals):
        """ Get data more consistant regarding 'website_id' and 'parent_id' fields.

        When installing module with some website menu records (coming from xml files),
        there were sometimes some strange behaviours:
         - If a record did not have any 'website_id' defined, it was set as a "root menu",
           even if a 'parent_id' menu was defined on the record.
         - It was possible to define a record on a website A, with a parent menu coming from
           website B. With this inherit, we try to associate the record with a similar
           parent menu coming from the same website A.
        """

        if not self._context.get('install_mode'):
            # When created manually (not at the module install), we trust the user
            # and let him do what he wants
            return super(WebsiteMenu, self).create(vals)

        Menu = self.env['website.menu']
        initial_website_id = vals.get('website_id') or self._context.get('website_id') or False
        if initial_website_id:
            if vals.get('parent_id'):
                # Try to retrieve the parent menu identical to the one in 'vals'
                # but coming from the same website then the one in 'vals'
                initial_parent = Menu.browse(vals['parent_id'])
                if initial_parent.website_id.id != initial_website_id:
                    new_parent = Menu.search([
                        ('website_id', '=', initial_website_id),
                        ('url', '=', initial_parent.url),
                    ], limit=1)
                    if new_parent and new_parent != initial_parent:
                        vals['parent_id'] = new_parent.id
            else:
                # When no parent menu is set, take the default one of the website
                vals['parent_id'] = self.env['website'].browse(initial_website_id).menu_id.id
        elif vals.get('parent_id'):
            # When no website is set, assign the website of the parent menu
            vals['website_id'] = Menu.browse(vals['parent_id']).website_id.id
        return super(WebsiteMenu, self).create(vals)
