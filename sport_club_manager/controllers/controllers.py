# -*- coding: utf-8 -*-

from odoo.api import Environment
from odoo import http
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo import SUPERUSER_ID
from odoo import registry as registry_get

_URL_ROOT = '/sport'

class SportClubManager(AuthSignupHome):

    # TODO I think this part can be deleted (redirection implemented in medel res.users)
    # @http.route()
    # def web_login(self, *args, **kw):
    #     print('\nweb_login', args, kw, '\n')
    #     response = super(SportClubManager, self).web_login(*args, **kw)

    #     user_id = http.request.session.uid
    #     if not user_id:
    #         return response

    #     group_admin_id = http.request.env.ref('base.group_system').id
    #     group_manager_id = http.request.env.ref('sport_club_manager.group_sport_club_manager_manager').id
    #     group_committee_id = http.request.env.ref('sport_club_manager.group_sport_club_manager_committee').id
    #     group_portal_id = http.request.env.ref('base.group_portal').id
    #     user_group_ids = http.request.env['res.users'].sudo().search_read([('id', '=', user_id),], ['groups_id'], limit=1)[0]['groups_id']
    #     if group_admin_id in user_group_ids:
    #         # http://localhost:8069/web#view_type=kanban&model=membership&menu_id=88&action=120
    #         import ipdb; ipdb.set_trace()
    #         #return http.redirect_with_hash(http.request.params.get('redirect'))
    #     elif group_manager_id in user_group_ids or group_committee_id in user_group_ids:
    #         import ipdb; ipdb.set_trace()
    #         #return http.redirect_with_hash(http.request.params.get('redirect'))
    #         # redirect to backend
    #     elif group_portal_id in user_group_ids:
    #         import ipdb; ipdb.set_trace()
    #         # redirect to website welcome screen
    #         pass
    #     return response

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

    @http.route('%s/my/membership/accept' % _URL_ROOT, type='http', auth='public')
    def accept(self, db, token, action, id, **kwargs):
        registry = registry_get(db)
        with registry.cursor() as cr:
            env = Environment(cr, SUPERUSER_ID, {})
            membership = env['membership'].search([('token', '=', token), ('user_response', '!=', 'accepted')])
            if membership:
                membership.do_accept()
        return self.view(db, token, action, id, view='form')

    @http.route('%s/my/membership/decline' % _URL_ROOT, type='http', auth='public')#, auth="calendar")
    def declined(self, db, token, action, id):
        registry = registry_get(db)
        with registry.cursor() as cr:
            env = Environment(cr, SUPERUSER_ID, {})
            membership = env['membership'].search([('token', '=', token), ('user_response', '!=', 'declined')])
            if membership:
                membership.do_decline()
        return self.view(db, token, action, id, view='form')


    @http.route('%s/my/membership/view' % _URL_ROOT, type='http', auth='public')#auth="calendar")
    def view(self, db, token, action, id, view='calendar'):
        registry = registry_get(db)
        with registry.cursor() as cr:
            # Since we are in auth=none, create an env with SUPERUSER_ID
            env = Environment(cr, SUPERUSER_ID, {})
            membership = env['membership'].search([('token', '=', token),])
            if not membership:
                return http.request.not_found()
            # timezone = membership.partner_id.tz
            # lang = membership.partner_id.lang or 'en_US'
            # event = env['calendar.event'].with_context(tz=timezone, lang=lang).browse(int(id))

            # If user is internal and logged, redirect to form view of event
            # otherwise, display the simplifyed web page with event informations
            # if http.request.session.uid and http.request.env['res.users'].browse(http.request.session.uid).user_has_groups('base.group_user'):
            #     return werkzeug.utils.redirect('/web?db=%s#id=%s&view_type=form&model=calendar.event' % (db, id))

            # NOTE : we don't use http.request.render() since:
            # - we need a template rendering which is not lazy, to render before cursor closing
            # - we need to display the template in the language of the user (not possible with
            #   http.request.render())
            # return http.request.render('sport_club_manager.website_info_club', {
            #     'memberships': memberships,
            # })
            response_content = env['ir.ui.view'].render_template(
                'sport_club_manager.membership_affiliation_page_anonymous', {
                    'membership': membership,
                })
            return http.request.make_response(response_content, headers=[('Content-Type', 'text/html')])
