from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    current_membership_id = fields.Many2one('membership', compute='_compute_current_membership_id',
        string='Current Membership')
    current_membership_payment_date = fields.Date('Current Membership Payment Date',
        related='current_membership_id.payment_date')
    current_membership_payment_date_str = fields.Char('Current Membership Payment Date',
        related='current_membership_id.payment_date_str')

    def _compute_current_membership_id(self):
        for record in self:
            record.current_membership_id  = record.membership_ids.filtered(lambda m: m.period_id.current)
