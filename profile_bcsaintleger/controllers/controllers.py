# # -*- coding: utf-8 -*-

from odoo.http import request, route, Controller


class WebsitePartnerPage(Controller):

    # TODO Set route in english + manage fr translation
    @route(['/infos-pratiques'], type='http', auth="public", website=True)
    def infos_pratiques(self, **post):
        sport_complex = request.env.ref('profile_bcsaintleger.saintleger_sports_complex')
        return request.render('profile_bcsaintleger.website_practical_information', {'sport_complex': sport_complex, 'partner': sport_complex,})
# TODO
# * Ajouter dans le folder 'profile_bcsaintleger' une adresse pour le complexe (xml)
# * Faire pointer la vue dessus
# * Mettre l'iframe dans un champ de ce contact et l'afficher dynamiquement dans la vue
# * Add Compte bancaire
#    (068-2280671-34)
#    IBAN: BE68 0682 2806 7134
#    BIC: GKCCBEBB
# Add facebook https://www.facebook.com/Badminton-Club-Saint-L%C3%A9ger-523719094305111

                # TODO
                #  * Add view in this folder
                #  * Add an xml-id to this view
                #  * Reference to this view with sth like 'return request.render("website_partner.partner_page", values)''

        # TODO Delete me
        # _, partner_id = unslug(partner_id)
        # if partner_id:
        #     partner_sudo = request.env['res.partner'].sudo().browse(partner_id)
        #     is_website_publisher = request.env['res.users'].has_group('website.group_website_publisher')
        #     if partner_sudo.exists() and (partner_sudo.website_published or is_website_publisher):
        #         values = {
        #             'main_object': partner_sudo,
        #             'partner': partner_sudo,
        #             'edit_page': False
        #         }
        #         return request.render("website_partner.partner_page", values)
        # return request.not_found()
