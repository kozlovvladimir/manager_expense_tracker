from odoo import models, fields, api

"""
This module defines the ManagerWorkDay model,
which tracks the workday data for a manager.
It records odometer readings at the start and end of the day,
calculates the distance traveled,
fuel expenses, and depreciation costs.
The model uses the manager's fuel price data to compute
fuel and depreciation expenses based on the workday's data.
"""


class ManagerWorkDay(models.Model):
    """
    This class represents a manager's work day, tracking odometer readings,
    fuel usage, depreciation, and related expenses.
    It calculates the total distance traveled, fuel expenses,
    and depreciation costs based on the manager's workday data.

    Fields:
    - manager_id: The manager associated with this workday record.
    - date: The date of the workday.
    - odometer_start: The odometer reading at the start of the day.
    - odometer_end: The odometer reading at the end of the day.
    - km: The computed distance traveled, based on the odometer readings.
    - fuel_price_per_liter: The fuel price per liter based
    on the manager's most recent fuel price data.
    - fuel_consumption_per_100km: The fuel consumption rate (L/100 km) based
    on the manager's fuel price data.
    - depreciation_rate: The depreciation rate per kilometer,
    based on the manager's fuel price data.
    - fuel_expenses: The computed fuel expenses based on distance traveled,
    fuel consumption, and fuel price.
    - depreciation_expenses: The computed depreciation expenses based
    on distance and depreciation rate.
    - total_expenses: The total expenses, including fuel
    and depreciation costs.
    - is_holiday: A boolean indicating if the workday is a holiday.
    """
    _name = "manager.work.day"
    _description = "Manager's Work Day"

    # Many-to-one relation to the budget.sales.manager model,
    # linking work day to a specific manager
    manager_id = fields.Many2one(
        "budget.sales.manager",
        string="Manager",
        required=True
    )

    # The date of the work day
    date = fields.Date(required=True)

    # Odometer reading at the start of the work day
    odometer_start = fields.Float(
        string="Odometer Start",
        required=True
    )

    # Odometer reading at the end of the work day
    odometer_end = fields.Float(
        string="Odometer End",
        required=True
    )

    # Computed field for the distance traveled (in km),
    # calculated from odometer readings
    km = fields.Float(
        string="Distance (km)",
        compute="_compute_km",
        store=True
    )

    # Computed field for the fuel price per liter based
    # on the manager's fuel price data
    fuel_price_per_liter = fields.Float(
        string="Fuel Price per Liter",
        compute="_compute_fuel_data",
        store=True
    )

    # Computed field for the fuel consumption per 100 km based
    # on the manager's fuel price data
    fuel_consumption_per_100km = fields.Float(
        string="Fuel Consumption (L/100km)",
        compute="_compute_fuel_data",
        store=True
    )

    # Computed field for the depreciation rate per km based
    # on the manager's fuel price data
    depreciation_rate = fields.Float(
        string="Depreciation per km",
        compute="_compute_fuel_data",
        store=True
    )

    # Computed field for the total fuel expenses based
    # on distance, fuel consumption, and price
    fuel_expenses = fields.Float(
        string="Fuel Expenses",
        compute="_compute_fuel_expenses",
        store=True
    )

    # Computed field for the depreciation expenses based
    # on distance and depreciation rate
    depreciation_expenses = fields.Float(
        string="Depreciation Expenses",
        compute="_compute_depreciation_expenses",
        store=True
    )

    # Computed field for the total expenses, including fuel and depreciation
    total_expenses = fields.Float(
        string="Total Expenses",
        compute="_compute_total_expenses",
        store=True
    )

    # Boolean field indicating if the work day is a holiday
    is_holiday = fields.Boolean(
        string="Holiday"
    )

    @api.depends("odometer_start", "odometer_end")
    def _compute_km(self):
        """
        Computes the distance traveled based on the odometer readings.
        Ensures that distance is always a positive value.
        """
        for record in self:
            record.km = max(record.odometer_end - record.odometer_start, 0)

    @api.depends(
        "manager_id",
        "date",
        "manager_id.fuel_price_ids.fuel_price",
        "manager_id.fuel_price_ids.consumption",
        "manager_id.fuel_price_ids.depreciation",
        "manager_id.fuel_price_ids.date",
        "manager_id.fuel_price_ids.write_date"
    )
    def _compute_fuel_data(self):
        """
        Computes the fuel price, consumption rate, and depreciation rate based
        on the manager's most recent fuel data.
        If no data is found, defaults are set to zero.
        """
        for record in self:
            last_fuel_data = self.env["fuel.prices"].search([
                ("manager_id", "=", record.manager_id.id),
                ("date", "<=", record.date)
            ], order="date desc", limit=1)

            if last_fuel_data:
                record.fuel_price_per_liter = last_fuel_data.fuel_price
                record.fuel_consumption_per_100km = last_fuel_data.consumption
                record.depreciation_rate = last_fuel_data.depreciation
            else:
                record.fuel_price_per_liter = 0
                record.fuel_consumption_per_100km = 0
                record.depreciation_rate = 0

    @api.depends("km", "fuel_price_per_liter", "fuel_consumption_per_100km")
    def _compute_fuel_expenses(self):
        """
        Computes the fuel expenses based on the distance traveled,
        fuel consumption rate, and fuel price.
        """
        for record in self:
            record.fuel_expenses = (
                record.km * record.fuel_consumption_per_100km / 100
            ) * record.fuel_price_per_liter

    @api.depends("km", "depreciation_rate")
    def _compute_depreciation_expenses(self):
        """
        Computes the depreciation expenses based on the distance traveled
        and depreciation rate.
        """
        for record in self:
            record.depreciation_expenses = record.km * record.depreciation_rate

    @api.depends("fuel_expenses", "depreciation_expenses")
    def _compute_total_expenses(self):
        """
        Computes the total expenses as the sum of fuel expenses
        and depreciation expenses.
        """
        for record in self:
            record.total_expenses = sum(
                [record.fuel_expenses, record.depreciation_expenses])

    @api.model
    def create(self, vals):
        """
        Creates a new work day record
        and synchronizes it with the daily report.
        """
        record = super().create(vals)
        record._sync_with_daily_report()
        return record

    def write(self, vals):
        """
        Updates an existing work day record and synchronizes
        it with the daily report.
        """
        res = super().write(vals)
        self._sync_with_daily_report()
        return res

    def _sync_with_daily_report(self):
        """
        Synchronizes the work day data
        with the corresponding manager's daily report.
        Updates the odometer readings in the daily report.
        """
        for record in self:
            report = self.env["manager.daily.report"].search([
                ("manager_id", "=", record.manager_id.id),
                ("date", "=", record.date)
            ], limit=1)
            if report:
                report.write({
                    "odometer_start": record.odometer_start,
                    "odometer_end": record.odometer_end,
                })
