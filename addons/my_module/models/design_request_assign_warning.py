from odoo import fields, models


class ClientTicketAssignWarning(models.TransientModel):
    _name = 'design.request.assign.warning'
    _description = 'Design Request Assignment Warning'

    ticket_id = fields.Many2one('design.request', required=True, readonly=True)
    message = fields.Text(readonly=True)

    def action_assign_anyway(self):
        self.ensure_one()
        self.ticket_id.with_context(skip_assignment_warning=True).action_assign()
        return {'type': 'ir.actions.act_window_close'}

    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}
