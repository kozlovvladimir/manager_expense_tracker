from odoo import models, fields, api, _


class ManagerWorkDay(models.Model):
    _name = "manager.work.day"
    _description = "Manager's Work Day"

    manager_id = fields.Many2one(
        "budget.sales.manager",
        string="Manager",
        required=True
    )

    date = fields.Date(required=True)

    odometer_start = fields.Float(
        string="Odometer Start",
        required=True
    )

    odometer_end = fields.Float(
        string="Odometer End",
        required=True
    )

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

    is_holiday = fields.Boolean(
        string="Holiday"
    )

    @api.depends("odometer_start", "odometer_end")
    def _compute_km(self):
        """Calculate distance as the difference between odometer readings."""
        for record in self:
            record.km = max(record.odometer_end - record.odometer_start, 0)

    @api.depends("manager_id", "date")
    def _compute_fuel_data(self):
        """Fetch last entered fuel data for calculations."""
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
        """Calculate fuel expenses based on distance and fuel consumption."""
        for record in self:
            record.fuel_expenses = (
                                               record.km * record.fuel_consumption_per_100km / 100) * record.fuel_price_per_liter

    @api.depends("km", "depreciation_rate")
    def _compute_depreciation_expenses(self):
        """Calculate depreciation expenses."""
        for record in self:
            record.depreciation_expenses = record.km * record.depreciation_rate

    @api.depends("fuel_expenses", "depreciation_expenses")
    def _compute_total_expenses(self):
        """Calculate total expenses (fuel + depreciation)."""
        for record in self:
            record.total_expenses = record.fuel_expenses + record.depreciation_expenses
