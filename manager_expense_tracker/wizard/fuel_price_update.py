"""
This module defines the wizard for mass updating fuel prices, fuel consumption,
and depreciation rates for selected managers within a specified date range.
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FuelPriceUpdateWizard(models.TransientModel):
    """
    This transient model allows the mass update of fuel prices,
    fuel consumption rates,
    and depreciation rates for selected managers within a specified date range.
    It provides a user interface for selecting managers
    and specifying the new fuel price,
    consumption, and depreciation values.

    Fields:
    - manager_ids: Many-to-many relation with the budget.sales.manager model,
    to select managers.
    - date_start: The start date of the mass update period.
    - date_end: The end date of the mass update period.
    - new_fuel_price: The new fuel price to be applied
    to the selected managers.
    - new_consumption: The new fuel consumption rate to be applied.
    - new_depreciation: The new depreciation rate to be applied.
    """
    _name = 'fuel.price.update.wizard'
    _description = 'Fuel Price Mass Update Wizard'

    # Many-to-many relation with the budget.sales.manager model
    # to select the managers for updating fuel prices
    manager_ids = fields.Many2many('budget.sales.manager', string='Managers')

    # Start date for the mass fuel price update
    date_start = fields.Date(string='Start Date', required=True)

    # End date for the mass fuel price update
    date_end = fields.Date(string='End Date', required=True)

    # New fuel price to be applied
    new_fuel_price = fields.Float(string='New Fuel Price', required=True)

    # New fuel consumption rate to be applied
    new_consumption = fields.Float(string='New Consumption', required=True)

    # New depreciation rate to be applied
    new_depreciation = fields.Float(string='New Depreciation', required=True)

    def update_fuel_prices(self):
        """
        Updates fuel prices, consumption,
        and depreciation for the selected managers
        between the specified start and end dates.
        If a fuel price entry already exists,
        it is updated.
        Otherwise, a new entry is created for each manager and date.

        This method is used when the user triggers the mass update process.
        It will loop through each manager
        and each date in the specified range and apply
        the changes to the corresponding fuel price records.
        """
        FuelPrice = self.env['fuel.prices']
        for wizard in self:
            # Generate a list of dates between the start and end dates
            dates = FuelPrice._generate_dates(wizard.date_start,
                                              wizard.date_end)

            for manager in wizard.manager_ids:
                for date_str in dates:
                    # Convert the string date to a date object
                    date = fields.Date.from_string(date_str)

                    # Search for existing fuel price record
                    # for the manager and date
                    fuel_price = FuelPrice.search([
                        ('manager_id', '=', manager.id),
                        ('date', '=', date)
                    ], limit=1)

                    if fuel_price:
                        # If record exists, update fuel price, consumption,
                        # and depreciation
                        fuel_price.update_fuel_price(
                            wizard.new_fuel_price,
                            wizard.new_consumption,
                            wizard.new_depreciation
                        )
                    else:
                        # If no record exists, create a new fuel price entry
                        FuelPrice.create({
                            'manager_id': manager.id,
                            'date': date,
                            'fuel_price': wizard.new_fuel_price,
                            'consumption': wizard.new_consumption,
                            'depreciation': wizard.new_depreciation
                        })
