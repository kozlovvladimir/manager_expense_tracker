from odoo import models, fields, api

class BudgetSalesManager(models.Model):
    _name = "budget.sales.manager"
    _description = "Budget Sales Manager"

    manager_id = fields.Many2one(
        comodel_name="res.users",
        string="User",
        required=True,
        help="Select the user who is a sales manager."
    )

    phone = fields.Char(
        string="Phone",
        help="Phone number of the manager."
    )

    active = fields.Boolean(
        string="Active",
        default=True,
        help="Set active status of the manager."
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Override the create method to support batch processing"""
        return super().create(vals_list)
