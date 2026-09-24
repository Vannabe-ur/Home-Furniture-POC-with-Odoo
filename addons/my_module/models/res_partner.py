from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    ticket_ids = fields.One2many('design.request', 'partner_id', string="Design Requests")
    ticket_count = fields.Integer(string="Design Request Count", compute='_compute_ticket_count')

    def _compute_ticket_count(self):
        for partner in self:
            partner.ticket_count = len(partner.ticket_ids)

    def action_view_tickets(self):
        self.ensure_one()
        return {
            'name': 'Design Requests',
            'type': 'ir.actions.act_window',
            'res_model': 'design.request',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }
