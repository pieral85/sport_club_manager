# -*- coding: utf-8 -*-

import logging

from odoo import api, SUPERUSER_ID
from odoo.tools import sql

_logger = logging.getLogger(__name__)

def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    Period = env['period'].with_context(active_test=False)
    ProdTmpl = env['product.template']

    Category = env['category'].with_context(active_test=False)
    categories = Category.search([('product_attribute_value_id', '=', False)])
    _logger.info(f"Creating (or attaching) missing product attributes for categories {categories.ids}")
    prod_attr_id = env.ref('club_account.product_attribute_membership_category').id
    for category in categories:
        pav = env['product.attribute.value'].search([('name', '=', category.name)], limit=1)
        if pav:
            _logger.info(f" Skipping creation of {pav} (already existing)")
        else:
            _logger.info(f" {pav} created")
            pav = env['product.attribute.value'].create({
                'name': category.name,
                'attribute_id': prod_attr_id,
            })
        category.product_attribute_value_id = pav

    periods = Period.search([('product_tmpl_id', '=', False)])
    vals = ProdTmpl._get_product_default_values()
    _logger.info(f"Creating missing product templates for periods {periods.ids}")
    for period in periods:
        prod_tmpl = ProdTmpl.search([('name', '=', period.name)], limit=1)
        if prod_tmpl:
            _logger.info(f" Skipping creation of {prod_tmpl} (already existing)")
        else:
            _logger.info(f" {prod_tmpl} created")
            prod_tmpl = ProdTmpl.create({
                'name': period.name,
            })
        prod_tmpl.write(vals)
        period.product_tmpl_id = prod_tmpl

    period_cats = env['period.category'].with_context(active_test=False).search([('product_id', '=', False)])
    _logger.info(f"Creating missing products for period categories {period_cats.ids}")
    for p_cat in period_cats:
        prod_prod = p_cat._get_expected_product_product()
        if prod_prod:
            _logger.info(f" Skipping creation of {prod_prod} (already existing)")
        else:
            prod_prod = p_cat._create_product_product()
            _logger.info(f" {prod_prod} created")
        p_cat.product_id = prod_prod

def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    sql.drop_not_null(cr, env['category']._table, 'product_attribute_value_id')
    categories = env['category'].search([])  # TODO include inactive ones? (with_context(active_test=False))
    # as categories won't be deleted at uninstall and because there is a `ondelete='restrict'`
    # between `category` and `product.attribute.value`, remove the link between both will allow to delete
    # all product attribute value records:
    categories.write({'product_attribute_value_id': False})
