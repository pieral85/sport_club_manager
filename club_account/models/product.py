# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    membership_ok = fields.Boolean('For Membership', readonly=True)

    @api.model
    def _get_product_default_values(self):
        return {
            'membership_ok': True,
            'type': 'service',
            'purchase_ok': False,
            'list_price': 0.0,  # price should be set only on product variants
        }

    @api.constrains('name', 'membership_ok', 'attribute_line_ids')
    def _check_membership_product(self):
        """ Checks that the name is unique for "membership" products.

        :return: None
        """
        membership_attr = self.env.ref('club_account.product_attribute_membership_category')
        for prod_tmpl in self:
            if prod_tmpl.membership_ok:
                if self.search_count([('membership_ok', '=', True), ('name', '=', prod_tmpl.name)]) > 1:
                    raise ValidationError(_("For 'membership' products, " \
                        "the name must be unique! Please change it accordingly."))
                if prod_tmpl.attribute_line_ids.filtered(lambda ptal: ptal.attribute_id != membership_attr):
                    raise ValidationError(_("For 'membership' products, " \
                        "the only valid attribute is '{}'.").format(membership_attr.name))


class ProductProduct(models.Model):
    _inherit = 'product.product'

    period_category_ids = fields.One2many('period.category', 'product_id', string='Period Categories', readonly=True,
        help="Field only existing to allow the compute of the period category field (many2one).")
    period_category_id = fields.Many2one('period.category', string='Period Category',
        compute='_compute_period_category')

    @api.depends('period_category_ids')
    def _compute_period_category(self):
        for product in self:
            product.period_category_id = self.period_category_ids[0] if product.period_category_ids else False

    def _compute_product_lst_price(self):
        """ Customize the compute of the list price for products related to "memberships".
        For "usual" products, compute as per Odoo standard method.
         """
        membership_products = self.filtered(lambda p: p.period_category_ids)
        for product in membership_products:
            product.lst_price = product.period_category_ids.price_due
        super(ProductProduct, self - membership_products)._compute_product_lst_price()

    def price_compute(self, price_type, uom=False, currency=False, company=None):
        """ Customize the price for products related to "memberships".
        For "usual" products, compute as per Odoo standard method.
        Amongst others, this method is called for prices rendered on the website.
         """
        prices = super(ProductProduct, self).price_compute(price_type, uom, currency, company)
        for product in self.filtered(lambda p: p.period_category_ids):
            prices[product.id] = product.lst_price
        return prices

    @api.constrains('period_category_ids')
    def _check_period_category_ids(self):
        for product in self:
            if not product.membership_ok and product.period_category_ids:
                raise ValidationError(_("You cannot have period categories for a non 'membership' product."))
            elif len(product.period_category_ids) > 1:
                raise ValidationError(_("You cannot have multiple period categories for this product."))
