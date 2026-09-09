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
    project_id = fields.Many2one('project.project', string='Project', related='request_id.project_id', store=True, readonly=True)
    unit_code = fields.Char(string='Unit Code')
    product_type = fields.Selection(related='request_id.product_type', string='House / Product Type', readonly=True)
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
                              ('done', 'Done'),
                              ('cancel', 'Cancelled')], 
                              string='Status', default='draft', required=True, tracking=True)
    
    line_ids = fields.One2many('client.bill_of_quantity.line', 'boq_id', string='BoQ Items', copy=True)
    total_cost = fields.Monetary(string='Total Cost', compute='_compute_totals', store=True)
    total_materials_cost = fields.Monetary(string='Total Materials Cost', compute='_compute_totals', store=True)
    total_service_cost = fields.Monetary(string='Total Service / Overhead Cost', compute='_compute_totals', store=True)
    total_labor_cost = fields.Monetary(string='Total Labor Cost', compute='_compute_totals', store=True)
    margin = fields.Float(string='Margin (%)', default=0.0)

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
            boq.total_cost = base_total * (1 + boq.margin)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('client.bill_of_quantity') or 'New'
        return super().create(vals_list)

    @api.onchange('request_id')
    def _onchange_request_id(self):
        if self.request_id:
            self.unit_code = self.unit_code or self.request_id.project_id.name
            self.responsible_id = self.request_id.designer_id or self.env.user

    def action_submit(self):
        for boq in self:
            if boq.state != 'draft':
                raise UserError('Only draft BoQs can be submitted.')
            if not boq.line_ids:
                raise UserError('Add at least one BoQ item before submitting.')
            boq.write({'state': 'submitted'})

    def action_done(self):
        for boq in self:
            if boq.state != 'submitted':
                raise UserError('Only submitted BoQs can be marked done.')
            boq.write({'state': 'done'})

    def action_cancel(self):
        for boq in self:
            if boq.state in ('done', 'cancel'):
                raise UserError('This BoQ cannot be cancelled.')
            boq.write({'state': 'cancel'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})


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
