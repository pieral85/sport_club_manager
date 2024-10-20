import json

from odoo import fields, models
from odoo.tools.misc import get_lang


class Membership(models.Model):
    _inherit = 'membership'

    payment_date = fields.Date('Payment Date', compute='_compute_payment_date')
    payment_date_str = fields.Char('Payment Date (string representation)', compute='_compute_payment_date')

    def _compute_payment_date(self):
        # TODO Maybe use <AML>.membership_ids in order to easily fetch the relevent payment?
        for membership in self:
            if not membership.invoice_id:
                membership.payment_date = False
                membership.payment_date_str = ''
                continue

            # in case of multiple payments on the invoice, we want to take the latest payment date after which the sum
            # of what has been paid is higher than the membership due price
            payments_widget_vals = json.loads(membership.invoice_id.invoice_payments_widget)
            if not payments_widget_vals:
                membership.payment_date = False
                membership.payment_date_str = ''
                continue

            remaining_price = membership.price_due
            for content in payments_widget_vals['content']:
                remaining_price -= content['amount']
                if remaining_price <= 0:
                    membership.payment_date = fields.Date.to_date(content['date'])
                    date_format = get_lang(self.env, membership.member_id.lang).date_format
                    membership.payment_date_str = membership.payment_date.strftime(date_format)
