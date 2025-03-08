from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class FuelPriceUpdateWizard(models.TransientModel):
    """ Wizard for updating fuel prices for a specific month """
    _name = "fuel.price.update.wizard"
    _description = "Fuel Price Update Wizard"

    month = fields.Char(
        string="Month",
        required=True,
        size=7,  # Format: YYYY-MM
        help=_("Specify the month (YYYY-MM) for which the fuel price should be updated.")
    )
    new_fuel_price = fields.Float(
        string=_("New Fuel Price (per liter)"),
        required=True,
        digits=(6, 2),
        help=_("Enter the new fuel price per liter.")
    )

    @api.constrains("new_fuel_price")
    def _check_positive_price(self):
        """ Ensure that the new fuel price is greater than zero """
        for record in self:
            if record.new_fuel_price <= 0:
                raise ValidationError(_("Fuel price must be greater than zero!"))

    def update_fuel_price(self):
        """ Update the fuel price for the given month """
        fuel_record = self.env["fuel.prices"].search([("month", "=", self.month)], limit=1)

        if fuel_record:
            fuel_record.fuel_price = self.new_fuel_price
        else:
            self.env["fuel.prices"].create({
                "month": self.month,
                "fuel_price": self.new_fuel_price,
                "consumption": 10.0,  # Default value
                "depreciation": 1.25,  # Default value
                "active": True
            })
