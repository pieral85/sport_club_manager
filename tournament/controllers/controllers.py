# -*- coding: utf-8 -*-
# from odoo import http


# class Tournament(http.Controller):
#     @http.route('/tournament/tournament', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tournament/tournament/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('tournament.listing', {
#             'root': '/tournament/tournament',
#             'objects': http.request.env['tournament.tournament'].search([]),
#         })

#     @http.route('/tournament/tournament/objects/<model("tournament.tournament"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tournament.object', {
#             'object': obj
#         })
