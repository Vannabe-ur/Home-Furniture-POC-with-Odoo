from odoo import models, fields, api

class ClientTicket(models.Model):
    _name = 'client.ticket'
    _description = 'Client Service Ticket'
    _inherit = ['mail.thread']

    ticket_ref = fields.Char(string="Reference", readonly=True, copy=False, default='New')
    name = fields.Char(string="Subject", required=True)
    description = fields.Text(string="Description")
    partner_id = fields.Many2one('res.partner', string="Client", required=True)
    assigned_to = fields.Many2one('res.users', string="Assigned To")
    date_due = fields.Datetime(string="Due Date")
    is_overdue = fields.Boolean(string="Overdue", compute='_compute_is_overdue', store=True)
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Urgent'),
    ], string="Priority", default='0')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted')
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
        ('done', 'Done'),
    ], string="Status", default='draft', required=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ticket_ref', 'New') == 'New':
                vals['ticket_ref'] = self.env['ir.sequence'].next_by_code('client.ticket') or 'New'
        return super().create(vals_list)

    @api.depends('date_due', 'state')
    def _compute_is_overdue(self):
        now = fields.Datetime.now()
        for rec in self:
            rec.is_overdue = bool(
                rec.date_due and rec.date_due < now and rec.state != 'done'
            )

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        # If this client has a linked user, default the ticket to them
        if self.partner_id and self.partner_id.user_id:
            self.assigned_to = self.partner_id.user_id

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_submitted(self):
        for rec in self:
            rec.state = 'submitted'

    def action_assign(self):
        for rec in self:
            rec.state = 'assigned'
            rec._send_assignment_email()

    def action_start(self):
        for rec in self:
            rec.state = 'in_progress'

    def action_complete(self):
        for rec in self:
            rec.state = 'completed'

    def action_done(self):
        for rec in self:
            rec.state = 'done'

    def _send_ticket_email(self, subject, body_html, log_note=None):
        self.ensure_one()
        if not self.assigned_to.email:
            return
        self.env['mail.mail'].create({
            'subject': subject,
            'body_html': body_html,
            'email_to': self.assigned_to.email,
        }).send()
        if log_note:
            self.message_post(body=log_note)

    def _send_assignment_email(self):
        self.ensure_one()
        self._send_ticket_email(
            subject=f"New ticket assigned: {self.ticket_ref} - {self.name}",
            body_html=(
                f"<p>You have been assigned ticket "
                f"<strong>{self.ticket_ref}</strong> (\"{self.name}\").</p>"
                f"<p>Client: {self.partner_id.name}</p>"
                f"<p>Due: {self.date_due or 'Not set'}</p>"
            ),
            log_note=f"Assignment email sent to {self.assigned_to.name} ({self.assigned_to.email}).",
        )

    @api.model
    def _cron_notify_overdue(self):
        overdue = self.search([('is_overdue', '=', True)])
        for ticket in overdue:
            ticket.message_post(
                body=f"This ticket is overdue (due {ticket.date_due})."
            )

    @api.model
    def _cron_email_assigned_overdue(self):
        overdue = self.search([
            ('is_overdue', '=', True),
            ('assigned_to', '!=', False),
        ])
        for ticket in overdue:
            ticket._send_ticket_email(
                subject=f"Overdue: {ticket.ticket_ref} - {ticket.name}",
                body_html=(
                    f"<p>Ticket <strong>{ticket.ticket_ref}</strong> "
                    f"(\"{ticket.name}\") assigned to you is overdue "
                    f"(due {ticket.date_due}).</p>"
                    f"<p>Client: {ticket.partner_id.name}</p>"
                ),
                log_note=f"Overdue reminder emailed to {ticket.assigned_to.name} ({ticket.assigned_to.email}).",
            )