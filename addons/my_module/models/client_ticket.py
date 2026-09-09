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
    ], string="Status", default='draft', required=True, group_expand=True)

    submitted_at = fields.Datetime(string="Submitted At", readonly=True, copy=False)
    submitted_by = fields.Many2one('res.users', string="Submitted By", readonly=True, copy=False)
    approved_at = fields.Datetime(string="Approved At", readonly=True, copy=False)
    approved_by = fields.Many2one('res.users', string="Approved By", readonly=True, copy=False)
    assigned_at = fields.Datetime(string="Assigned At", readonly=True, copy=False)
    assigned_by = fields.Many2one('res.users', string="Assigned By", readonly=True, copy=False)
    started_at = fields.Datetime(string="Started At", readonly=True, copy=False)
    started_by = fields.Many2one('res.users', string="Started By", readonly=True, copy=False)
    completed_at = fields.Datetime(string="Completed At", readonly=True, copy=False)
    completed_by = fields.Many2one('res.users', string="Completed By", readonly=True, copy=False)
    closed_at = fields.Datetime(string="Closed At", readonly=True, copy=False)
    closed_by = fields.Many2one('res.users', string="Closed By", readonly=True, copy=False)
    cancelled_at = fields.Datetime(string="Cancelled At", readonly=True, copy=False)
    cancelled_by = fields.Many2one('res.users', string="Cancelled By", readonly=True, copy=False)

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
    max_budget = fields.Monetary(string="Max. Budget")
    currency_id = fields.Many2one(
        'res.currency', string="Currency",
        default=lambda self: self.env.company.currency_id, required=True,
    )

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

    # Tabs field
    description = fields.Text(string="Description")
    phis_ref = fields.Text(string="PHIS Reference")
    aihouse_ref = fields.Text(string="AIHouse Reference")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ticket_ref', 'New') == 'New':
                vals['ticket_ref'] = self.env['ir.sequence'].next_by_code('client.ticket') or 'New'
        return super().create(vals_list)

    def write(self, vals):
        if any(ticket.state == 'closed' for ticket in self):
            raise UserError("Closed tickets are locked and cannot be edited.")
        return super().write(vals)

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
        if not self.partner_id:
            self.phone = False
            self.email = False
            return

        self.phone = self.partner_id.phone
        self.email = self.partner_id.email

        # If this customer has a linked user, use them as the default manager.
        if self.partner_id.user_id:
            self.design_manager_id = self.partner_id.user_id

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_submitted(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError("Only draft tickets can be submitted.")
            if not rec.design_manager_id:
                raise UserError(
                    "Please select a Design Manager before submitting the ticket."
                )

            rec.write({
                'state': 'submitted',
                'submitted_at': fields.Datetime.now(),
                'submitted_by': self.env.user.id,
            })
            rec.message_post(
                body=f"Ticket submitted to Design Manager {rec.design_manager_id.name}."
            )
            rec._send_template_email(
                'my_module.mail_template_ticket_submitted',
                rec.design_manager_id,
                f"Notification email sent to Design Manager {rec.design_manager_id.name}.",
            )

    def action_approved(self):
        for rec in self:
            if rec.state != 'submitted':
                raise UserError("Only submitted tickets can be approved.")
            approval_datetime = fields.Datetime.now()
            rec.write({
                'state': 'approved',
                'approved_at': approval_datetime,
                'approved_by': self.env.user.id,
            })

            approval_time = fields.Datetime.context_timestamp(
                rec, approval_datetime
            ).strftime('%Y-%m-%d %H:%M:%S')

            rec.message_post(
                body=(
                    f"Ticket Approved at: {approval_time} | By: {self.env.user.name}"
                ),
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )
            
    def action_assign(self):
        for rec in self:
            if rec.state != 'approved':
                raise UserError("Only approved tickets can be assigned.")
            if not rec.designer_id:
                raise UserError(
                    "Please select a Designer before assigning the ticket."
                )
            rec.write({
                'state': 'assigned',
                'assigned_at': fields.Datetime.now(),
                'assigned_by': self.env.user.id,
            })
            rec._send_assignment_email()

    def action_start(self):
        for rec in self:
            if rec.state != 'assigned':
                raise UserError("Only assigned tickets can be started.")
            rec.write({
                'state': 'in_progress',
                'started_at': fields.Datetime.now(),
                'started_by': self.env.user.id,
            })

    def action_complete(self):
        for rec in self:
            if rec.state != 'in_progress':
                raise UserError("Only tickets in progress can be completed.")
            if not rec.bom_id:
                raise UserError(
                    "Please complete the related BoM reference."
                )
            
            rec.write({
                'state': 'completed',
                'completed_at': fields.Datetime.now(),
                'completed_by': self.env.user.id,
            })
            rec._send_template_email(
                'my_module.mail_template_ticket_completed',
                rec.design_manager_id,
                f"Completion email sent to Design Manager {rec.design_manager_id.name}.",
            )

    def action_close(self):
        for rec in self:
            if rec.state != 'completed':
                raise UserError("Only completed tickets can be closed.")
            rec.write({
                'state': 'closed',
                'closed_at': fields.Datetime.now(),
                'closed_by': self.env.user.id,
            })

    def action_cancel(self):
        for rec in self:
            if rec.state in ('closed', 'cancel'):
                raise UserError("This ticket cannot be cancelled.")
            rec.write({
                'state': 'cancel',
                'cancelled_at': fields.Datetime.now(),
                'cancelled_by': self.env.user.id,
            })

    def _send_template_email(self, template_xmlid, recipient, log_note=None):
        self.ensure_one()
        if not recipient or not recipient.email:
            if log_note:
                self.message_post(
                    body=f"{log_note} Email was not sent: no recipient email."
                )
            return
        template = self.env.ref(template_xmlid).sudo()
        template.send_mail(
            self.id,
            force_send=True,
            email_values={'email_to': recipient.email},
        )
        if log_note:
            self.message_post(body=log_note)

    def _send_assignment_email(self):
        self.ensure_one()
        self._send_template_email(
            'my_module.mail_template_ticket_assigned',
            self.designer_id,
            f"Assignment email sent to Designer {self.designer_id.name}.",
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
            ticket._send_template_email(
                'my_module.mail_template_ticket_overdue',
                ticket.design_manager_id,
                f"Overdue reminder emailed to {ticket.design_manager_id.name}.",
            )
