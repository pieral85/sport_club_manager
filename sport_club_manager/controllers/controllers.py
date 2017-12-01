# -*- coding: utf-8 -*-

from odoo import http
from odoo.addons.auth_signup.controllers.main import AuthSignupHome

_URL_ROOT = '/sport'

class SportClubManager(AuthSignupHome):
    @http.route('%s/period/' % _URL_ROOT, auth='public', website=True)
    def period(self, **kw):
        periods = http.request.env['period'].search([])
        return http.request.render('sport_club_manager.website_period', {
            'periods': periods,
        })

    @http.route('%s/membership/request' % _URL_ROOT, auth='user', website=True)
    def request_membership(self):
        consumed_period_ids = http.request.env['membership'].search([('user_id', '=', http.request.uid),]).mapped('period_id').ids
        period_category_ids = http.request.env['period_category'].search([
            ('period_id.active', '=', True),
            ('period_id.id', 'not in', consumed_period_ids),
            ]
        )
        return http.request.render('sport_club_manager.website_membership_request', {
            'period_categories': period_category_ids,
        })

    @http.route('%s/members/<model("res.users"):member>/' % _URL_ROOT, auth='public', website=True)
    def member(self, member):
        return http.request.render('sport_club_manager.website_member_info', {
            'player': member
        })

    @http.route('%s/info_club/' % _URL_ROOT, auth='public', website=True)
    def info_club(self):
        committee = (
            ('President', http.request.env['res.users'].search([('president', '=', True),])),
            ('Secretary', http.request.env['res.users'].search([('secretary', '=', True),])),
            ('Treasurer', http.request.env['res.users'].search([('treasurer', '=', True),])),
        )
        return http.request.render('sport_club_manager.website_info_club', {
            'committee': committee,
        })

    @http.route('%s/my/membership/historical' % _URL_ROOT, auth='user', website=True)
    def membership_historical(self):
        memberships = http.request.env['membership'].search([
            ('user_id.id', '=', http.request.uid),
            ]
        )
        return http.request.render('sport_club_manager.website_info_club', {
            'memberships': memberships,
        })
