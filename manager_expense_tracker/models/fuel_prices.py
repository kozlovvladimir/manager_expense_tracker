from odoo import models, fields, api, _, tools
from odoo.exceptions import ValidationError

class FuelPrices(models.Model):
    _name = "fuel.prices"
    _description = "Fuel Prices and Consumption Rates"
    _order = "month desc"

    month = fields.Char(
        required=True,
        size=7,
        help=_("The month for which the fuel price and consumption rate are set.")
    )
    fuel_price = fields.Float(
        string="Fuel Price (per liter)",
        required=True,
        digits=(6, 2),
        help=_("The price of fuel per liter for the given month.")
    )
    consumption = fields.Float(
        string="Fuel Consumption (per 100 km)",
        required=True,
        digits=(6, 2),
        help=_("Fuel consumption rate per 100 km.")
    )
    depreciation = fields.Float(
        string="Depreciation (per km)",
        required=True,
        default=1.25,
        digits=(6, 2),
        help=_("Depreciation cost per km (modifiable).")
    )
    active = fields.Boolean(
        default=True,
        help=_("Indicates whether this fuel price entry is currently active.")
    )

    _sql_constraints = [
        ("unique_month", "UNIQUE(month)",
         tools.ustr("Fuel price for this month already exists!"))
    ]

    @api.constrains("fuel_price", "consumption", "depreciation")
    def _check_positive_values(self):
        for record in self:
            if record.fuel_price <= 0:
                raise ValidationError(_("Fuel price must be greater than zero!"))
            if record.consumption <= 0:
                raise ValidationError(_("Fuel consumption must be greater than zero!"))
            if record.depreciation < 0:
                raise ValidationError(_("Depreciation cannot be negative!"))
