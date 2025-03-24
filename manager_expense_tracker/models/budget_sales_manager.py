from odoo import models, fields, api

class BudgetSalesManager(models.Model):
    _name = "budget.sales.manager"
    _description = "Budget Sales Manager"

    name = fields.Char(
        string="Name",
        compute="_compute_name",
        store=True
    )

    manager_id = fields.Many2one(
        comodel_name="res.users",
        string="Manager",
        required=True
    )

    phone = fields.Char(string="Phone")
    active = fields.Boolean(default=True)

    code_1c = fields.Char(
        string="Code 1C",
        size=50,
        help="Unique identifier for integration with 1C system"
    )

    fuel_price_ids = fields.One2many(
        "fuel.prices",
        "manager_id",
        string="Fuel Prices"
    )

    finances_ids = fields.One2many(
        "manager.finance",
        "manager_id",
        string="Financial Records"
    )

    @api.depends("manager_id")
    def _compute_name(self):
        """automatically fills in the manager's name"""
        for record in self:
            record.name = record.manager_id.name if record.manager_id else "N/A"

    @api.depends("manager_id", "phone")
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.manager_id.name} ({record.phone})" if record.phone else record.manager_id.name