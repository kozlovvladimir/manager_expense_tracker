from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ManagerDailyReport(models.Model):
    """ Daily Report of Manager """
    _name = "manager.daily.report"
    _description = "Daily Report of Manager"
    _inherit = "hr.expense"

    name = fields.Char(string="Report Name", required=True, default="Daily Report")

    tax_ids = fields.Many2many("account.tax", string="Taxes", compute=False,
                               store=False)

    employee_id = fields.Many2one("hr.employee", string="Employee", required=False)

    manager_id = fields.Many2one(
        "budget.sales.manager",
        string="Manager",
        required=True,
    )

    vehicle_id = fields.Many2one(
        "fleet.vehicle",
        string="Vehicle",
        help="Vehicle used for the trip.",
    )

    date = fields.Date(
        string="Date",
        required=True,
        default=fields.Date.today,
    )

    description = fields.Char(string="Report Description")

    # Trip Details
    odometer_start = fields.Float(string="Odometer Start")
    odometer_end = fields.Float(string="Odometer End")
    distance = fields.Float(
        string="Distance (km)",
        compute="_compute_distance",
        store=True,
    )

    # Fuel & Expenses
    fuel_price_per_liter = fields.Float(
        string="Fuel Price per Liter",
        compute="_compute_fuel_price",
        store=True,
    )
    fuel_consumption_rate = fields.Float(
        string="Fuel Consumption (L/100 km)",
        compute="_compute_fuel_price",
        store=True,
    )
    fuel_used = fields.Float(
        string="Fuel Used (L)",
        compute="_compute_fuel_expenses",
        store=True,
    )
    fuel_cost = fields.Float(
        string="Fuel Cost",
        compute="_compute_fuel_expenses",
        store=True,
    )
    depreciation_rate = fields.Float(
        string="Depreciation Rate (per km)",
        compute="_compute_fuel_price",
        store=True,
    )
    depreciation_cost = fields.Float(
        string="Depreciation Cost",
        compute="_compute_fuel_expenses",
        store=True,
    )

    fuel_price_source = fields.Selection(
        [("auto", "Auto-filled"), ("manual", "Manually Entered")],
        string="Fuel Price Source",
        compute="_compute_fuel_price",
        store=True,
    )

    # Financial Data
    income = fields.Float(string="Income", default=0.0)
    expenses_manual = fields.Float(string="Other Expenses", default=0.0)
    total_expenses = fields.Float(
        string="Total Expenses",
        compute="_compute_total_expenses",
        store=True,
    )
    balance = fields.Float(
        string="Balance",
        compute="_compute_balance",
        store=True,
    )

    # Related Expense Entry
    fuel_expense_id = fields.Many2one(
        "hr.expense",
        string="Fuel Expense",
        help="Automatically created fuel expense record.",
    )

    @api.depends("odometer_start", "odometer_end")
    def _compute_distance(self):
        """ Compute trip distance """
        for record in self:
            record.distance = max(
                record.odometer_end - record.odometer_start,
                0
            )

    @api.depends("manager_id", "date")
    def _compute_fuel_price(self):
        """ Auto-fill last known fuel prices & consumption rates """
        FuelPrices = self.env["fuel.prices"]
        for record in self:
            fuel_entry = FuelPrices.search_read(
                [("manager_id", "=", record.manager_id.id),
                 ("date", "<=", record.date)],
                ["fuel_price", "consumption", "depreciation"],
                order="date desc",
                limit=1,
            )
            if fuel_entry:
                record.update({
                    "fuel_price_per_liter": fuel_entry[0]["fuel_price"],
                    "fuel_consumption_rate": fuel_entry[0]["consumption"],
                    "depreciation_rate": fuel_entry[0]["depreciation"],
                    "fuel_price_source": "auto"
                })
            else:
                record.update({
                    "fuel_price_per_liter": 56.0,
                    "fuel_consumption_rate": 10.0,
                    "depreciation_rate": 1.25,
                    "fuel_price_source": "manual"
                })

    @api.depends(
        "distance",
        "fuel_consumption_rate",
        "fuel_price_per_liter",
        "depreciation_rate"
    )
    def _compute_fuel_expenses(self):
        """ Compute fuel and depreciation costs """
        for record in self:
            record.fuel_used = (record.distance * record.fuel_consumption_rate) / 100
            record.fuel_cost = record.fuel_used * record.fuel_price_per_liter
            record.depreciation_cost = record.distance * record.depreciation_rate

    @api.depends("fuel_cost", "depreciation_cost", "expenses_manual")
    def _compute_total_expenses(self):
        """ Compute total expenses (fuel + depreciation + other) """
        for record in self:
            record.total_expenses = (
                record.fuel_cost
                + record.depreciation_cost
                + record.expenses_manual
            )

    @api.depends("income", "total_expenses")
    def _compute_balance(self):
        """ Compute balance: income - expenses """
        for record in self:
            record.balance = record.income - record.total_expenses

    def create_fuel_expense(self):
        """ Create an hr.expense record for fuel cost """
        for record in self:
            if record.fuel_cost > 0:
                expense_vals = {
                    "name": f"Fuel Expense ({record.date})",
                    "employee_id": record.manager_id.id,
                    "amount": record.fuel_cost,
                    "date": record.date,
                    "state": "draft",
                    "product_id": self.env.ref("hr_expense.product_product_fuel").id,
                }
                expense = self.env["hr.expense"].create(expense_vals)
                record.fuel_expense_id = expense.id

    @api.model_create_multi
    def create(self, vals_list):
        """ Create multiple manager daily reports
        and related fuel expenses efficiently. """
        records = super().create(vals_list)
        records.create_fuel_expense()
        return records

    def action_print_report(self):
        """Функція для виклику друкованого звіту"""
        for record in self:
            print(
                f"Генерується звіт для {record.id}: дата {record.date},"
                f"менеджер {record.manager_id.name}, баланс {record.balance}"
            )
        return self.env.ref(
            'manager_expense_tracker.action_finance_report').report_action(
            self)

