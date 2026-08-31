from odoo import models, fields, api
from odoo.exceptions import UserError

class ClientTicket(models.Model):
    _name = 'client.ticket'
    _rec_name = 'ticket_ref'
    _description = 'Client Service Ticket'
    _inherit = ['mail.thread']

    ticket_ref = fields.Char(string="Ticket Reference", readonly=True, copy=False, default='New')

    # Priority
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Urgent'),
    ], string="Priority", default='0')

    # State workflow
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('closed', 'Closed'),
        ('cancel', 'Cancelled'),
    ], string="Status", default='draft', required=True)

    # --- Left column ---
    partner_id = fields.Many2one('res.partner', string="Customer", required=True)
    request_type = fields.Selection([
        ('interior', 'Interior Design'),
        ('exterior', 'Exterior Design'),
        ('outdoor', 'Outdoor Design'),
    ], string="Request Type", required=True)
    product_type = fields.Selection([
        ('kitchen', 'Kitchen Area'),
        ('bathroom', 'Bathroom Area'),
        ('livingroom', 'Livingroom Area'),
        ('pool', 'Swimming pool'),
        ('garden', 'Backyard garden'),
        ('parking', 'Parking lot Area'),
    ], string="House / Product Type")

    # Standalone stored fields (editable by user)
    phone = fields.Char(string="Phone")
    email = fields.Char(string="Email")

    project_id = fields.Many2one('project.project', string="Project")

    # --- Auto-fill logic when partner_id changes ---
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.phone = self.partner_id.phone
            self.email = self.partner_id.email
        if self.partner_id and self.partner_id.user_id:
            self.design_manager_id = self.partner_id.user_id

    # Right Column
    requester_id = fields.Many2one(
        'res.users', string="Requester",
        default=lambda self: self.env.user, required=True,
    )
    design_manager_id = fields.Many2one('res.users', string="Design Manager")
    designer_id = fields.Many2one('res.users', string="Designer")
    require_date = fields.Datetime(string="Require Date")
    is_overdue = fields.Boolean(string="Overdue", compute='_compute_is_overdue', store=True)
    bom_id = fields.Many2one('mrp.production', string="Related BoM")

    # Tabs filed
    description = fields.Text(string="Description")
    phis_ref = fields.Text(string="PHIS Reference")
    aihouse_ref = fields.Text(string="AIHouse Reference")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ticket_ref', 'New') == 'New':
                vals['ticket_ref'] = self.env['ir.sequence'].next_by_code('client.ticket') or 'New'
        return super().create(vals_list)

    @api.depends('require_date', 'state')
    def _compute_is_overdue(self):
        today = fields.Date.today()

        for rec in self:
            if rec.require_date:
                due_date = fields.Datetime.to_datetime(
                    rec.require_date
                ).date()

                rec.is_overdue = (
                    due_date < today
                    and rec.state not in ('completed', 'closed', 'cancel')
                )
            else:
                rec.is_overdue = False

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        # If this client has a linked user, default the ticket to them
        if self.partner_id and self.partner_id.user_id:
            self.design_manager_id = self.partner_id.user_id

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_submitted(self):
        for rec in self:
            if not rec.design_manager_id:
                raise UserError(
                    "Please select a Design Manager before submitting the ticket"
                )
            
            rec.state = 'submitted'
            rec.message_post(
                body=f"Ticket submitted for design Manager {rec.design_manager_id.name}"
            )

    def action_approved(self):
        for rec in self:
            if not rec.designer_id:
                raise UserError(
                    "Please select a Designer before approving the ticket."
                )
            approval_datetime = fields.Datetime.now()
            rec.state = 'approved'

            approval_time = fields.Datetime.context_timestamp(
                rec, approval_datetime
            ).strftime('%Y-%m-d %H:%M:%S')
            rec.state = 'approved'

            rec.message_post(
                body_html=(
                    f"<p>Ticket approved and assigned to: </p>"
                     f"<p>Designer: {rec.designer_id.name} </p>"
                     f"<p>Approved at: {approval_time} | By: {rec.design_manager_id.name} </p>"
                ),
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )


    def action_assign(self):
        for rec in self:
            rec.state = 'assigned'
            rec._send_assignment_email()

    def action_start(self):
        for rec in self:
            rec.state = 'in_progress'

    def action_complete(self):
        for rec in self:
            if not rec.bom_id:
                raise UserError(
                    "Please complete the related BoM reference."
                )
            
            rec.state = 'completed'

    def action_close(self):
        for rec in self:
            rec.state = 'closed'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def _send_ticket_email(self, subject, body_html, log_note=None):
        self.ensure_one()
        if not self.design_manager_id.email:
            return
        self.env['mail.mail'].create({
            'subject': subject,
            'body_html': body_html,
            'email_to': self.design_manager_id.email,
        }).send()
        if log_note:
            self.message_post(body=log_note)

    def _send_assignment_email(self):
        self.ensure_one()
        self._send_ticket_email(
            subject=f"New ticket assigned: {self.ticket_ref}",
            body_html=(
                f"<p>You have been assigned ticket "
                f"<strong>{self.ticket_ref}</strong></p>"
                f"<p>Customer: {self.partner_id.name}</p>"
                f"<p>Due: {self.require_date or 'Not set'}</p>"
            ),
            log_note=f"Assignment email sent to {self.design_manager_id.name} ({self.design_manager_id.email}).",
        )

    @api.model
    def _cron_notify_overdue(self):
        overdue = self.search([('is_overdue', '=', True)])
        for ticket in overdue:
            ticket.message_post(
                body=f"This ticket is overdue (due {ticket.require_date})."
            )

    @api.model
    def _cron_email_assigned_overdue(self):
        overdue = self.search([
            ('is_overdue', '=', True),
            ('design_manager_id', '!=', False),
        ])
        for ticket in overdue:
            ticket._send_ticket_email(
                subject=f"Overdue: {ticket.ticket_ref}",
                body_html=(
                    f"<p>Ticket <strong>{ticket.ticket_ref}</strong> assigned to you is overdue "
                    f"(due {ticket.require_date}).</p>"
                    f"<p>Client: {ticket.partner_id.name}</p>"
                ),
                log_note=f"Overdue reminder emailed to {ticket.design_manager_id.name} ({ticket.design_manager_id.email}).",
            )