from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    design_request_ids = fields.One2many(
        'design.request', 'project_id', string='Design Requests'
    )
    design_manager_names = fields.Char(
        string='Design Managers', compute='_compute_design_manager_names'
    )

    @api.depends('design_request_ids.design_manager_id')
    def _compute_design_manager_names(self):
        for project in self:
            managers = project.design_request_ids.mapped('design_manager_id')
            project.design_manager_names = ', '.join(managers.mapped('name'))
