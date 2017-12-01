# -*- coding: utf-8 -*-

from odoo import http
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
# class ModuleTest(http.Controller):
#     @http.route('/module_test/module_test/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/module_test/module_test/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('module_test.listing', {
#             'root': '/module_test/module_test',
#             'objects': http.request.env['module_test.module_test'].search([]),
#         })

#     @http.route('/module_test/module_test/objects/<model("module_test.module_test"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('module_test.object', {
#             'object': obj
#         })
_URL_ROOT = '/sport'

class SportClubManager(AuthSignupHome): # http.Controller):
    # @http.route('/sport/sport/', auth='public', website=True)
    # def index(self, **kw):
    #     return "Hello, world"

    @http.route('%s/period/' % _URL_ROOT, auth='public', website=True)
    def period(self, **kw):
        periods = http.request.env['period'].search([])
        # periods = http.request.env['period'].search(['|', ('active', '=', True), ('active', '=', False)])
        return http.request.render('sport_club_manager.website_period', {
            'periods': periods,
        })

    # @http.route('%s/login/' % _URL_ROOT)
    # def web_login(self, *args, **kw):
    #     return super(SportClubManager, self).web_login(*args, **kw)
    # @http.route('%s/signup/' % _URL_ROOT, type='http', auth='public', website=True, sitemap=False)
    # def web_auth_signup(self, *args, **kw):
    #     return super(SportClubManager, self).web_auth_signup(*args, **kw)
    # @http.route('%s/reset_password' % _URL_ROOT, type='http', auth='public', website=True, sitemap=False)
    # def web_auth_reset_password(self, *args, **kw):
    #     return super(SportClubManager, self).web_auth_reset_password(*args, **kw)

    @http.route('%s/membership/request' % _URL_ROOT, auth='user', website=True)
    def request_membership(self):
        import ipdb; ipdb.set_trace()
        # period_category_ids = http.request.env['period_category'].search([('period_id.active', '=', True),])
        consumed_period_ids = http.request.env['membership'].search([('user_id', '=', http.request.uid),]).mapped('period_id').ids
        period_category_ids = http.request.env['period_category'].search([
            ('period_id.active', '=', True),
            ('period_id.id', 'not in', consumed_period_ids),
            ]
        )
        # period_ids = http.request.env['period'].search([])
        # me = http.request.env['res.users'].search([('id', '=', http.request.session.uid)])
        return http.request.render('sport_club_manager.website_membership_request', {
            # 'me': me,
            #'periods': period_ids,
            'period_categories': period_category_ids,
            # 'status': 'titi',
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
        # me = http.request.env['res.users'].search([('id','=',http.request.session.uid)]).id
        memberships = http.request.env['membership'].search([
            #'&', '|', ('period_id.active', '=', True), ('period_id.active', '=', False),
            ('user_id.id', '=', http.request.uid),
            ]
        )

        return http.request.render('sport_club_manager.website_info_club', {
            'memberships': memberships,
        })



    # @http.route('%s/session_ % _URL_ROOTlist/', auth='public', website=True)
    # def session_list(self, **kw):
    #     sessions = http.request.env['sport_club_manager.session'].search([])
    #     return http.request.render('sport_club_manager.session_list', {
    #         'session': sessions
    #     })

    # @http.route('%s/<int:id> % _URL_ROOT/', auth='public', website=True)
    # def teacher(self, id):
    #     return '<h1>{} ({})</h1>'.format(id, type(id).__name__)

    # @http.route('%s/<model(" % _URL_ROOTsport_club_manager.session"):session>/', auth='public', website=True)
    # def session(self, session):
    #     return http.request.render('sport_club_manager.session', {
    #         'session': session
    #     })

