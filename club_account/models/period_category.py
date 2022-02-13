# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PeriodCategory(models.Model):
    _inherit = 'period.category'
    _inherits = {'product.product': 'product_id'}

    _sql_constraints = [
        ('product_id_uniq', 'unique(product_id)', _('The product must be unique!')),
    ]

    product_id = fields.Many2one('product.product', string='Product Variant',
        required=True, readonly=True, ondelete='restrict')

    def _create_product_product(self, period=None, category=None):
        """ TODO

        return: product.product record
        """
        if self.product_id:
            return self.product_id
        if period is None:
            period = self.period_id
        prod_tmpl = period.product_tmpl_id
        membership_attr = self.env.ref('club_account.product_attribute_membership_category')
        if category is None:
            category = self.category_id
        prod_attr_val = category.product_attribute_value_id

        ptal = prod_tmpl.attribute_line_ids.filtered(lambda ptal: ptal.attribute_id == membership_attr)
        if not ptal:
            prod_tmpl.write({
                'attribute_line_ids': [
                    (0, 0, {
                        'attribute_id': membership_attr.id,
                        'value_ids': [(6, 0, [prod_attr_val.id])]
                    }),
                ]
            })
            ptal = prod_tmpl.attribute_line_ids
        else:
            ptal.write({
                'value_ids': [(4, prod_attr_val.id)]
            })
        if len(ptal) != 1:
            raise ValidationError(_("Product template must have only 1 attribute line assigned (currently: '%s').", ptal))

        def get_prod_prod(prod_prod):
            return prod_attr_val in prod_prod.product_template_attribute_value_ids.mapped('product_attribute_value_id')
        return prod_tmpl.product_variant_ids.filtered(get_prod_prod)[0]

    def _get_expected_product_product(self):
        self.ensure_one()
        pav = self.category_id.product_attribute_value_id
        return self.period_id.product_tmpl_id.product_variant_ids\
            .filtered(lambda pp: pav in pp.product_template_attribute_value_ids.mapped('product_attribute_value_id'))

    @api.model
    def create(self, values):
        if 'product_id' not in values or not values['product_id']:
            prod_prod = self._create_product_product(
                period=self.env['period'].browse(values['period_id']),
                category=self.env['category'].browse(values['category_id'])
            )
            values['product_id'] = prod_prod.id
        return super(PeriodCategory, self).create(values)

    def write(self, vals):
        return super(PeriodCategory, self).write(vals)

    def unlink(self):
        for per_cat in self:
            prod_attr_val = per_cat.category_id.product_attribute_value_id
            # get product template attribute line
            # (same as doing `per_cat.product_id.product_template_attribute_value_ids.filtered(lambda ptav: ptav.product_attribute_value_id == prod_attr_val).attribute_line_id`)
            ptal = per_cat.product_id.product_tmpl_id.attribute_line_ids.filtered(lambda ptal: prod_attr_val in ptal.value_ids)
            if prod_attr_val == ptal.value_ids:
                # only one value remaining for attribute line: line must be deleted
                ptal.unlink()
            elif prod_attr_val in ptal.value_ids:
                # multiple values remaining for attribute line: only need to remove value from line
                ptal.write({'value_ids': [(3, prod_attr_val.id)]})
        return super(PeriodCategory, self).unlink()

    @api.constrains('product_id')
    def _check_product_id(self):
        """ Checks that the product of the period category is unique.

        :return: None
        """
        for per_cat in self:
            if self.search_count([('product_id', '=', per_cat.product_id.id)]) > 1:
                raise ValidationError(_("The product of the period category must be unique! " \
                    "Please change it accordingly."))
            expected_prod_prod = per_cat._get_expected_product_product()
            if expected_prod_prod and per_cat.product_id != expected_prod_prod:
                raise ValidationError(_("The expected product of the period category does not match the assigned one."))
