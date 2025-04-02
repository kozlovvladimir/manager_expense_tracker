"""ManagerDailyReport model to track daily activity, fuel,
and finances for managers.
"""

from odoo import models, fields, api


class ManagerDailyReport(models.Model):
    """
    Daily report per manager, tracking odometer, fuel, depreciation, income,
    and balance.
    """

    _name = "manager.daily.report"
    _description = "Daily Report of Manager"
    _inherit = "hr.expense"

    name = fields.Char(string="Report Name", required=True,
                       default="Daily Report")
    tax_ids = fields.Many2many(
        'account.tax',
        'manager_daily_report_tax_rel',
        'manager_report_id',
        'tax_id',
        string="Taxes"
    )
    employee_id = fields.Many2one(
        "hr.employee", string="Employee"
    )
    manager_id = fields.Many2one(
        "budget.sales.manager", string="Manager", required=True
    )
    vehicle_id = fields.Many2one(
        "fleet.vehicle", string="Vehicle"
    )
    date = fields.Date(required=True, default=fields.Date.today)
    description = fields.Char(string="Report Description")
    odometer_start = fields.Float(string="Odometer Start")
    odometer_end = fields.Float(string="Odometer End")
    distance = fields.Float(
        string="Distance (km)", compute="_compute_distance", store=True
    )

    fuel_price_per_liter = fields.Float()
    fuel_consumption_rate = fields.Float(string="Fuel Consumption (L/100 km)")
    fuel_used = fields.Float(string="Fuel Used (L)",
                             compute="_compute_fuel_expenses", store=True)
    fuel_cost = fields.Float(compute="_compute_fuel_expenses", store=True)
    depreciation_rate = fields.Float(string="Depreciation Rate (per km)")
    depreciation_cost = fields.Float(compute="_compute_fuel_expenses",
                                     store=True)

    fuel_price_source = fields.Selection(
        [("auto", "Auto-filled"), ("manual", "Manually Entered")],
        compute="_compute_fuel_price", store=True
    )

    income = fields.Float(default=0.0)
    expenses_manual = fields.Float(string="Other Expenses", default=0.0)
    total_expenses = fields.Float(compute="_compute_total_expenses",
                                  store=True)
    balance = fields.Float(compute="_compute_balance", store=True)
    fuel_expense_id = fields.Many2one(
        "hr.expense", string="Fuel Expense"
    )

    @api.depends("odometer_start", "odometer_end")
    def _compute_distance(self):
        for record in self:
            record.distance = max(
                record.odometer_end - record.odometer_start, 0
            )

    @api.depends(
        "manager_id", "date",
        "manager_id.fuel_price_ids.fuel_price",
        "manager_id.fuel_price_ids.consumption",
        "manager_id.fuel_price_ids.depreciation",
        "manager_id.fuel_price_ids.date",
        "manager_id.fuel_price_ids.write_date"
    )
    def _compute_fuel_price(self):
        fuel_prices = self.env["fuel.prices"]
        for record in self:
            if not record.manager_id or not record.date:
                record.fuel_price_per_liter = 0.0
                record.fuel_consumption_rate = 0.0
                record.depreciation_rate = 0.0
                record.fuel_price_source = "manual"
                continue

            fuel_entry = fuel_prices.search([
                ("manager_id", "=", record.manager_id.id),
                ("date", "<=", record.date)
            ], order="date desc", limit=1)

            if fuel_entry:
                record.fuel_price_per_liter = fuel_entry.fuel_price
                record.fuel_consumption_rate = fuel_entry.consumption
                record.depreciation_rate = fuel_entry.depreciation
                record.fuel_price_source = "auto"
            else:
                record.fuel_price_per_liter = 56.0
                record.fuel_consumption_rate = 10.0
                record.depreciation_rate = 1.25
                record.fuel_price_source = "manual"

    @api.depends(
        "distance", "fuel_consumption_rate",
        "fuel_price_per_liter", "depreciation_rate"
    )
    def _compute_fuel_expenses(self):
        for rec in self:
            rec.fuel_used = (
                    rec.distance * rec.fuel_consumption_rate / 100
            )
            rec.fuel_cost = rec.fuel_used * rec.fuel_price_per_liter
            rec.depreciation_cost = rec.distance * rec.depreciation_rate

    @api.depends("fuel_cost", "depreciation_cost", "expenses_manual")
    def _compute_total_expenses(self):
        for rec in self:
            rec.total_expenses = (
                    rec.fuel_cost + rec.depreciation_cost + rec.expenses_manual
            )

    @api.depends("income", "total_expenses")
    def _compute_balance(self):
        for record in self:
            record.balance = record.income - record.total_expenses

    def _find_finance_or_work_day(self, model):
        return self.env[model].search([
            ("manager_id", "=", self.manager_id.id),
            ("date", "=", self.date)
        ], limit=1)

    @api.onchange("manager_id", "date")
    def _onchange_manager_or_date(self):
        self._compute_fuel_price()

    @api.onchange(
        "fuel_price_per_liter", "fuel_consumption_rate",
        "depreciation_rate"
    )
    def _onchange_update_fuel_price_model(self):
        for record in self:
            if not record.manager_id or not record.date:
                continue
            fuel = self.env["fuel.prices"].search([
                ("manager_id", "=", record.manager_id.id),
                ("date", "=", record.date)
            ], limit=1)
            if fuel:
                fuel.write({
                    "fuel_price": record.fuel_price_per_liter,
                    "consumption": record.fuel_consumption_rate,
                    "depreciation": record.depreciation_rate
                })
            else:
                self.env["fuel.prices"].create({
                    "manager_id": record.manager_id.id,
                    "date": record.date,
                    "fuel_price": record.fuel_price_per_liter,
                    "consumption": record.fuel_consumption_rate,
                    "depreciation": record.depreciation_rate
                })

    @api.onchange("income", "expenses_manual", "balance")
    def _onchange_finance_data_sync_to_finance(self):
        if self.manager_id and self.date:
            finance = self._find_finance_or_work_day("manager.finance")
            if finance:
                finance.income = self.income
                finance.expenses_other = self.expenses_manual
                finance.balance = self.balance

    @api.onchange("odometer_start", "odometer_end")
    def _onchange_odometer_sync_to_work_day(self):
        if self.manager_id and self.date:
            work_day = self._find_finance_or_work_day("manager.work.day")
            if work_day:
                work_day.odometer_start = self.odometer_start
                work_day.odometer_end = self.odometer_end

    def create_fuel_expense(self):
        """Create a draft fuel expense record if fuel cost is greater than zero."""
        for record in self:
            if record.fuel_cost > 0:
                product = self.env.ref(
                    "hr_expense.product_product_fuel",
                    raise_if_not_found=False
                )
                expense_vals = {
                    "name": f"Fuel Expense ({record.date})",
                    "employee_id": record.employee_id.id,
                    "amount": record.fuel_cost,
                    "date": record.date,
                    "state": "draft",
                }
                if product:
                    expense_vals["product_id"] = product.id
                expense = self.env["hr.expense"].create(expense_vals)
                record.fuel_expense_id = expense.id

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override the create method to auto-assign employee_id
        based on manager's user and create a fuel expense if needed.
        """
        for vals in vals_list:
            if not vals.get("employee_id") and vals.get("manager_id"):
                manager = self.env["budget.sales.manager"].browse(
                    vals["manager_id"]
                )
                employee = self.env["hr.employee"].search([(
                    "user_id", "=", manager.manager_id.id
                )], limit=1)
                if employee:
                    vals["employee_id"] = employee.id
        records = super().create(vals_list)
        records.create_fuel_expense()
        return records

    def action_print_report(self):
        """
        Generate and return the finance PDF report for the daily report.
        """
        return self.env.ref(
            'manager_expense_tracker.action_finance_report'
        ).report_action(self)
