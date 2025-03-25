from odoo.tests import TransactionCase

"""
This module contains test cases for the 'manager.finance' model.
It includes tests for creating finance records, computing the balance,
and ensuring the correct calculation of income and expenses for budget sales managers.
"""

class TestManagerFinance(TransactionCase):
    """
    This class tests the functionality of the 'manager.finance' model.
    It includes tests for creating finance records, checking the balance computation
    based on income and expenses, and ensuring that the calculations are correct.
    """

    def test_create_manager_finance(self):
        """Test creation of finance record"""
        manager = self.env["budget.sales.manager"].create({
            "manager_id": self.env.user.id
        })
        finance = self.env["manager.finance"].create({
            "manager_id": manager.id,
            "date": "2025-03-01",
            "income": 1000.0,
            "expenses_other": 200.0
        })
        self.assertEqual(finance.income, 1000.0)
        self.assertEqual(finance.expenses_other, 200.0)

    def test_compute_balance(self):
        """Test balance computation for finance"""
        manager = self.env["budget.sales.manager"].create({
            "manager_id": self.env.user.id
        })
        finance = self.env["manager.finance"].create({
            "manager_id": manager.id,
            "date": "2025-03-01",
            "income": 1000.0,
            "expenses_other": 200.0
        })
        self.assertEqual(finance.balance, 800.0)
