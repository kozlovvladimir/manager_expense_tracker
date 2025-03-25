from odoo import models, fields, api

"""
This module defines the ManagerFinance model,
which tracks the financial data for a manager.
It includes fields for recording income, manually entered expenses,
automatically calculated
expenses, and balance for a specific manager on a given date.
It also manages the approval
status of the financial data
and provides functionality to sync the financial records with
daily reports.

Fields:
- manager_id: The manager associated with the financial data.
- date: The date of the financial data record.
- income: The income of the manager on the specified date.
- expenses_other: The manually entered other expenses for the manager.
- expenses_auto: The automatically calculated expenses based
on fuel consumption and depreciation.
- balance: The balance for the manager, calculated as income minus the sum
of other expenses and automatic expenses.
- approved: A boolean field indicating whether
the financial data has been approved.
- fuel_price_id: A reference to the most recent fuel price record
for the manager and date.
"""


class ManagerFinance(models.Model):
    """
    This class represents the financial data of a manager.
    It tracks the income, expenses (both manual and automatic),
    balance, and fuel price for a specific manager
    on a given date. It also manages the approval status of the financial data
    and syncs the financial records
    with daily reports.

    Fields:
    - manager_id: The manager associated with the financial data.
    - date: The date of the financial data record.
    - income: The income of the manager on the specified date.
    - expenses_other: The manually entered other expenses for the manager.
    - expenses_auto: The automatically calculated expenses based
    on fuel consumption and depreciation.
    - balance: The balance for the manager,
    calculated as income minus the sum of other expenses
    and automatic expenses.
    - approved: A boolean field indicating whether
    the financial data has been approved.
    - fuel_price_id: A reference to the most recent fuel price record for
    the manager and date.
    """
    _name = "manager.finance"
    _description = "Manager's Finance"

    # Many-to-one relation with the manager
    # to link financial data to a specific manager
    manager_id = fields.Many2one(
        "budget.sales.manager",
        string="Manager",
        required=True
    )

    # The date when the financial data is recorded
    date = fields.Date(
        required=True
    )

    # Income for the manager on the given date
    income = fields.Float(
        required=True
    )

    # Other expenses manually entered for the manager
    expenses_other = fields.Float(
        string="Other Expenses",
        required=True
    )

    # Computed field for automatic expenses based
    # on fuel price and consumption
    expenses_auto = fields.Float(
        string="Auto Expenses",
        compute="_compute_auto_expenses",
        store=True
    )

    # Computed field for the balance, calculated as income minus expenses
    balance = fields.Float(
        string="Balance",
        compute="_compute_balance",
        store=True
    )

    # Boolean field to indicate whether the finance data is approved
    approved = fields.Boolean(string="Approved")

    # Many-to-one relation with fuel.prices
    # to link the fuel price record to the financial data
    fuel_price_id = fields.Many2one(
        "fuel.prices",
        string="Fuel Price Record",
        compute="_compute_fuel_price",
        store=True
    )

    @api.depends("income", "expenses_other", "expenses_auto")
    def _compute_balance(self):
        """
        Computes the balance by subtracting the sum of other expenses
        and auto expenses from the income.
        This field is automatically updated when income or expenses change.
        """
        for record in self:
            record.balance = record.income - (
                    record.expenses_other + record.expenses_auto
            )

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
        """
        Computes auto expenses based on the manager's workday data
        and fuel price data.
        The expenses are calculated using distance traveled,
        fuel consumption rate, and depreciation rate.
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
        "manager_id",
        "date",
        "manager_id.fuel_price_ids.fuel_price",
        "manager_id.fuel_price_ids.consumption",
        "manager_id.fuel_price_ids.depreciation",
        "manager_id.fuel_price_ids.date",
        "manager_id.fuel_price_ids.write_date"
    )
    def _compute_fuel_price(self):
        """
        Computes the most recent fuel price record based
        on the manager and date.
        Updates the fuel price field with the latest fuel price
        for the given date.
        """
        for record in self:
            record.fuel_price_id = self.env["fuel.prices"].search([
                ("manager_id", "=", record.manager_id.id),
                ("date", "<=", record.date)
            ], order="date desc", limit=1)

    def write(self, vals):
        """
        Overrides the write method to update the related manager.daily.report
        and sync financial data. Ensures that income, other expenses,
        and balance
        are updated in the daily report when modified.
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
