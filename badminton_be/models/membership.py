# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class Membership(models.Model):
    _inherit = 'membership'

    member_lfbb_membership_number = fields.Char(related='member_id.lfbb_membership_number', readonly=False)
    member_lfbb_uuid = fields.Char(related='member_id.lfbb_uuid', readonly=False)
    member_lfbb_external_url = fields.Char(related='member_id.lfbb_external_url', readonly=False)
    member_lfbb_internal_url = fields.Char(related='member_id.lfbb_internal_url', readonly=False)
