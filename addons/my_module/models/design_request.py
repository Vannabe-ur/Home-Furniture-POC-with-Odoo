from datetime import timedelta, timezone

from odoo import models, fields, api
from odoo.exceptions import UserError

DESIGN_AREA_SELECTION = [
    ('living_room', 'Living Room'),
    ('bedroom', 'Bedroom'),
    ('kitchen', 'Kitchen'),
    ('bathroom', 'Bathroom'),
    ('dining_room', 'Dining Room'),
    ('home_office', 'Home Office'),
    ('facade', 'Facade'),
    ('entrance', 'Entrance'),
    ('balcony_terrace', 'Balcony / Terrace'),
    ('parking_area', 'Parking Area'),
    ('backyard_garden', 'Backyard / Garden'),
    ('swimming_pool', 'Swimming Pool'),
    ('patio_outdoor_living', 'Patio / Outdoor Living Area'),
    ('entrance_foyer', 'Entrance / Foyer'),
    ('building_facade', 'Building Facade'),
    ('main_entrance', 'Main Entrance'),
    ('rooftop', 'Rooftop'),
    ('exterior_walls', 'Exterior Walls'),
    ('patio', 'Patio'),
    ('outdoor_living_area', 'Outdoor Living Area'),
    ('outdoor_dining_area', 'Outdoor Dining Area'),
    ('outdoor_kitchen', 'Outdoor Kitchen'),
    ('landscape_area', 'Landscape Area'),
]

INTERIOR_DESIGN_AREA_SELECTION = [
    ('living_room', 'Living Room'),
    ('bedroom', 'Bedroom'),
    ('kitchen', 'Kitchen'),
    ('dining_room', 'Dining Room'),
    ('bathroom', 'Bathroom'),
    ('home_office', 'Home Office'),
    ('entrance_foyer', 'Entrance / Foyer'),
]

EXTERIOR_DESIGN_AREA_SELECTION = [
    ('building_facade', 'Building Facade'),
    ('main_entrance', 'Main Entrance'),
    ('balcony_terrace', 'Balcony / Terrace'),
    ('rooftop', 'Rooftop'),
    ('exterior_walls', 'Exterior Walls'),
    ('parking_area', 'Parking Area'),
]

OUTDOOR_DESIGN_AREA_SELECTION = [
    ('backyard_garden', 'Backyard / Garden'),
    ('swimming_pool', 'Swimming Pool'),
    ('patio', 'Patio'),
    ('outdoor_living_area', 'Outdoor Living Area'),
    ('outdoor_dining_area', 'Outdoor Dining Area'),
    ('outdoor_kitchen', 'Outdoor Kitchen'),
    ('landscape_area', 'Landscape Area'),
]

LEGACY_DESIGN_AREA_MAP = {
    'livingroom': 'living_room',
    'pool': 'swimming_pool',
    'garden': 'backyard_garden',
    'parking': 'parking_area',
    'entrance': 'entrance_foyer',
    'facade': 'building_facade',
    'patio_outdoor_living': 'outdoor_living_area',
}

class DesignRequest(models.Model):
    _name = 'design.request'
    # Keep the existing PostgreSQL table so a module upgrade can retain
    # existing Design Request records while the Odoo technical model name changes.
    _table = 'client_ticket'
    _rec_name = 'ticket_ref'
    _description = 'Design Request'
    _inherit = ['mail.thread']

    ticket_ref = fields.Char(string="Design Request ID", readonly=True, copy=False, default='New')

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
    # Kept as a storage alias so existing records and integrations survive the
    # field rename. New screens and code use design_area.
    product_type = fields.Selection(
        DESIGN_AREA_SELECTION + [
            ('livingroom', 'Living Room Area'),
            ('pool', 'Swimming pool'),
            ('garden', 'Backyard garden'),
            ('parking', 'Parking lot Area'),
        ], string="Legacy Design Area", copy=True,
    )
    design_area = fields.Selection(
        DESIGN_AREA_SELECTION,
        string="Design Area",
    )
    interior_design_area = fields.Selection(
        INTERIOR_DESIGN_AREA_SELECTION,
        string='Interior Design Area',
        compute='_compute_category_design_areas',
        inverse='_inverse_interior_design_area',
    )
    exterior_design_area = fields.Selection(
        EXTERIOR_DESIGN_AREA_SELECTION,
        string='Exterior Design Area',
        compute='_compute_category_design_areas',
        inverse='_inverse_exterior_design_area',
    )
    outdoor_design_area = fields.Selection(
        OUTDOOR_DESIGN_AREA_SELECTION,
        string='Outdoor Design Area',
        compute='_compute_category_design_areas',
        inverse='_inverse_outdoor_design_area',
    )
    @api.depends('request_type', 'design_area')
    def _compute_category_design_areas(self):
        for rec in self:
            rec.interior_design_area = rec.design_area if rec.request_type == 'interior' else False
            rec.exterior_design_area = rec.design_area if rec.request_type == 'exterior' else False
            rec.outdoor_design_area = rec.design_area if rec.request_type == 'outdoor' else False

    def _inverse_interior_design_area(self):
        for rec in self:
            rec.design_area = rec.interior_design_area

    def _inverse_exterior_design_area(self):
        for rec in self:
            rec.design_area = rec.exterior_design_area

    def _inverse_outdoor_design_area(self):
        for rec in self:
            rec.design_area = rec.outdoor_design_area

    @api.onchange('request_type')
    def _onchange_request_type(self):
        area_types = {
            'interior': {
                'living_room', 'bedroom', 'kitchen', 'bathroom',
                'dining_room', 'home_office', 'entrance_foyer',
            },
            'exterior': {
                'building_facade', 'main_entrance', 'balcony_terrace',
                'rooftop', 'exterior_walls', 'parking_area',
            },
            'outdoor': {
                'backyard_garden', 'swimming_pool', 'patio',
                'outdoor_living_area', 'outdoor_dining_area',
                'outdoor_kitchen', 'landscape_area',
            },
        }
        if self.design_area and self.design_area not in area_types.get(self.request_type, set()):
            self.design_area = False

    # Standalone stored fields (editable by user)
    phone = fields.Char(string="Phone")
    email = fields.Char(string="Email")

    project_id = fields.Many2one('project.project', string="Project")
    project_task_id = fields.Many2one(
        'project.task', string="Project Task", readonly=True, copy=False,
    )
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
    is_overdue = fields.Boolean(string="Overdue", compute='_compute_is_overdue')
    boq_id = fields.Many2one(
        'client.bill_of_quantity', string="Related BoQ", ondelete='restrict',
        domain="[('request_id', '=', id)]",
    )
    boq_ids = fields.One2many(
        'client.bill_of_quantity', 'request_id', string="BoQs"
    )
    boq_count = fields.Integer(string="BoQ Count", compute='_compute_boq_count')
    sale_order_count = fields.Integer(string="Sales", compute='_compute_sale_order_count')
    project_task_count = fields.Integer(
        string="Project Task Count", compute='_compute_project_task_count'
    )

    # Tabs field
    description = fields.Text(string="Description")
    phis_ref = fields.Text(string="PHIS Reference")
    aihouse_ref = fields.Text(string="AIHouse Reference")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ticket_ref', 'New') == 'New':
                vals['ticket_ref'] = self.env['ir.sequence'].next_by_code('design.request') or 'New'
            if vals.get('design_area'):
                vals['product_type'] = vals['design_area']
        return super().create(vals_list)

    def _compute_boq_count(self):
        for ticket in self:
            ticket.boq_count = len(ticket.boq_ids)

    def _compute_sale_order_count(self):
        sale_order_model = self.env['sale.order']
        for ticket in self:
            ticket.sale_order_count = sale_order_model.search_count([
                ('client_ticket_id', '=', ticket.id),
            ])

    @api.depends('project_task_id')
    def _compute_project_task_count(self):
        for ticket in self:
            ticket.project_task_count = 1 if ticket.project_task_id else 0

    def action_view_boqs(self):
        self.ensure_one()
        return {
            'name': 'BoQs',
            'type': 'ir.actions.act_window',
            'res_model': 'client.bill_of_quantity',
            'view_mode': 'list,form',
            'domain': [('request_id', '=', self.id)],
            'context': {'default_request_id': self.id},
        }

    def action_view_sale_orders(self):
        self.ensure_one()
        return {
            'name': 'Sales Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('client_ticket_id', '=', self.id)],
            'context': {'default_client_ticket_id': self.id},
        }

    def action_view_project_task(self):
        self.ensure_one()
        if not self.project_task_id:
            return False
        return {
            'name': 'Project Task',
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_mode': 'form',
            'res_id': self.project_task_id.id,
        }

    def write(self, vals):
        if any(ticket.state in ('closed', 'cancel') for ticket in self):
            raise UserError(
                "Closed or cancelled design requests are locked and cannot be edited."
            )
        if vals.get('design_area'):
            vals = dict(vals, product_type=vals['design_area'])
        return super().write(vals)

    @api.depends('require_date', 'state')
    def _compute_is_overdue(self):
        for rec in self:
            rec.is_overdue = rec._is_overdue_today()

    def _is_overdue_today(self):
        self.ensure_one()
        if not self.require_date or self.state in ('completed', 'closed', 'cancel'):
            return False

        # Compare the complete deadline, not only its calendar date. This
        # makes a request overdue immediately after its required time passes.
        require_datetime = fields.Datetime.to_datetime(self.require_date)
        return require_datetime < fields.Datetime.now()

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if not self.partner_id:
            self.phone = False
            self.email = False
            return

        self.phone = self.partner_id.phone
        self.email = self.partner_id.email

    def action_reset_draft(self):
        for rec in self:
            if rec.state in ('closed', 'cancel'):
                raise UserError(
                    "Closed or cancelled design requests cannot be reset to draft."
                )
            rec.state = 'draft'

    def action_submitted(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError("Only draft design requests can be submitted.")
            if not rec.design_manager_id:
                raise UserError(
                    "Please select a Design Manager before submitting the design request."
                )

            rec.write({
                'state': 'submitted',
                'submitted_at': fields.Datetime.now(),
                'submitted_by': self.env.user.id,
            })
            rec._post_template_to_chatter(
                'my_module.mail_template_ticket_submitted'
            )

    def action_approved(self):
        for rec in self:
            if rec.state != 'submitted':
                raise UserError("Only submitted design requests can be approved.")
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
                raise UserError("Only approved design requests can be assigned.")
            if not rec.designer_id:
                raise UserError(
                    "Please select a Designer before assigning the design request."
                )
            project = rec.project_id
            if not project:
                project_xmlids = {
                    'interior': 'my_module.project_interior_design',
                    'exterior': 'my_module.project_exterior_design',
                    'outdoor': 'my_module.project_outdoor_design',
                }
                project = self.env.ref(
                    project_xmlids.get(rec.request_type), raise_if_not_found=False
                ) if rec.request_type else self.env['project.project'].browse()
            if not project:
                raise UserError(
                    "Please select a Project for this design request before assignment."
                )
            if not self.env.context.get('skip_assignment_warning'):
                required_datetime = fields.Datetime.to_datetime(rec.require_date)
                required_local_datetime = fields.Datetime.context_timestamp(
                    rec, required_datetime
                )
                local_day_start = required_local_datetime.replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                local_day_end = local_day_start + timedelta(days=1)
                utc_day_start = local_day_start.astimezone(timezone.utc).replace(
                    tzinfo=None
                )
                utc_day_end = local_day_end.astimezone(timezone.utc).replace(
                    tzinfo=None
                )
                conflicting_requests = self.search([
                    ('id', '!=', rec.id),
                    ('designer_id', '=', rec.designer_id.id),
                    ('require_date', '>=', fields.Datetime.to_string(utc_day_start)),
                    ('require_date', '<', fields.Datetime.to_string(utc_day_end)),
                    ('state', 'in', ('approved', 'assigned', 'in_progress')),
                ]) if rec.require_date else self.browse()
                if conflicting_requests:
                    conflict_text = ', '.join(
                        f"{request.ticket_ref} ({request.partner_id.name})"
                        for request in conflicting_requests
                    )
                    wizard = self.env['design.request.assign.warning'].create({
                        'ticket_id': rec.id,
                        'message': (
                            f"Designer {rec.designer_id.name} already has another "
                            "scheduled request on the same day.\n\n"
                            f"Conflicting Design Request: {conflict_text}\n\n"
                            "Please check with the designer first."
                        ),
                    })
                    return {
                        'type': 'ir.actions.act_window',
                        'name': 'Assignment Warning',
                        'res_model': 'design.request.assign.warning',
                        'view_mode': 'form',
                        'res_id': wizard.id,
                        'target': 'new',
                    }
            rec.write({'project_id': project.id})
            rec._action_assign()

    def _action_assign(self):
        for rec in self:
            design_area = dict(DESIGN_AREA_SELECTION).get(
                rec.design_area, rec.design_area or 'Design Area'
            )
            task = rec.project_task_id
            new_stage = self.env['project.task.type'].search([
                ('project_ids', 'in', rec.project_id.id),
                ('name', '=', 'New'),
            ], limit=1)
            if not task:
                task_values = {
                    'name': f"{rec.ticket_ref} - {design_area}",
                    'project_id': rec.project_id.id,
                    'user_ids': [(6, 0, [rec.designer_id.id])],
                    'partner_id': rec.partner_id.id,
                    'description': rec.description or False,
                }
                if new_stage:
                    task_values['stage_id'] = new_stage.id
                task = self.env['project.task'].create(task_values)
            rec.write({
                'state': 'assigned',
                'assigned_at': fields.Datetime.now(),
                'assigned_by': self.env.user.id,
                'project_task_id': task.id,
            })
            rec._send_assignment_email()

    def action_start(self):
        for rec in self:
            if rec.state != 'assigned':
                raise UserError("Only assigned design requests can be started.")
            rec.write({
                'state': 'in_progress',
                'started_at': fields.Datetime.now(),
                'started_by': self.env.user.id,
            })
            in_progress_stage = self.env['project.task.type'].search([
                ('project_ids', 'in', rec.project_id.id),
                ('name', '=', 'In Progress'),
            ], limit=1)
            if rec.project_task_id and in_progress_stage:
                rec.project_task_id.write({'stage_id': in_progress_stage.id})

    def action_complete(self):
        for rec in self:
            if rec.state != 'in_progress':
                raise UserError("Only design requests in progress can be completed.")
            if not rec.boq_id:
                raise UserError(
                    "Please select a related BoQ before completing the design request."
                )
            if rec.boq_id.state not in ('approved', 'done'):
                raise UserError(
                    "The related BoQ must be Approved or Done before completing the design request."
                )
            
            rec.write({
                'state': 'completed',
                'completed_at': fields.Datetime.now(),
                'completed_by': self.env.user.id,
            })
            done_stage = self.env['project.task.type'].search([
                ('project_ids', 'in', rec.project_id.id),
                ('name', '=', 'Done'),
            ], limit=1)
            if rec.project_task_id and done_stage:
                rec.project_task_id.write({'stage_id': done_stage.id})
            rec._post_template_to_chatter(
                'my_module.mail_template_ticket_completed'
            )

    def action_close(self):
        for rec in self:
            if rec.state != 'completed':
                raise UserError("Only completed design requests can be closed.")
            rec.write({
                'state': 'closed',
                'closed_at': fields.Datetime.now(),
                'closed_by': self.env.user.id,
            })

    def action_cancel(self):
        for rec in self:
            if rec.state in ('closed', 'cancel'):
                raise UserError("This design request cannot be cancelled.")
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
            raise_exception=True,
            email_values={
                'email_to': recipient.email,
                'email_from': (
                    self.env.company.email_formatted
                    or self.env.user.email_formatted
                    or ''
                ),
            },
        )

    def _send_assignment_email(self):
        self.ensure_one()
        self._post_template_to_chatter(
            'my_module.mail_template_ticket_assigned'
        )

    def _post_template_to_chatter(self, template_xmlid):
        self.ensure_one()
        template = self.env.ref(
            template_xmlid
        ).sudo()
        rendered_body = template._render_field(
            'body_html', self.ids, options={'post_process': True}
        ).get(self.id, '')
        rendered_subject = template._render_field(
            'subject', self.ids
        ).get(self.id, '')
        self.message_post(
            body=rendered_body,
            subject=rendered_subject or False,
            message_type='email',
            subtype_xmlid='mail.mt_comment',
            body_is_html=True,
        )

    @api.model
    def _cron_notify_overdue(self):
        candidates = self.search([
            ('require_date', '!=', False),
            ('state', 'not in', ('completed', 'closed', 'cancel')),
        ])
        overdue = candidates.filtered(lambda ticket: ticket._is_overdue_today())
        for ticket in overdue:
            ticket.message_post(
                body=f"This design request is overdue (due {ticket.require_date})."
            )

    @api.model
    def _cron_email_assigned_overdue(self):
        candidates = self.search([
            ('require_date', '!=', False),
            ('design_manager_id', '!=', False),
            ('state', 'not in', ('completed', 'closed', 'cancel')),
        ])
        overdue = candidates.filtered(lambda ticket: ticket._is_overdue_today())
        for ticket in overdue:
            ticket._send_template_email(
                'my_module.mail_template_ticket_overdue',
                ticket.design_manager_id,
                f"Overdue reminder emailed to {ticket.design_manager_id.name}.",
            )

    @api.model
    def _cron_email_deadline_reminders(self):
        reminder_date = fields.Date.context_today(self) + timedelta(days=1)
        tickets = self.search([
            ('require_date', '!=', False),
            ('state', 'not in', ('completed', 'closed', 'cancel')),
        ])
        for ticket in tickets:
            require_datetime = fields.Datetime.to_datetime(ticket.require_date)
            require_date_local = fields.Datetime.context_timestamp(
                ticket, require_datetime
            ).date()
            if require_date_local != reminder_date:
                continue

            recipients = {
                email for email in (
                    ticket.design_manager_id.email,
                    ticket.designer_id.email,
                ) if email
            }
            if not recipients:
                ticket.message_post(
                    body='Deadline reminder was not emailed: no manager or designer email was found.'
                )
                continue

            template = self.env.ref(
                'my_module.mail_template_ticket_deadline_reminder'
            ).sudo()
            template.send_mail(
                ticket.id,
                force_send=True,
                raise_exception=True,
                email_values={
                    'email_to': ','.join(sorted(recipients)),
                    'email_from': (
                        ticket.env.company.email_formatted
                        or ticket.env.user.email_formatted
                        or ''
                    ),
                },
            )
