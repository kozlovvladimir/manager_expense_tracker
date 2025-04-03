"""
ManagerFinance model tracks financial data for sales managers,
including income, expenses, and balance.
"""

from odoo import models, fields, api


class ManagerFinance(models.Model):
    """
    Financial data model for budget sales managers.
    Tracks income, manual and automatic expenses, balance,
    and fuel price information per date.
    """

    _name = "manager.finance"
    _description = "Manager's Finance"

    manager_id = fields.Many2one(
        "budget.sales.manager",
        string="Manager",
        required=True
    )

    date = fields.Date(required=True)

    income = fields.Float(required=True)

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
        """Calculate balance = income - (manual + auto expenses)."""
        for record in self:
            record.balance = record.income - (
                record.expenses_other + record.expenses_auto
            )

    @api.depends(
        "manager_id", "date",
        "manager_id.fuel_price_ids.fuel_price",
        "manager_id.fuel_price_ids.consumption",
        "manager_id.fuel_price_ids.depreciation",
        "manager_id.fuel_price_ids.date",
        "manager_id.fuel_price_ids.write_date"
    )
    def _compute_auto_expenses(self):
        """
        Compute auto expenses based on distance, consumption, depreciation.
        Auto-expense = fuel_cost + depreciation, if work_day exists.
        """
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
                ("date", "<=", record.date)
            ], order="date desc", limit=1)

            record.fuel_price_id = fuel_data

            if work_day and fuel_data:
                fuel_consumption = work_day.km * fuel_data.consumption / 100
                fuel_cost = fuel_consumption * fuel_data.fuel_price
                depreciation_cost = work_day.km * fuel_data.depreciation
                record.expenses_auto = fuel_cost + depreciation_cost
            else:
                record.expenses_auto = 0

    @api.depends(
        "manager_id", "date",
        "manager_id.fuel_price_ids.fuel_price",
        "manager_id.fuel_price_ids.consumption",
        "manager_id.fuel_price_ids.depreciation",
        "manager_id.fuel_price_ids.date",
        "manager_id.fuel_price_ids.write_date"
    )
    def _compute_fuel_price(self):
        """Get most recent fuel price before
        or on the current record's date.
        """
        for record in self:
            record.fuel_price_id = self.env["fuel.prices"].search([
                ("manager_id", "=", record.manager_id.id),
                ("date", "<=", record.date)
            ], order="date desc", limit=1)

    def write(self, vals):
        """
        Sync financial changes (income, expenses, balance)
        with manager.daily.report if exists.
        """
        res = super().write(vals)
        for record in self:
            report = self.env["manager.daily.report"].search([
                ("manager_id", "=", record.manager_id.id),
                ("date", "=", record.date)
            ], limit=1)
            if report:
                report.write({
                    "income": record.income,
                    "expenses_manual": record.expenses_other,
                    "balance": record.balance,
                })
        return res

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            daily = self.env["manager.daily.report"].search([
                ("manager_id", "=", record.manager_id.id),
                ("date", "=", record.date)
            ], limit=1)
            if not daily:
                self.env["manager.daily.report"].create({
                    "manager_id": record.manager_id.id,
                    "date": record.date,
                    "income": record.income,
                    "expenses_manual": record.expenses_other,
                })
        return records