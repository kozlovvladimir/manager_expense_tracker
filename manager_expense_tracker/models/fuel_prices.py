from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta

"""
This module defines the FuelPrices model, which tracks the fuel price history,
fuel consumption rates,
and depreciation costs for a specific manager.
It provides functionality for updating fuel prices,
generating reports based on fuel prices,
and ensuring data integrity for fuel-related transactions.
"""


class FuelPrices(models.Model):
    """
    This class defines the fuel prices
    and consumption rates for a specific manager.
    It tracks fuel price history, consumption, depreciation costs,
    and provides functionality
    for updating fuel prices and generating reports based on these prices.

    Fields:
    - manager_id: The manager associated with the fuel price record.
    - date: The date the fuel price was set.
    - fuel_price: The price of fuel per liter on the specified date.
    - consumption: The fuel consumption rate per 100 km.
    - depreciation: The depreciation cost per kilometer.
    - active: Indicates if this fuel price entry is currently active.
    """
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
        """
        Generates a list of dates between the start and end date, inclusive.

        Args:
            start_date (datetime.date): The start date.
            end_date (datetime.date): The end date.

        Returns:
            list: A list of dates between the start
            and end date in 'YYYY-MM-DD' format.

        Raises:
            ValidationError: If the start date is later than the end date.
        """
        if start_date > end_date:
            raise ValidationError(
                _("Start date cannot be later than end date."))
        return [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in
                range((end_date - start_date).days + 1)]

    def update_fuel_price(self, new_fuel_price, new_consumption,
                          new_depreciation):
        """
        Updates the fuel price, consumption,
        and depreciation values for the record
        and logs the changes.
        This method allows updating existing fuel price details.

        Args:
            new_fuel_price (float): The new fuel price.
            new_consumption (float): The new fuel consumption rate.
            new_depreciation (float): The new depreciation cost.
        """
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
        """
        Opens the fuel price update wizard for a single record,
        allowing managers to update
        fuel prices through a user-friendly interface.

        Returns:
            dict: The action dictionary to open the wizard form.
        """
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
        """
        Opens the mass fuel price update wizard for multiple records,
        allowing bulk updates
        of fuel prices for multiple managers at once.

        Returns:
            dict: The action dictionary to open the mass update wizard form.
        """
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
        """
        Overrides the write method to update related reports when fuel price
        records are modified.
        This ensures that related daily reports are recalculated based
        on the updated fuel price.

        Args:
            vals (dict): The field values to be updated.

        Returns:
            bool: The result of the write operation.
        """
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
        """
        Overrides the create method to update related reports
        after creating new fuel price records.
        This ensures that related reports are recalculated immediately
        after the creation of new records.

        Args:
            vals_list (list): The list of values for the new records.

        Returns:
            records: The created records.
        """
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
