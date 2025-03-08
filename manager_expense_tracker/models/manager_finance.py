from odoo import models, fields, api

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
        compute="_compute_balance",
        store=True
    )
    approved = fields.Boolean()

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
                ("month", "=", record.date.strftime('%Y-%m'))
            ], limit=1)

            if work_day and fuel_data:
                record.expenses_auto = (
                    (work_day.distance * fuel_data.consumption / 100 * fuel_data.fuel_price) +
                    (work_day.distance * fuel_data.depreciation)
                )
            else:
                record.expenses_auto = 0
