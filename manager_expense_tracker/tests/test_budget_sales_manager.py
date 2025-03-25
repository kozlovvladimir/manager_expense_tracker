from odoo.tests import TransactionCase

"""
This module contains test cases for the 'budget.sales.manager' model.
It includes tests for creating a new Budget Sales Manager and computing
the name based on the manager_id.
"""


class TestBudgetSalesManager(TransactionCase):
    """
    This class tests the functionality of the 'budget.sales.manager' model.
    It includes tests for creating a manager and checking name computation.
    """

    def test_create_budget_sales_manager(self):
        """Test creation of a new Budget Sales Manager"""
        manager = self.env["budget.sales.manager"].create({
            "manager_id": self.env.user.id,
            "phone": "123-456-789",
            "code_1c": "ABC123"
        })
        self.assertEqual(manager.name, self.env.user.name)
        self.assertEqual(manager.phone, "123-456-789")
        self.assertEqual(manager.code_1c, "ABC123")

    def test_compute_name(self):
        """Test name computation based on manager_id"""
        manager = self.env["budget.sales.manager"].create({
            "manager_id": self.env.user.id,
        })
        self.assertEqual(manager.name, self.env.user.name)
