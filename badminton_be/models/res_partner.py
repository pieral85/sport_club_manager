# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
from urllib.parse import parse_qs, urlencode, urlparse

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

LFBB_ROOT_URL = 'https://lfbb.tournamentsoftware.com'


class ResPartner(models.Model):
    _inherit = 'res.partner'

    lfbb_membership_number = fields.Char('LFBB Membership Number', copy=False,
        help="LFBB membership number of the player.\nUsually looks like 300xxxxx.")
    lfbb_uuid = fields.Char('LFBB UUID', inverse='_inverse_lfbb_uuid', copy=False,
        help="LFBB UUID of the player/club. Can also be any valid URL:\n" \
        "i.e. #1: https://lfbb.tournamentsoftware.com/association/group/<UUID>\n" \
        "i.e. #2: https://lfbb.tournamentsoftware.com/organization/group.aspx?id=...&gid=<UUID>")
    lfbb_external_url = fields.Char('LFBB External URL', compute='_compute_lfbb_url',
        help="Player/club external link (do not require any authentication).")
    lfbb_internal_url = fields.Char('LFBB Internal URL', compute='_compute_lfbb_url',
        help="Player/club internal link (require an authentication with club admin account).")

    @api.depends('lfbb_uuid')
    def _compute_lfbb_url(self):
        for record in self:
            if not record.lfbb_uuid:
                record.lfbb_external_url = ''
                record.lfbb_internal_url = ''
            else:
                int_mid_url = 'association/group' if record.is_company else 'player-profile'
                record.lfbb_external_url = f'{LFBB_ROOT_URL}/{int_mid_url}/{record.lfbb_uuid}'
                ext_id_key, end_url = ('gid', 'group.aspx') if record.is_company else ('mid', 'member.aspx')
                url_params = urlencode({ext_id_key: record.lfbb_uuid})
                record.lfbb_internal_url = f'{LFBB_ROOT_URL}/organization/{end_url}?{url_params}'

    @api.constrains('lfbb_membership_number')
    def _check_lfbb_membership_number(self):
        """ Checks that the number of the LFBB membership is unique.

        :return: None
        """
        for record in self:
            if record.lfbb_membership_number and \
               self.search_count([('lfbb_membership_number', '=', record.lfbb_membership_number)]) > 1:
                raise ValidationError(_("The LFBB membership number must be unique! " \
                    "Please change it accordingly or leave it empty."))

    @api.constrains('lfbb_uuid')
    def _check_lfbb_uuid(self):
        """ Checks that the external UUID of the LFBB membership is unique and well formatted.

        :return: None
        """
        regex = re.compile('^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}\Z', re.I)
        for record in self:
            if not record.lfbb_uuid:
                continue
            if not regex.match(record.lfbb_uuid):
                raise ValidationError(_("The %s ('%s') does not match the UUID4 format.\n" \
                    "It should look like 'xxxxxxxx-xxxx-4xxx-xxxx-xxxxxxxxxxxx' or any valid URL from %s.",
                    record._fields['lfbb_uuid'].string, record.lfbb_uuid, LFBB_ROOT_URL))
            if self.search_count([('lfbb_uuid', '=', record.lfbb_uuid)]) > 1:
                raise ValidationError(_("The %s must be unique! Please change it accordingly or leave it empty.",
                    record._fields['lfbb_uuid'].string))

    def _inverse_lfbb_uuid(self):
        for record in self:
            url_parsed = urlparse(record.lfbb_uuid)
            if urlparse(LFBB_ROOT_URL).netloc != url_parsed.netloc:
                continue
            paths = url_parsed.path.split('/')

            if record.is_company:
                if url_parsed.path == '/organization/group.aspx':
                    ext_uuid = parse_qs(url_parsed.query).get('gid', [''])[0]
                elif '/association/group' in url_parsed.path:
                    ext_uuid = paths[paths.index('group') + 1]
            else:
                if url_parsed.path == '/organization/member.aspx':
                    ext_uuid = parse_qs(url_parsed.query).get('mid', [''])[0]
                elif 'player-profile' in paths:
                    ext_uuid = paths[paths.index('player-profile') + 1]
            record.lfbb_uuid = ext_uuid
