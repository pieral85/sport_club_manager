# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class FieldConverter(models.AbstractModel):
    _inherit = 'ir.qweb.field'

    @api.model
    def record_to_html(self, record, field_name, options):
        res = super(FieldConverter, self).record_to_html(record, field_name, options)
        if not res or 'chars_to_show' not in options:
            return res
        replacement_char = options.get('replacement_char', '_')
        pivot_char = options.get('pivot_char')
        chars_to_show = options['chars_to_show']
        convert = lambda s: s[:chars_to_show] + replacement_char * (len(s) - chars_to_show)
        if not pivot_char:
            return convert(res)
        return pivot_char.join(convert(s) for s in res.split(pivot_char))
