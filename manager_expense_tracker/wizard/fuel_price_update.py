from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FuelPriceUpdateWizard(models.TransientModel):
    _name = "fuel.price.update.wizard"
    _description = "Fuel Price Update Wizard"

    manager_ids = fields.Many2many(
        "budget.sales.manager",
        string="Managers",
        required=True,
        help="Select managers for whom the price should be updated."
    )

    date_start = fields.Date(
        string="Start Date",
        required=True,
        help="Specify the start date for the fuel price update."
    )

    date_end = fields.Date(
        string="End Date",
        required=True,
        help="Specify the end date for the fuel price update."
    )

    new_fuel_price = fields.Float(
        string="New Fuel Price (per liter)",
        required=True,
        digits=(6, 2),
        help="Enter the new fuel price per liter."
    )

    new_consumption = fields.Float(
        string="New Fuel Consumption (per 100 km)",
        required=True,
        digits=(6, 2),
        default=10.0,
        help="Enter the new fuel consumption rate."
    )

    new_depreciation = fields.Float(
        string="New Depreciation (per km)",
        required=True,
        digits=(6, 2),
        help="Enter the new depreciation cost per km."
    )

    @api.constrains("new_fuel_price", "new_consumption", "new_depreciation")
    def _check_positive_values(self):
        """ Ensure that values are positive """
        for record in self:
            if record.new_fuel_price <= 0:
                raise ValidationError(_("Fuel price must be greater than zero!"))
            if record.new_consumption <= 0:
                raise ValidationError(_("Fuel consumption must be greater than zero!"))
            if record.new_depreciation < 0:
                raise ValidationError(_("Depreciation cannot be negative!"))

    def update_fuel_prices(self):
        """ Update or create fuel prices for selected managers and date range """
        FuelPrices = self.env["fuel.prices"]
        for manager in self.manager_ids:
            dates = self.env["fuel.prices"]._generate_dates(self.date_start, self.date_end)
            for date in dates:
                fuel_record = FuelPrices.search([
                    ("manager_id", "=", manager.id),
                    ("date", "=", date)
                ], limit=1)

                if fuel_record:
                    fuel_record.write({
                        "fuel_price": self.new_fuel_price,
                        "consumption": self.new_consumption,
                        "depreciation": self.new_depreciation
                    })
                    fuel_record.message_post(body=f"Fuel price updated to {self.new_fuel_price}")
                else:
                    FuelPrices.create({
                        "manager_id": manager.id,
                        "date": date,
                        "fuel_price": self.new_fuel_price,
                        "consumption": self.new_consumption,
                        "depreciation": self.new_depreciation,
                        "active": True
                    })
