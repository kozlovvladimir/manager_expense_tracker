from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta


class FuelPrices(models.Model):
    _name = "fuel.prices"
    _description = "Fuel Prices and Consumption Rates"
    _order = "date desc, id desc"

    manager_id = fields.Many2one(
        "budget.sales.manager",
        string="Manager",
        required=False,
        help="Select the manager for whom this price is set."
    )

    date = fields.Date(
        string="Date",
        required=True,
        help="Date when the fuel price was set."
    )

    fuel_price = fields.Float(
        string="Fuel Price (per liter)",
        required=True,
        digits=(6, 2),
        help="The price of fuel per liter for the given date."
    )

    consumption = fields.Float(
        string="Fuel Consumption (per 100 km)",
        required=True,
        digits=(6, 2),
        help="Fuel consumption rate per 100 km."
    )

    depreciation = fields.Float(
        string="Depreciation (per km)",
        required=True,
        default=1.25,
        digits=(6, 2),
        help="Depreciation cost per km."
    )

    active = fields.Boolean(
        default=True,
        help="Indicates whether this fuel price entry is currently active."
    )

    _sql_constraints = [
        ("unique_manager_date", "UNIQUE(manager_id, date)",
         "Fuel price for this manager and date already exists!")
    ]

    @api.model
    def _generate_dates(self, start_date, end_date):
        if start_date > end_date:
            raise ValidationError(_("Start date cannot be later than end date."))
        return [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range((end_date - start_date).days + 1)]

    def update_fuel_price(self, new_fuel_price, new_consumption, new_depreciation):
        for record in self:
            old_values = {
                "fuel_price": record.fuel_price,
                "consumption": record.consumption,
                "depreciation": record.depreciation
            }
            record.write({
                "fuel_price": new_fuel_price,
                "consumption": new_consumption,
                "depreciation": new_depreciation
            })
            record.message_post(
                body=_(
                    "Fuel price updated: {} → {} <br/>"
                    "Consumption updated: {} → {} <br/>"
                    "Depreciation updated: {} → {}"
                ).format(
                    old_values["fuel_price"], new_fuel_price,
                    old_values["consumption"], new_consumption,
                    old_values["depreciation"], new_depreciation
                )
            )

    def open_update_wizard(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Update Fuel Price",
            "res_model": "fuel.price.update.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_manager_id": self.manager_id.id,
                "default_date": self.date,
                "default_new_fuel_price": self.fuel_price,
                "default_new_consumption": self.consumption,
                "default_new_depreciation": self.depreciation
            },
        }

    def open_mass_update_wizard(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Mass Update Fuel Prices",
            "res_model": "fuel.price.update.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_manager_ids": [(6, 0, self.mapped("manager_id").ids)],
            }
        }

    def write(self, vals):
        res = super().write(vals)
        for record in self:
            reports = self.env['manager.daily.report'].search([
                ('manager_id', '=', record.manager_id.id),
                ('date', '=', record.date)
            ])
            for report in reports:
                report._compute_fuel_price()
                report._compute_fuel_expenses()
                report._compute_total_expenses()
                report._compute_balance()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            reports = self.env['manager.daily.report'].search([
                ('manager_id', '=', record.manager_id.id),
                ('date', '=', record.date)
            ])
            for report in reports:
                report._compute_fuel_price()
                report._compute_fuel_expenses()
                report._compute_total_expenses()
                report._compute_balance()
        return records
