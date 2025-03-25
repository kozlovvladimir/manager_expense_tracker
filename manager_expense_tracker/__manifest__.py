# """
# This module tracks workdays, mileage, and financial transactions
# of budget sales managers.
# It integrates with Odoo's HR, accounting, fleet,
# and sales modules to provide a complete
# solution for managing sales budgets, including work day tracking,
# fuel prices, financial records,
# and daily reports.
# """

{
    "name": "Budget Sales Tracking",
    "summary": "Tracking work days, mileage,"
               "and finances of budget sales managers",
    "description": "This module allows tracking workdays, mileage, "
                   "and financial transactions of budget sales managers.",
    "author": "Your Name",
    "category": "Sales",
    "version": "1.0",
    "depends": ["base", "sale", "account", "hr_expense", "fleet"],
    "data": [
        "security/security_rules.xml",
        "security/ir.model.access.csv",
        "views/budget_sales_manager_views.xml",
        "views/manager_work_day_views.xml",
        "views/manager_finance_views.xml",
        "views/fuel_prices_views.xml",
        "wizard/fuel_price_update.xml",
        "report/finance_report_template.xml",
        "views/manager_daily_report_views.xml",
        "views/menu_views.xml",
    ],
    "demo": [
        "demo/budget_sales_manager_demo.xml",
        "demo/fuel_prices_demo.xml",
        "demo/manager_finance_demo.xml",
        "demo/manager_work_day_demo.xml",
        "demo/manager_daily_report_demo.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
    "images": [
        "static/description/icon.png"
    ],
    "assets": {
        "web.assets_backend": [
            "manager_expense_tracker/static/src/css/custom_styles.css",
        ],
    },
}
