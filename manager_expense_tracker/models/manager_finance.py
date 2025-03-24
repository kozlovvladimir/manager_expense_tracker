# === manager_finance.py ===
from odoo import models, fields, api, _


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
        for record in self:
            record.balance = record.income - (record.expenses_other + record.expenses_auto)

    @api.depends(
        "manager_id",
        "date",
        "manager_id.fuel_price_ids.fuel_price",
        "manager_id.fuel_price_ids.consumption",
        "manager_id.fuel_price_ids.depreciation",
        "manager_id.fuel_price_ids.date",
        "manager_id.fuel_price_ids.write_date"
    )
    def _compute_auto_expenses(self):
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
                record.expenses_auto = (
                    (work_day.km * fuel_data.consumption / 100 * fuel_data.fuel_price) +
                    (work_day.km * fuel_data.depreciation)
                )
            else:
                record.expenses_auto = 0

    @api.depends(
        "manager_id",
        "date",
        "manager_id.fuel_price_ids.fuel_price",
        "manager_id.fuel_price_ids.consumption",
        "manager_id.fuel_price_ids.depreciation",
        "manager_id.fuel_price_ids.date",
        "manager_id.fuel_price_ids.write_date"
    )
    def _compute_fuel_price(self):
        for record in self:
            record.fuel_price_id = self.env["fuel.prices"].search([
                ("manager_id", "=", record.manager_id.id),
                ("date", "<=", record.date)
            ], order="date desc", limit=1)

    def write(self, vals):
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

# === manager_daily_report.py ===
from odoo import models, fields, api, _


class ManagerDailyReport(models.Model):
    _name = "manager.daily.report"
    _description = "Daily Report of Manager"
    _inherit = "hr.expense"

    name = fields.Char(string="Report Name", required=True, default="Daily Report")
    manager_id = fields.Many2one("budget.sales.manager", string="Manager", required=True)
    date = fields.Date(string="Date", required=True, default=fields.Date.today)
    income = fields.Float(string="Income", default=0.0)
    expenses_manual = fields.Float(string="Other Expenses", default=0.0)
    total_expenses = fields.Float(string="Total Expenses", compute="_compute_total_expenses", store=True)
    balance = fields.Float(string="Balance", compute="_compute_balance", store=True)

    fuel_cost = fields.Float(string="Fuel Cost", default=0.0)
    depreciation_cost = fields.Float(string="Depreciation Cost", default=0.0)

    @api.depends("fuel_cost", "depreciation_cost", "expenses_manual")
    def _compute_total_expenses(self):
        for record in self:
            record.total_expenses = record.fuel_cost + record.depreciation_cost + record.expenses_manual

    @api.depends("income", "total_expenses")
    def _compute_balance(self):
        for record in self:
            record.balance = record.income - record.total_expenses

    def write(self, vals):
        res = super().write(vals)
        for record in self:
            finance = self.env["manager.finance"].search([
                ("manager_id", "=", record.manager_id.id),
                ("date", "=", record.date)
            ], limit=1)
            if finance:
                finance.write({
                    "income": record.income,
                    "expenses_other": record.expenses_manual,
                    "balance": record.balance,
                })
        return res
