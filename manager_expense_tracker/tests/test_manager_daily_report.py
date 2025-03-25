from odoo.tests import TransactionCase

"""
This model defines the test cases for the `manager.daily.report` model.
It includes tests for creating daily reports, computing the balance, and 
verifying the correct calculations for income, expenses, and balance.
"""

class TestManagerDailyReport(TransactionCase):
    """
    This class contains test cases for the 'manager.daily.report' model.
    It includes tests for creating daily reports and computing the balance
    based on income and expenses.
    """

    def test_create_daily_report(self):
        """Test creation of daily report"""
        manager = self.env["budget.sales.manager"].create({
            "manager_id": self.env.user.id
        })
        report = self.env["manager.daily.report"].create({
            "manager_id": manager.id,
            "date": "2025-03-01",
            "income": 100.0,
            "expenses_manual": 20.0
        })
        self.assertEqual(report.income, 100.0)
        self.assertEqual(report.expenses_manual, 20.0)

    def test_compute_balance(self):
        """Test balance computation"""
        manager = self.env["budget.sales.manager"].create({
            "manager_id": self.env.user.id
        })
        report = self.env["manager.daily.report"].create({
            "manager_id": manager.id,
            "date": "2025-03-01",
            "income": 100.0,
            "expenses_manual": 20.0
        })
        self.assertEqual(report.balance, 80.0)
