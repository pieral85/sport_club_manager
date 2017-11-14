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

class Sport(AuthSignupHome): # http.Controller):
    # @http.route('/sport/sport/', auth='public', website=True)
    # def index(self, **kw):
    #     return "Hello, world"

    @http.route('/sport/period/', auth='public', website=True)
    def period(self, **kw):
        periods = http.request.env['period'].search(['|', ('active', '=', True), ('active', '=', False)])
        return http.request.render('sport_club_manager.website_period', {
            'periods': periods,
        })

    @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        return super(Sport, self).web_auth_signup(*args, **kw)

    @http.route('/web/reset_password', type='http', auth='public', website=True, sitemap=False)
    def web_auth_reset_password(self, *args, **kw):
        return super(Sport, self).web_auth_reset_password(*args, **kw)

    # @http.route('/sport/session_list/', auth='public', website=True)
    # def session_list(self, **kw):
    #     sessions = http.request.env['sport_club_manager.session'].search([])
    #     return http.request.render('sport_club_manager.session_list', {
    #         'session': sessions
    #     })

    # @http.route('/sport/<int:id>/', auth='public', website=True)
    # def teacher(self, id):
    #     return '<h1>{} ({})</h1>'.format(id, type(id).__name__)

    # @http.route('/sport/<model("sport_club_manager.session"):session>/', auth='public', website=True)
    # def session(self, session):
    #     return http.request.render('sport_club_manager.session', {
    #         'session': session
    #     })

