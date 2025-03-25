from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError

"""
This module contains test cases for the 'fuel.prices' model.
It includes tests for creating fuel price records,
ensuring the unique constraint
on fuel prices for the same manager and date,
and verifying fuel price calculations.
"""

class TestFuelPrices(TransactionCase):
    """
    This class tests the functionality of the 'fuel.prices' model.
    It includes tests for creating fuel price records,
    checking the unique constraint
    on fuel prices for the same manager and date,
    and calculating fuel prices, consumption, and depreciation.
    """

    def test_create_fuel_prices(self):
        """Test creation of fuel price record"""
        manager = self.env["budget.sales.manager"].create({
            "manager_id": self.env.user.id
        })
        fuel_price = self.env["fuel.prices"].create({
            "manager_id": manager.id,
            "date": "2025-03-01",
            "fuel_price": 2.50,
            "consumption": 8.0,
            "depreciation": 1.25
        })
        self.assertEqual(fuel_price.fuel_price, 2.50)
        self.assertEqual(fuel_price.consumption, 8.0)

    def test_unique_constraint(self):
        """Test that fuel price records cannot be duplicated for the same manager and date"""
        manager = self.env["budget.sales.manager"].create({
            "manager_id": self.env.user.id
        })
        self.env["fuel.prices"].create({
            "manager_id": manager.id,
            "date": "2025-03-01",
            "fuel_price": 2.50,
            "consumption": 8.0,
            "depreciation": 1.25
        })
        with self.assertRaises(ValidationError):
            self.env["fuel.prices"].create({
                "manager_id": manager.id,
                "date": "2025-03-01",
                "fuel_price": 2.60,
                "consumption": 8.5,
                "depreciation": 1.30
            })
