from odoo.tests import TransactionCase

"""
This model defines the test cases for the `manager.work.day` model.
It includes tests for creating work day records, calculating fuel expenses,
depreciation expenses, and total expenses based on work day data.
"""


class TestManagerWorkDay(TransactionCase):
    """
    This class contains test cases for the 'manager.work.day' model.
    It includes tests for creating work day records, as well as calculating
    fuel expenses, depreciation expenses,
    and total expenses based on work day data.
    """

    def test_create_work_day(self):
        """Test creation of work day record"""
        # Create a new manager record
        manager = self.env["budget.sales.manager"].create({
            "manager_id": self.env.user.id
        })
        # Create a new work day record
        work_day = self.env["manager.work.day"].create({
            "manager_id": manager.id,
            "date": "2025-03-01",
            "odometer_start": 100.0,
            "odometer_end": 150.0
        })
        # Check that the distance (km) is correctly calculated
        self.assertEqual(work_day.km, 50.0)

    def test_compute_expenses(self):
        """Test fuel and depreciation expense calculations"""
        # Create a new manager record
        manager = self.env["budget.sales.manager"].create({
            "manager_id": self.env.user.id
        })
        # Create a new work day record
        work_day = self.env["manager.work.day"].create({
            "manager_id": manager.id,
            "date": "2025-03-01",
            "odometer_start": 100.0,
            "odometer_end": 150.0
        })

        # Instead of directly accessing protected methods,
        # use public methods if possible
        work_day._compute_fuel_expenses()
        # Internal method for fuel expense calculation
        work_day._compute_depreciation_expenses()
        # Internal method for depreciation calculation
        work_day._compute_total_expenses()
        # Internal method for total expenses calculation

        # Check that total expenses are greater than 0
        self.assertGreater(work_day.total_expenses, 0.0)
