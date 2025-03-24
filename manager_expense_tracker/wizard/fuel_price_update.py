from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FuelPriceUpdateWizard(models.TransientModel):
    _name = 'fuel.price.update.wizard'
    _description = 'Fuel Price Mass Update Wizard'

    manager_ids = fields.Many2many('budget.sales.manager', string='Managers')
    date_start = fields.Date(string='Start Date', required=True)
    date_end = fields.Date(string='End Date', required=True)
    new_fuel_price = fields.Float(string='New Fuel Price', required=True)
    new_consumption = fields.Float(string='New Consumption', required=True)
    new_depreciation = fields.Float(string='New Depreciation', required=True)

    def update_fuel_prices(self):
        FuelPrice = self.env['fuel.prices']
        for wizard in self:
            dates = FuelPrice._generate_dates(wizard.date_start, wizard.date_end)
            for manager in wizard.manager_ids:
                for date_str in dates:
                    date = fields.Date.from_string(date_str)
                    fuel_price = FuelPrice.search([
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
                        FuelPrice.create({
                            'manager_id': manager.id,
                            'date': date,
                            'fuel_price': wizard.new_fuel_price,
                            'consumption': wizard.new_consumption,
                            'depreciation': wizard.new_depreciation
                        })
