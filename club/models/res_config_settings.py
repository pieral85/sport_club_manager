# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    mail_local_part = fields.Char('Mail Local Part',
        help="""If you are using an email address as mail server, enter the local part of the email.
        i.e. If you use 'my_club@gmail.com' as mail server, 'my_club' should be the mail local part.
        """)

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('mail_local_part', (self.mail_local_part or ''))

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICP = self.env['ir.config_parameter']
        res.update(
            mail_local_part=ICP.get_param('mail_local_part', default=''),
        )
        return res
