# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tests.common import Form


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    membership_ids = fields.One2many('membership', 'invoice_line_id', 'Memberships',
        inverse='_inverse_membership_ids')

    @api.constrains('membership_ids', 'quantity')
    def _check_quantity_membership_ids(self):
        """ Checks that the number of memberships matches the quantity.

        :return: None
        """
        for move_line in self:
            if move_line.product_id.membership_ok and len(move_line.membership_ids) != move_line.quantity:
                    raise ValidationError(_("On the invoice line, the quantity does not match the number of " \
                        "memberships. Please change it accordingly."))

    def remove_memberships(self, memberships=None):
        """ Remove membership(s) of current account move line.

        :param memberships: membership record(s) to remove from their related account move line.
            If None (by default), remove all memberships of current aml

        :return: None
        """
        for move_line in self:
            if memberships is None:
                _memberships = move_line.membership_ids
            _memberships = memberships & move_line.membership_ids
            if not _memberships:
                continue

            if move_line.move_id.state == 'posted':
                raise UserError(_("You cannot remove membership(s) because the invoice '%s' has been posted. " \
                    "Please reset it to draft first.") % move_line.move_id.name)
            # all memberships of aml must be removed: delete line itself
            elif _memberships == move_line.membership_ids:
                # We need to remove the invoice line through a `Form`, otherwise the balance won't be updated
                # (debit != credit), leading to an error while checking the balance [1].
                # This method is much slower rather than performing an `unlink` operation: it is therefore working
                # as a workaround, until a better solution is found
                # [1] https://github.com/odoo/odoo/blob/66a1e96f88/addons/account/models/account_move.py#L2022-L2023
                invoice_form = Form(move_line.move_id)
                for i, _x in enumerate(move_line.move_id.line_ids.ids):
                    try:
                        if invoice_form.invoice_line_ids.edit(i).id ==  move_line.id:
                            invoice_form.invoice_line_ids.remove(i)
                            invoice_form.save()
                            break
                    except IndexError:
                        break
            else:
                move_line.write({'membership_ids': [(3, m_id) for m_id in _memberships.ids]})

    def _inverse_membership_ids(self):
        for move_line in self:
            # See comments above (in method `remove_memberships`) explaining the usage of the `Form`
            invoice_form = Form(move_line.move_id)
            for i, _ in enumerate(move_line.move_id.line_ids.ids):
                try:
                    if invoice_form.invoice_line_ids.edit(i).id ==  move_line.id:
                        with invoice_form.invoice_line_ids.edit(i) as move_line_form:
                            move_line_form.quantity = len(move_line.membership_ids)
                        invoice_form.save()
                        break
                except IndexError:
                    break
