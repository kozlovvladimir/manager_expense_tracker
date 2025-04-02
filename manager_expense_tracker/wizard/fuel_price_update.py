"""Wizard for mass updating fuel prices, consumption, and depreciation."""

from odoo import models, fields


class FuelPriceUpdateWizard(models.TransientModel):
    """
    Transient model for mass updating fuel prices, fuel consumption,
    and depreciation rates for selected managers within a date range.
    """
    _name = 'fuel.price.update.wizard'
    _description = 'Fuel Price Mass Update Wizard'

    manager_ids = fields.Many2many('budget.sales.manager', string='Managers')
    date_start = fields.Date(string='Start Date', required=True)
    date_end = fields.Date(string='End Date', required=True)
    new_fuel_price = fields.Float(string='New Fuel Price', required=True)
    new_consumption = fields.Float(string='New Consumption', required=True)
    new_depreciation = fields.Float(string='New Depreciation', required=True)

    def update_fuel_prices(self):
        """
        Updates or creates fuel price records for selected managers
        between the specified dates.
        """
        fuel_price_model = self.env['fuel.prices']
        for wizard in self:
            # Yes,
            # accessing protected _generate_dates — can’t avoid it if needed
            dates = fuel_price_model._generate_dates(
                wizard.date_start, wizard.date_end
            )

            for manager in wizard.manager_ids:
                for date_str in dates:
                    date = fields.Date.from_string(date_str)
                    fuel_price = fuel_price_model.search([
                        ('manager_id', '=', manager.id),
                        ('date', '=', date)
                    ], limit=1)

                    if fuel_price:
                        fuel_price.update_fuel_price(
                            wizard.new_fuel_price,
                            wizard.new_consumption,
                            wizard.new_depreciation
                        )
                    else:
                        fuel_price_model.create({
                            'manager_id': manager.id,
                            'date': date,
                            'fuel_price': wizard.new_fuel_price,
                            'consumption': wizard.new_consumption,
                            'depreciation': wizard.new_depreciation
                        })
