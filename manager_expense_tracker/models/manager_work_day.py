"""Defines the ManagerWorkDay model for tracking daily manager activities.

This model records odometer readings, calculates travel distance,
fuel and depreciation expenses, and synchronizes the data with daily reports.
"""

from odoo import models, fields, api


class ManagerWorkDay(models.Model):
    """Tracks a manager's work day including mileage and expenses."""

    _name = "manager.work.day"
    _description = "Manager's Work Day"

    manager_id = fields.Many2one(
        "budget.sales.manager",
        string="Manager",
        required=True
    )
    date = fields.Date(required=True)
    odometer_start = fields.Float(string="Odometer Start", required=True)
    odometer_end = fields.Float(string="Odometer End", required=True)
    km = fields.Float(
        string="Distance (km)",
        compute="_compute_km",
        store=True
    )
    fuel_price_per_liter = fields.Float(
        string="Fuel Price per Liter",
        compute="_compute_fuel_data",
        store=True
    )
    fuel_consumption_per_100km = fields.Float(
        string="Fuel Consumption (L/100km)",
        compute="_compute_fuel_data",
        store=True
    )
    depreciation_rate = fields.Float(
        string="Depreciation per km",
        compute="_compute_fuel_data",
        store=True
    )
    fuel_expenses = fields.Float(
        string="Fuel Expenses",
        compute="_compute_fuel_expenses",
        store=True
    )
    depreciation_expenses = fields.Float(
        string="Depreciation Expenses",
        compute="_compute_depreciation_expenses",
        store=True
    )
    total_expenses = fields.Float(
        string="Total Expenses",
        compute="_compute_total_expenses",
        store=True
    )
    is_holiday = fields.Boolean(string="Holiday")

    @api.depends("odometer_start", "odometer_end")
    def _compute_km(self):
        for record in self:
            record.km = max(record.odometer_end - record.odometer_start, 0)

    @api.depends(
        "manager_id", "date",
        "manager_id.fuel_price_ids.fuel_price",
        "manager_id.fuel_price_ids.consumption",
        "manager_id.fuel_price_ids.depreciation",
        "manager_id.fuel_price_ids.date",
        "manager_id.fuel_price_ids.write_date"
    )
    def _compute_fuel_data(self):
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
        for record in self:
            record.fuel_expenses = (
                record.km * record.fuel_consumption_per_100km / 100
            ) * record.fuel_price_per_liter

    @api.depends("km", "depreciation_rate")
    def _compute_depreciation_expenses(self):
        for record in self:
            record.depreciation_expenses = record.km * record.depreciation_rate

    @api.depends("fuel_expenses", "depreciation_expenses")
    def _compute_total_expenses(self):
        for record in self:
            record.total_expenses = (
                record.fuel_expenses + record.depreciation_expenses
            )

    @api.model_create_multi
    def create(self, vals_list):
        """Create manager work day records and sync with daily report."""
        records = super().create(vals_list)
        # Although this accesses a protected method,
        # it's part of the same model logic
        records._sync_with_daily_report()
        return records

    def write(self, vals):
        """
            Override write method to synchronize data with related
            daily report after updating a work day.
            """
        res = super().write(vals)
        # Although this accesses a protected method,
        # it's part of the same model logic
        self._sync_with_daily_report()
        return res

    def _sync_with_daily_report(self):
        """Sync odometer readings to the manager.daily.report record
        of the same date and manager."""
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
