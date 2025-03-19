from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ManagerFinance(models.Model):
    _name = "manager.finance"
    _description = "Manager's Finance"

    manager_id = fields.Many2one(
        "budget.sales.manager",
        string="Manager",
        required=True
    )
    date = fields.Date(
        string="Date",
        required=True
    )
    income = fields.Float(
        string="Income",
        required=True
    )
    expenses_other = fields.Float(
        string="Other Expenses",
        required=True
    )
    expenses_auto = fields.Float(
        string="Auto Expenses",
        compute="_compute_auto_expenses",
        store=True
    )
    balance = fields.Float(
        string="Balance",
        compute="_compute_balance",
        store=True
    )
    approved = fields.Boolean(string="Approved")

    fuel_price_id = fields.Many2one(
        "fuel.prices",
        string="Fuel Price Record",
        compute="_compute_fuel_price",
        store=True
    )

    @api.depends("income", "expenses_other", "expenses_auto")
    def _compute_balance(self):
        """Calculate balance as income minus total expenses."""
        for record in self:
            record.balance = record.income - (record.expenses_other + record.expenses_auto)

    @api.depends("manager_id", "date")
    def _compute_auto_expenses(self):
        """Compute auto expenses based on distance traveled and fuel cost."""
        for record in self:
            if not record.manager_id or not record.date:
                record.expenses_auto = 0
                continue

            work_day = self.env["manager.work.day"].search([
                ("manager_id", "=", record.manager_id.id),
                ("date", "=", record.date)
            ], limit=1)

            fuel_data = self.env["fuel.prices"].sudo().search([
                ("manager_id", "=", record.manager_id.id),
                ("date", "=", record.date)
            ], order="date desc", limit=1)

            record.fuel_price_id = fuel_data

            if work_day and fuel_data:
                record.expenses_auto = (
                    (work_day.km * fuel_data.consumption / 100 * fuel_data.fuel_price) +
                    (work_day.km * fuel_data.depreciation)
                )
            else:
                record.expenses_auto = 0

    @api.depends("date", "manager_id")
    def _compute_fuel_price(self):
        """Automatically link finance record to the correct fuel price record."""
        for record in self:
            record.fuel_price_id = self.env["fuel.prices"].search([
                ("manager_id", "=", record.manager_id.id),
                ("date", "=", record.date)
            ], order="date desc", limit=1)
