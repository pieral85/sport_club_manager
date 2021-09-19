# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# TODO
# - géréer le fait que le groupe 'account.group_account_invoice' doit etre intégré à ce module (--> hérité pour le trésorier?)
from odoo import api, fields, models


class Category(models.Model):
    _inherit = 'category'
    _inherits = {
        'product.attribute.value': 'product_attribute_value_id',
    }

    product_attribute_value_id = fields.Many2one('product.attribute.value', string='Product Attribute Value',
        required=True, readonly=True, ondelete='restrict')

    # @api.model_create_multi
    @api.model
    def create(self, values):
        product_attribute_id = self.env.ref('club_account.product_attribute_membership_category').id
        if 'product_attribute_value_id' not in values or not values['product_attribute_value_id']:
            product_attribute_value_id = self.env['product.attribute.value'].create({
                'name': values['name'],
                'attribute_id': product_attribute_id,
            }).id
            values['product_attribute_value_id'] = product_attribute_value_id
        return super(Category, self).create(values)

    def unlink(self):
        product_attribute_values = self.mapped('product_attribute_value_id')
        ret = super(Category, self).unlink()
        product_attribute_values.unlink()
        return ret

# TODO dans methode "write", s'assurer que product_attribute_value_id.name==self.name
# TODO s'assurer que le delete d'une category delete aussi l'attribute_value_id correspondant

# modules qui contiennet un menu pour les product variants:
#     purchase
#     sale_management
#     point_of_sale
#     website_sale
#     stock
#     website_sale_comparison
