"""Test cases for the manager.work.day model.

Covers creation of work day records and expense computations
(fuel, depreciation, total).
"""

from odoo.tests import TransactionCase


class TestManagerWorkDay(TransactionCase):
    """
    This class contains test cases for the 'manager.work.day' model.
    It includes tests for creating work day records, as well as calculating
    fuel expenses, depreciation expenses,
    and total expenses based on work day data.
    """

    def test_create_work_day(self):
        """Test creation of work day record"""
        manager = self.env["budget.sales.manager"].create({
            "manager_id": self.env.user.id
        })
        work_day = self.env["manager.work.day"].create({
            "manager_id": manager.id,
            "date": "2025-03-01",
            "odometer_start": 100.0,
            "odometer_end": 150.0
        })
        self.assertEqual(work_day.km, 50.0)

    def test_compute_expenses(self):
        """Test fuel and depreciation expense calculations"""
        manager = self.env["budget.sales.manager"].create({
            "manager_id": self.env.user.id
        })

        self.env["fuel.prices"].create({
            "manager_id": manager.id,
            "date": "2025-03-01",
            "fuel_price": 2.5,
            "consumption": 8.0,
            "depreciation": 1.0
        })

        work_day = self.env["manager.work.day"].create({
            "manager_id": manager.id,
            "date": "2025-03-01",
            "odometer_start": 100.0,
            "odometer_end": 150.0
        })

        work_day._compute_fuel_expenses()
        work_day._compute_depreciation_expenses()
        work_day._compute_total_expenses()

        self.assertGreater(work_day.total_expenses, 0.0)
