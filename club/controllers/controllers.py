# -*- coding: utf-8 -*-

from odoo.api import Environment
from odoo.http import request, route
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo import SUPERUSER_ID
from odoo import registry as registry_get

_URL_ROOT = '/club'


class Club(AuthSignupHome):

    @route('%s/period/' % _URL_ROOT, auth='public', website=True)
    def period(self, **kw):
        periods = request.env['period'].search([])
        return request.render('club.website_period', {
            'periods': periods,
        })

    @route('%s/membership/request' % _URL_ROOT, auth='user', website=True)
    def request_membership(self):
        consumed_period_ids = request.env['membership'].search([('member_id', '=', request.env.user.partner_id.id),]).mapped('period_id').ids  # TODO Test 'request.env.user.partner_id.id'
        period_category_ids = request.env['period.category'].search([
            ('period_id.active', '=', True),
            ('period_id.id', 'not in', consumed_period_ids),
            ]
        )
        return request.render('club.website_membership_request', {
            'period_categories': period_category_ids,
        })

    # @route('%s/members/<model("res.partner"):member>/' % _URL_ROOT, auth='public', website=True)
    # def member(self, member):
    #     return request.render('club.website_member_info', {
    #         'member': member
    #     })

    @route('/aboutus', auth='public', website=True)
    def info_club(self):
        User = request.env['res.users'].sudo()
        # TODO Add _ for following terms
        committee = (
            ('President', User.search([('president', '=', True),])),
            ('Secretary', User.search([('secretary', '=', True),])),
            ('Treasurer', User.search([('treasurer', '=', True),])),
        )
        return request.render('club.website_info_club', {
            'committee': committee,
        })
    # @route('%s/info_club/' % _URL_ROOT, auth='public', website=True)
    # def info_club(self):
    #     committee = (
    #         ('President', request.env['res.users'].search([('president', '=', True),])),
    #         ('Secretary', request.env['res.users'].search([('secretary', '=', True),])),
    #         ('Treasurer', request.env['res.users'].search([('treasurer', '=', True),])),
    #     )
    #     return request.render('club.website_info_club', {
    #         'committee': committee,
    #     })

    @route('%s/my/membership/<string:action>' % _URL_ROOT, type='http', auth='public', website=True)
    def membership_invitation_response(self, action, db, token):
        registry = registry_get(db)
        messages = {}
        with registry.cursor() as cr:
            env = Environment(cr, SUPERUSER_ID, {})
            membership = env['membership'].search([('token', '=', token)])
            if not token or not membership or len(membership) > 1:
                return request.render('website.404')

            if not membership.token_is_valid and action != 'view':
                messages['warning'] = 'You cannot perform this action because the token has expired.'

            if membership.state == 'member':
                messages['info'] = 'Congratulations, your membership has already been approved by the committee.'
            elif membership.token_is_valid:
                if action == 'accept':
                    membership.do_accept()
                    messages['success'] = 'You have accepted the invitation. Your membership must now be approved by the committee.'
                elif action == 'decline':
                    membership.do_decline()
                    messages['success'] = 'You have declined the invitation.'
                elif action == 'view' and membership.state == 'requested':
                    messages['info'] = 'Your membership request is going to be examined by the committee. \
                        Please ensure to pay the amount due first.'

            response_content = env['ir.ui.view']._render_template(
                'club.membership_affiliation_page_anonymous', {
                    'membership': membership,
                    'messages': messages,
                })
        return request.make_response(response_content, headers=[('Content-Type', 'text/html')])
