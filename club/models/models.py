# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class Base(models.AbstractModel):
    _inherit = 'base'

    def _get_closest_lang(self):
        """ Return closest(*) lang from a recordset, compared to user company lang.
            If records have no lang (because field does not exist or it exists but is not set),
            the lang of the company is returned.

            (*) i.e. consider company lang is 'fr_FR': lang order would be 'fr_FR' > 'fr_BE' > 'en_US'
        """
        company_lang = self.env.company.partner_id.lang
        if 'lang' not in self:
            return company_lang
        langs = self.mapped('lang')
        langs.sort(key=lambda l: (l == company_lang) + (l[:2] == company_lang[:2]), reverse=True)
        return langs[0] if langs else company_lang
