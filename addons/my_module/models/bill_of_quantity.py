from odoo import api, fields, models
from odoo.exceptions import UserError


class BillOfQuantity(models.Model):
    _name = 'client.bill_of_quantity'
    _description = 'Bill of Quantity'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    name = fields.Char(string='BoQ ID', readonly=True, copy=False, default='New', tracking=True)
    request_id = fields.Many2one('client.ticket', string='Request ID', required=True, ondelete='restrict', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Customer', related='request_id.partner_id', store=True, readonly=True)
    phone = fields.Char(string='Phone', related='request_id.phone', readonly=True)
    email = fields.Char(string='Email', related='request_id.email', readonly=True)
    require_date = fields.Datetime(string='Required Date', related='request_id.require_date', readonly=True)
    unit_code = fields.Char(string='Unit Code')
    design_area = fields.Selection(related='request_id.design_area', string='Design Area', readonly=True)
    priority = fields.Selection(related='request_id.priority', string='Priority', readonly=True)
    version = fields.Integer(string='Version', default=1, required=True)
    revision_date = fields.Date(string='Revision Date', default=fields.Date.context_today, required=True)
    responsible_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user, required=True)
    design_manager_id = fields.Many2one('res.users', string='Design Manager', related='request_id.design_manager_id', store=True, readonly=True)
    max_budget = fields.Monetary(string='Max. Budget', related='request_id.max_budget', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id, required=True)
    attachment = fields.Binary(string='Attachment', attachment=True)
    attachment_filename = fields.Char(string='Attachment Filename')
    state = fields.Selection([('draft', 'Draft'), 
                              ('submitted', 'Submitted'), 
                              ('approved', 'Approved'),
                              ('done', 'Done'),
                              ('cancel', 'Cancelled')], 
                              string='Status', default='draft', required=True, tracking=True, group_expand=True)
    rejection_feedback = fields.Text(string='Rejection Feedback')
    approved_at = fields.Datetime(string='Approved On', readonly=True, copy=False)
    approved_by = fields.Many2one('res.users', string='Approved By', readonly=True, copy=False)
    rejected_at = fields.Datetime(string='Rejected On', readonly=True, copy=False)
    rejected_by = fields.Many2one('res.users', string='Rejected By', readonly=True, copy=False)
    
    line_ids = fields.One2many('client.bill_of_quantity.line', 'boq_id', string='BoQ Items', copy=True)
    total_cost = fields.Monetary(string='Total Estimate Cost', compute='_compute_totals', store=True)
    total_materials_cost = fields.Monetary(string='Total Materials Cost', compute='_compute_totals', store=True)
    total_service_cost = fields.Monetary(string='Total Service / Overhead Cost', compute='_compute_totals', store=True)
    total_labor_cost = fields.Monetary(string='Total Labor Cost', compute='_compute_totals', store=True)
    margin_cost = fields.Monetary(string='Margin Cost', compute='_compute_totals', store=True)
    margin = fields.Float(string='Margin (%)', default=0.0)
    history_ids = fields.One2many(
        'client.bill_of_quantity.history', 'boq_id', string='Audit History', readonly=True,
    )
    sale_order_ids = fields.One2many('sale.order', 'boq_id', string='Sale Quotations', readonly=True)
    sale_order_count = fields.Integer(string='Sales', compute='_compute_sale_order_count')

    @api.depends('line_ids.subtotal', 'line_ids.job_type', 'margin')
    def _compute_totals(self):
        for boq in self:
            lines = boq.line_ids
            boq.total_materials_cost = sum(lines.filtered(lambda line: line.job_type == 'material').mapped('subtotal'))
            boq.total_service_cost = sum(lines.filtered(lambda line: line.job_type == 'service').mapped('subtotal'))
            boq.total_labor_cost = sum(lines.filtered(lambda line: line.job_type == 'labor').mapped('subtotal'))
            base_total = (
                boq.total_materials_cost
                + boq.total_service_cost
                + boq.total_labor_cost
            )
            # The percentage widget stores 10% as 0.10, so margin is applied
            # as a markup on the combined material, service, and labor costs.
            boq.margin_cost = base_total * boq.margin
            boq.total_cost = base_total + boq.margin_cost

    def _compute_sale_order_count(self):
        for boq in self:
            boq.sale_order_count = len(boq.sale_order_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('client.bill_of_quantity') or 'New'
        records = super().create(vals_list)
        for boq in records:
            boq._record_history('created')
        return records

    def write(self, vals):
        locked_boqs = self.filtered(lambda boq: boq.state in ('done', 'cancel'))
        if locked_boqs:
            raise UserError(
                'A BoQ is locked after it is marked Done or Cancelled and cannot be modified.'
            )
        return super().write(vals)

    @api.onchange('request_id')
    def _onchange_request_id(self):
        if self.request_id:
            self.responsible_id = self.request_id.designer_id or self.env.user

    def action_submit(self):
        for boq in self:
            if boq.state != 'draft':
                raise UserError('Only draft BoQs can be submitted.')
            if not boq.line_ids:
                raise UserError('Add at least one BoQ item before submitting.')
            if not boq.design_manager_id:
                raise UserError('Please select a Design Manager before submitting the BoQ.')
            boq.write({'state': 'submitted'})
            boq._record_history('submitted')
            boq._post_template_to_chatter('my_module.mail_template_boq_submitted')

    def action_approve(self):
        for boq in self:
            if boq.state != 'submitted':
                raise UserError('Only submitted BoQs can be approved.')
            if boq.design_manager_id and self.env.user != boq.design_manager_id and not self.env.user.has_group('base.group_system'):
                raise UserError('Only the assigned Design Manager can approve this BoQ.')
            now = fields.Datetime.now()
            boq.write({
                'state': 'approved',
                'approved_at': now,
                'approved_by': self.env.user.id,
            })
            boq._record_history('approved')
            boq._post_template_to_chatter('my_module.mail_template_boq_approved')

    def action_reject(self):
        for boq in self:
            if boq.state != 'submitted':
                raise UserError('Only submitted BoQs can be rejected.')
            if boq.design_manager_id and self.env.user != boq.design_manager_id and not self.env.user.has_group('base.group_system'):
                raise UserError('Only the assigned Design Manager can reject this BoQ.')
            if not boq.rejection_feedback:
                raise UserError('Please enter rejection feedback before rejecting the BoQ.')
            now = fields.Datetime.now()
            new_version = boq.version + 1
            boq.write({
                'state': 'draft',
                'version': new_version,
                'revision_date': fields.Date.context_today(boq),
                'rejected_at': now,
                'rejected_by': self.env.user.id,
            })
            boq._record_history('rejected', boq.rejection_feedback)
            boq._post_template_to_chatter('my_module.mail_template_boq_rejected')

    def action_done(self):
        for boq in self:
            if boq.state != 'approved':
                raise UserError('Only approved BoQs can be marked done.')
            boq.write({'state': 'done'})
            boq._record_history('done')

    def action_cancel(self):
        for boq in self:
            if boq.state in ('done', 'cancel'):
                raise UserError('This BoQ cannot be cancelled.')
            boq.write({'state': 'cancel'})
            boq._record_history('cancelled')

    def action_reset_draft(self):
        for boq in self:
            if boq.state in ('done', 'cancel'):
                raise UserError('A Done or Cancelled BoQ cannot be reopened.')
            boq.write({'state': 'draft'})
            boq._record_history('reset')

    def action_view_request(self):
        self.ensure_one()
        return {
            'name': 'Design Request',
            'type': 'ir.actions.act_window',
            'res_model': 'client.ticket',
            'view_mode': 'form',
            'res_id': self.request_id.id,
        }

    def action_view_sale_orders(self):
        self.ensure_one()
        return {
            'name': 'Sales Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('boq_id', '=', self.id)],
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_boq_id': self.id,
            },
        }

    def action_create_sale_quotation(self):
        self.ensure_one()
        if self.state != 'done':
            raise UserError('A sale quotation can only be created when the BoQ is Done.')
        if not self.partner_id:
            raise UserError('Please select a customer before creating a sale quotation.')

        missing_product_lines = self.line_ids.filtered(lambda line: not line.product_id)
        if missing_product_lines:
            raise UserError(
                'Every BoQ item must have a product before creating a sale quotation.'
            )

        existing_order = self.sale_order_ids.filtered(
            lambda order: order.state in ('draft', 'sent')
        )[:1]
        if existing_order:
            order = existing_order
        else:
            order = self.env['sale.order'].create({
                'partner_id': self.partner_id.id,
                'origin': self.request_id.ticket_ref,
                'client_order_ref': self.name,
                'boq_id': self.id,
                'pricelist_id': self.partner_id.property_product_pricelist.id,
            })
            for line in self.line_ids:
                product = line.product_id
                uom = (
                    line.uom_id
                    or (product and product.uom_id)
                    or self.env.ref('uom.product_uom_unit', raise_if_not_found=False)
                )
                self.env['sale.order.line'].create({
                    'order_id': order.id,
                    'product_id': product.id or False,
                    'product_uom_id': uom.id if uom else False,
                    'product_uom_qty': line.quantity,
                    'price_unit': line.sale_price,
                    'name': line.description or (product.display_name if product else '/'),
                })


        margin_product = self.env['product.product'].sudo().search(
            [('default_code', '=', 'BOQ-MARGIN')], limit=1
        )
        if self.margin_cost and not margin_product:
            margin_template = self.env['product.template'].sudo().create({
                'name': 'BoQ Margin',
                'default_code': 'BOQ-MARGIN',
                'detailed_type': 'service',
                'sale_ok': True,
                'purchase_ok': False,
            })
            margin_product = margin_template.product_variant_id

        margin_lines = order.order_line.filtered(
            lambda line: line.product_id == margin_product
            and (line.name or '').startswith('BoQ Margin (')
        ) if margin_product else self.env['sale.order.line']
        if self.margin_cost:
            unit_uom = self.env.ref(
                'uom.product_uom_unit', raise_if_not_found=False
            )
            margin_values = {
                'product_id': margin_product.id,
                'product_uom_id': unit_uom.id if unit_uom else False,
                'product_uom_qty': 1.0,
                'price_unit': self.margin_cost,
                'name': f'BoQ Margin ({self.margin:.2%})',
            }
            if margin_lines:
                margin_lines[:1].write(margin_values)
                margin_lines[1:].unlink()
            else:
                self.env['sale.order.line'].create({
                    'order_id': order.id,
                    **margin_values,
                })
        elif margin_lines:
            margin_lines.unlink()

        return {
            'name': 'Sale Quotation',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': order.id,
        }

    def _record_history(self, event, note=False):
        self.ensure_one()
        self.env['client.bill_of_quantity.history'].create({
            'boq_id': self.id,
            'event': event,
            'state': self.state,
            'version': self.version,
            'revision_date': self.revision_date,
            'changed_by': self.env.user.id,
            'note': note or False,
        })

    def _send_template_email(self, template_xmlid, recipient):
        self.ensure_one()
        if not recipient or not recipient.email:
            self.message_post(body='BoQ email was not sent because the recipient has no email address.')
            return
        template = self.env.ref(template_xmlid).sudo()
        template.send_mail(
            self.id,
            force_send=True,
            email_values={'email_to': recipient.email},
        )

    def _post_template_to_chatter(self, template_xmlid):
        """Render a mail template as an email-style chatter message.

        This deliberately does not send through SMTP. It keeps the workflow
        visible in the BoQ chatter even when the academic/demo environment
        has no outgoing mail server configured.
        """
        self.ensure_one()
        template = self.env.ref(template_xmlid).sudo()
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


class BillOfQuantityLine(models.Model):
    _name = 'client.bill_of_quantity.line'
    _description = 'BoQ Item'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    boq_id = fields.Many2one('client.bill_of_quantity', string='BoQ', required=True, ondelete='cascade')
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True)
    job_type = fields.Selection([('material', 'Material'), ('service', 'Service / Overhead'), ('labor', 'Labor')], string='Job Type', required=True, default='material')
    product_id = fields.Many2one('product.product', string='Product')
    description = fields.Char(string='Description')
    quantity = fields.Float(string='Planned Qty', default=1.0, required=True)
    uom_id = fields.Many2one('uom.uom', string='UoM')
    sale_price = fields.Monetary(string='Sale Price')
    subtotal = fields.Monetary(string='Subtotal', compute='_compute_subtotal', store=True)
    currency_id = fields.Many2one(related='boq_id.currency_id', string='Currency', store=True, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        boq_ids = [vals.get('boq_id') for vals in vals_list if vals.get('boq_id')]
        locked_boqs = self.env['client.bill_of_quantity'].browse(boq_ids).filtered(
            lambda boq: boq.state in ('done', 'cancel')
        )
        if locked_boqs:
            raise UserError('Items cannot be added to a Done or Cancelled BoQ.')
        return super().create(vals_list)

    def write(self, vals):
        if self.filtered(lambda line: line.boq_id.state in ('done', 'cancel')):
            raise UserError('Items in a Done or Cancelled BoQ cannot be modified.')
        return super().write(vals)

    def unlink(self):
        if self.filtered(lambda line: line.boq_id.state in ('done', 'cancel')):
            raise UserError('Items in a Done or Cancelled BoQ cannot be deleted.')
        return super().unlink()

    @api.depends('quantity', 'sale_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.sale_price

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.description = self.product_id.display_name
            self.uom_id = self.product_id.uom_id
            self.sale_price = self.product_id.lst_price


class BillOfQuantityHistory(models.Model):
    _name = 'client.bill_of_quantity.history'
    _description = 'BoQ Audit History'
    _order = 'changed_at desc, id desc'

    boq_id = fields.Many2one('client.bill_of_quantity', string='BoQ', required=True, ondelete='cascade')
    event = fields.Selection([
        ('created', 'Created'),
        ('submitted', 'Submitted for Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
        ('reset', 'Reset to Draft'),
    ], string='Action', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='State', readonly=True)
    version = fields.Integer(string='Version', readonly=True)
    revision_date = fields.Date(string='Revision Date', readonly=True)
    changed_by = fields.Many2one('res.users', string='Changed By', readonly=True)
    changed_at = fields.Datetime(string='Changed On', default=fields.Datetime.now, readonly=True)
    note = fields.Text(string='Feedback / Note', readonly=True)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    boq_id = fields.Many2one(
        'client.bill_of_quantity', string='BoQ', ondelete='restrict', copy=False,
    )
    client_ticket_id = fields.Many2one(
        'client.ticket', string='Design Request', related='boq_id.request_id',
        store=True, readonly=True,
    )
    boq_margin = fields.Float(
        string='BoQ Margin (%)', related='boq_id.margin', readonly=True,
    )
    boq_total_estimate_cost = fields.Monetary(
        string='Total Estimate Cost', related='boq_id.total_cost', readonly=True,
    )
    boq_untaxed_amount = fields.Monetary(
        string='BoQ Untaxed Amount', compute='_compute_boq_amounts', readonly=True,
    )

    @api.depends(
        'boq_id', 'boq_id.total_materials_cost', 'boq_id.total_service_cost',
        'boq_id.total_labor_cost',
    )
    def _compute_boq_amounts(self):
        for order in self:
            order.boq_untaxed_amount = (
                order.boq_id.total_materials_cost
                + order.boq_id.total_service_cost
                + order.boq_id.total_labor_cost
            ) if order.boq_id else 0.0

    def action_view_boq(self):
        self.ensure_one()
        return {
            'name': 'BoQ',
            'type': 'ir.actions.act_window',
            'res_model': 'client.bill_of_quantity',
            'view_mode': 'form',
            'res_id': self.boq_id.id,
        }

    def action_view_client_ticket(self):
        self.ensure_one()
        return {
            'name': 'Design Request',
            'type': 'ir.actions.act_window',
            'res_model': 'client.ticket',
            'view_mode': 'form',
            'res_id': self.client_ticket_id.id,
        }
