# -*- coding: utf-8 -*-

from odoo.api import Environment
from odoo import http
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo import SUPERUSER_ID
from odoo import registry as registry_get

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

    # @http.route('%s/members/<model("res.users"):member>/' % _URL_ROOT, auth='public', website=True)
    # def member(self, member):
    #     return http.request.render('sport_club_manager.website_member_info', {
    #         'player': member
    #     })

    @http.route('/aboutus', auth='public', website=True)
    def info_club(self):
        committee = (
            ('President', http.request.env['res.users'].sudo().search([('president', '=', True),])),
            ('Secretary', http.request.env['res.users'].sudo().search([('secretary', '=', True),])),
            ('Treasurer', http.request.env['res.users'].sudo().search([('treasurer', '=', True),])),
        )
        return http.request.render('sport_club_manager.website_info_club', {
            'committee': committee,
        })
    # @http.route('%s/info_club/' % _URL_ROOT, auth='public', website=True)
    # def info_club(self):
    #     committee = (
    #         ('President', http.request.env['res.users'].search([('president', '=', True),])),
    #         ('Secretary', http.request.env['res.users'].search([('secretary', '=', True),])),
    #         ('Treasurer', http.request.env['res.users'].search([('treasurer', '=', True),])),
    #     )
    #     return http.request.render('sport_club_manager.website_info_club', {
    #         'committee': committee,
    #     })

    @http.route('%s/my/membership/historical' % _URL_ROOT, auth='user', website=True)
    def membership_historical(self):
        # import ipdb; ipdb.set_trace()
        memberships = http.request.env['membership'].search([
            ('user_id.id', '=', http.request.uid),
            ('state', 'in', ['requested', 'member']),
            ],
            order='period_id desc',
        )
        return http.request.render('sport_club_manager.website_my_historical', {
            'memberships': memberships,
        })

    @http.route('%s/my/membership/accept' % _URL_ROOT, type='http', auth='public')
    def accept(self, db, token, action, id, **kwargs):
        registry = registry_get(db)
        with registry.cursor() as cr:
            env = Environment(cr, SUPERUSER_ID, {})
            membership = env['membership'].search([('token', '=', token), ('state', '!=', 'member'), ('user_response', '!=', 'accepted')])
            if membership:
                membership.do_accept()
        return self.view(db, token, action, id, view='form')

    @http.route('%s/my/membership/decline' % _URL_ROOT, type='http', auth='public')
    def declined(self, db, token, action, id):
        registry = registry_get(db)
        with registry.cursor() as cr:
            env = Environment(cr, SUPERUSER_ID, {})
            membership = env['membership'].search([('token', '=', token), ('state', '!=', 'member'), ('user_response', '!=', 'declined')])
            if membership:
                membership.do_decline()
        return self.view(db, token, action, id, view='form')


    @http.route('%s/my/membership/view' % _URL_ROOT, type='http', auth='public')
    def view(self, db, token, action, id, view='calendar'):
        registry = registry_get(db)
        with registry.cursor() as cr:
            # Since we are in auth=none, create an env with SUPERUSER_ID
            env = Environment(cr, SUPERUSER_ID, {})
            membership = env['membership'].search([('token', '=', token),], limit=1)
            if not membership:
                return http.request.not_found()
            response_content = env['ir.ui.view'].render_template(
                'sport_club_manager.membership_affiliation_page_anonymous', {
                    'membership': membership,
                })
            return http.request.make_response(response_content, headers=[('Content-Type', 'text/html')])
