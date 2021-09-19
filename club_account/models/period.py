# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class Period(models.Model):
    _inherit = 'period'
    _inherits = {'product.template': 'product_tmpl_id'}

    product_tmpl_id = fields.Many2one('product.template', string='Product Template',
        required=True, readonly=True, ondelete='restrict')

    @api.model
    def create(self, values):
        if 'product_tmpl_id' not in values or not values['product_tmpl_id']:
            ProdTmpl = self.env['product.template']
            prod_vals = ProdTmpl._get_product_default_values()
            prod_vals.update(name=values.get('name', _('Membership Product')))
            product_tmpl_id = ProdTmpl.create(prod_vals).id
            values['product_tmpl_id'] = product_tmpl_id
        return super(Period, self).create(values)

    def unlink(self):
        product_templates = self.mapped('product_tmpl_id')
        ret = super(Period, self).unlink()
        product_templates.unlink()
        return ret
