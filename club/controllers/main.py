# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.addons.web.controllers.main import DataSet


class ClubDataSet(DataSet):
    def do_search_read(self, model, fields=False, offset=0, limit=False, domain=None, sort=None):
        tags_field_name = {
            'res.partner': 'category_id',
            'membership': 'member_tag_ids',
        }.get(model)
        if not tags_field_name:
            return super().do_search_read(model, fields, offset, limit, domain, sort)

        new_domain = []
        for sub_domain in domain:
            if sub_domain[0] == tags_field_name and 'ilike' in sub_domain[1]:
                if sub_domain[1].startswith('not '):
                    new_domain.append('!')
                sub_domain[1] = 'child_of'
                new_domain.append(sub_domain)
            else:
                new_domain.append(sub_domain)
        return super().do_search_read(model, fields, offset, limit, new_domain, sort)
