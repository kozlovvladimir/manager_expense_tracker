from odoo import models, fields, api

"""
This module defines the ManagerDailyReport model,
which tracks daily reports for managers.
It records daily activities such as fuel usage, expenses, income, and balance.
It also manages the relationship with fuel prices, depreciation,
and syncs financial data
with other models like work day and finance.
"""


class ManagerDailyReport(models.Model):
    """
    This class represents the daily report of a manager.
    It records the daily activities, including fuel usage, expenses,
    income, and balance for a specific manager.
    It also manages the relationship with fuel prices, depreciation,
    and syncs financial data with other models.

    Fields:
    - name: The name of the daily report, default is "Daily Report".
    - tax_ids: Many-to-many relationship with account.tax
    to manage taxes associated with the report.
    - employee_id: The employee associated with the report (optional).
    - manager_id: The manager associated with the daily report.
    - vehicle_id: The vehicle linked to the report.
    - date: The date the report was created.
    - description: A description of the daily report.
    - odometer_start: The odometer reading at the start of the day.
    - odometer_end: The odometer reading at the end of the day.
    - distance: The computed distance traveled, based on odometer readings.
    - fuel_price_per_liter: The price of fuel per liter for the manager
    on the given date.
    - fuel_consumption_rate: The fuel consumption rate per 100 km.
    - fuel_used: The total fuel used during the day.
    - fuel_cost: The computed fuel cost based
    on the fuel used and price per liter.
    - depreciation_rate: The depreciation rate per km.
    - depreciation_cost: The depreciation cost based on the distance traveled.
    - fuel_price_source: Indicates whether the fuel price is auto-filled
    or manually entered.
    - income: The total income for the manager on the given date.
    - expenses_manual: Other manually entered expenses.
    - total_expenses: The total computed expenses, including fuel,
    depreciation, and manual expenses.
    - balance: The balance for the day,
    computed as income minus total expenses.
    - fuel_expense_id: A link to the created fuel expense record.
    """
    _name = "manager.daily.report"
    _description = "Daily Report of Manager"
    _inherit = "hr.expense"

    # Report name for the daily report, with a default value of "Daily Report"
    name = fields.Char(string="Report Name", required=True,
                       default="Daily Report")

    # Many-to-many relation with account.tax
    # to manage the taxes associated with the report
    tax_ids = fields.Many2many(
        'account.tax',
        'manager_daily_report_tax_rel',
        'manager_report_id',
        'tax_id',
        string="Taxes"
    )

    # Employee associated with the report (optional)
    employee_id = fields.Many2one("hr.employee", string="Employee",
                                  required=False)

    # Many-to-one relation with budget.sales.manager
    # to link the manager to the daily report
    manager_id = fields.Many2one(
        "budget.sales.manager",
        string="Manager",
        required=True,
    )

    # Many-to-one relation with fleet.vehicle
    # to link the vehicle associated with the report
    vehicle_id = fields.Many2one("fleet.vehicle", string="Vehicle")

    # Date when the daily report is created
    date = fields.Date(required=True, default=fields.Date.today)

    # Description of the report
    description = fields.Char(string="Report Description")

    # Odometer reading at the start of the day
    odometer_start = fields.Float(string="Odometer Start")

    # Odometer reading at the end of the day
    odometer_end = fields.Float(string="Odometer End")

    # Computed field for the distance traveled (in km) based
    # on odometer readings
    distance = fields.Float(
        string="Distance (km)",
        compute="_compute_distance",
        store=True,
    )

    # Fuel price per liter for the manager on the given date
    fuel_price_per_liter = fields.Float()

    # Fuel consumption rate (L/100 km)
    fuel_consumption_rate = fields.Float(string="Fuel Consumption (L/100 km)")

    # Total fuel used (L)
    fuel_used = fields.Float(string="Fuel Used (L)")

    # Fuel cost calculated from the fuel used and fuel price
    fuel_cost = fields.Float()

    # Depreciation rate per km
    depreciation_rate = fields.Float(string="Depreciation Rate (per km)")

    # Depreciation cost calculated based on distance traveled
    depreciation_cost = fields.Float()

    # Selection to determine whether fuel price is auto-filled
    # or manually entered
    fuel_price_source = fields.Selection(
        [("auto", "Auto-filled"), ("manual", "Manually Entered")],
        compute="_compute_fuel_price",
        store=True,
    )

    # Total income for the manager on the given date
    income = fields.Float(default=0.0)

    # Other expenses manually entered
    expenses_manual = fields.Float(string="Other Expenses", default=0.0)

    # Computed total expenses, combining fuel, depreciation,
    # and manual expenses
    total_expenses = fields.Float(
        compute="_compute_total_expenses",
        store=True,
    )

    # Balance calculated as income minus total expenses
    balance = fields.Float(
        compute="_compute_balance",
        store=True,
    )

    # Link to the created fuel expense record
    fuel_expense_id = fields.Many2one(
        "hr.expense",
        string="Fuel Expense",
        help="Automatically created fuel expense record.",
    )

    @api.depends("odometer_start", "odometer_end")
    def _compute_distance(self):
        """
        Computes the distance traveled based on the odometer readings.
        Ensures that distance is always a positive value.
        """
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
        """
        Computes the fuel price, consumption rate,
        and depreciation rate for the report.
        Retrieves the most recent fuel price based on the manager and date.
        If no record is found, defaults are used.
        """
        FuelPrices = self.env["fuel.prices"]
        for record in self:
            if not record.manager_id or not record.date:
                record.fuel_price_per_liter = 0.0
                record.fuel_consumption_rate = 0.0
                record.depreciation_rate = 0.0
                record.fuel_price_source = "manual"
                continue

            fuel_entry = FuelPrices.search([
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

    @api.depends("distance", "fuel_consumption_rate", "fuel_price_per_liter",
                 "depreciation_rate")
    def _compute_fuel_expenses(self):
        """
        Computes the fuel expenses, including fuel cost and depreciation cost,
        based on the report's data.
        """
        for record in self:
            record.fuel_used = (
                    (record.distance * record.fuel_consumption_rate) / 100
            )
            record.fuel_cost = (
                    record.fuel_used * record.fuel_price_per_liter
            )
            record.depreciation_cost = (
                    record.distance * record.depreciation_rate
            )

    @api.depends("fuel_cost", "depreciation_cost", "expenses_manual")
    def _compute_total_expenses(self):
        """
        Computes the total expenses, including fuel cost, depreciation,
        and any manually entered expenses.
        """
        for record in self:
            record.total_expenses = (
                    record.fuel_cost
                    + record.depreciation_cost
                    + record.expenses_manual
            )

    @api.depends("income", "total_expenses")
    def _compute_balance(self):
        """
        Computes the balance for the day,
        which is the difference between income and total expenses.
        """
        for record in self:
            record.balance = record.income - record.total_expenses

    @api.onchange("manager_id", "date")
    def _onchange_manager_or_date(self):
        """
        Triggers the recalculation of fuel prices
        when the manager or date is changed.
        """
        self._compute_fuel_price()

    @api.onchange("fuel_price_per_liter", "fuel_consumption_rate",
                  "depreciation_rate")
    def _onchange_update_fuel_price_model(self):
        """
        Updates the fuel price model when fuel price, consumption,
        or depreciation rates are manually updated.
        """
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

    @api.onchange("fuel_used")
    def _onchange_fuel_used_block(self):
        """
        Allows manual editing of the fuel used without overriding
        the computed value.
        """
        pass

    @api.onchange("income", "expenses_manual", "balance")
    def _onchange_finance_data_sync_to_finance(self):
        """
        Syncs the financial data (income, expenses, balance)
        to the finance model when updated.
        """
        if self.manager_id and self.date:
            finance = self.env["manager.finance"].search([
                ("manager_id", "=", self.manager_id.id),
                ("date", "=", self.date)
            ], limit=1)
            if finance:
                finance.income = self.income
                finance.expenses_other = self.expenses_manual
                finance.balance = self.balance

    @api.onchange("odometer_start", "odometer_end")
    def _onchange_odometer_sync_to_work_day(self):
        """
        Syncs the odometer readings to the manager's work day when updated.
        """
        if self.manager_id and self.date:
            work_day = self.env["manager.work.day"].search([
                ("manager_id", "=", self.manager_id.id),
                ("date", "=", self.date)
            ], limit=1)
            if work_day:
                work_day.odometer_start = self.odometer_start
                work_day.odometer_end = self.odometer_end

    def create_fuel_expense(self):
        """
        Creates a fuel expense record when fuel cost is greater than zero.
        """
        for record in self:
            if record.fuel_cost > 0:
                product = self.env.ref("hr_expense.product_product_fuel",
                                       raise_if_not_found=False)
                expense_vals = {
                    "name": f"Fuel Expense ({record.date})",
                    "employee_id": record.manager_id.id,
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
        Creates multiple daily reports and generates fuel expense records.
        """
        records = super().create(vals_list)
        records.create_fuel_expense()
        return records

    def action_print_report(self):
        """
        Generates and prints the daily report.
        """
        for record in self:
            print(
                f"Generating report for {record.id}: date {record.date},"
                f" manager {record.manager_id.name}, balance {record.balance}"
            )
        return self.env.ref(
            'manager_expense_tracker.action_finance_report').report_action(
            self)
