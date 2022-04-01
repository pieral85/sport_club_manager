# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.http import request


class CustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        values['membership_count'] = request.env['membership'].search_count([
            ('member_id', '=', request.env.user.partner_id.id)
        ])
        return values

    @http.route(['/my/memberships', '/my/memberships/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_memberships(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        Membership = request.env['membership']
        domain = [
            ('member_id.id', '=', request.env.user.partner_id.id),
            ('state', 'in', ['requested', 'member']),
        ]

        searchbar_sortings = {
            'date': {'label': _('Season'), 'order': 'period_id desc'},
            'state': {'label': _('Status'), 'order': 'state desc'},
            'paid': {'label': _('Payment Status'), 'order': 'paid'},
        }
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # memberships count
        membership_count = Membership.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/memberships",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=membership_count,
            page=page,
            step=self._items_per_page
        )

        # content according to pager and archive selected
        memberships = Membership.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'date': date_begin,
            'date_end': date_end,
            'memberships': memberships,
            'page_name': 'membership',
            'default_url': '/my/memberships',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby
        })
        return request.render("club.portal_my_memberships", values)
