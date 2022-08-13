# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class MailTemplate(models.Model):
    _inherit = 'mail.template'

    kind = fields.Selection(selection_add=[('interclub', 'Interclub')], ondelete={'interclub': 'cascade'})
