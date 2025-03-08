{
    "name": "Budget Sales Tracking",
    "summary": "Tracking work days, mileage,"
               "and finances of budget sales managers",
    "description": "This module allows tracking workdays, mileage,"
                   "and financial transactions of budget sales managers.",
    "author": "Your Name",
    # "website": "https://yourwebsite.com",
    "category": "Sales",
    "version": "1.0",
    "depends": ["base", "sale", "account"],
    "data": [
        "security/security_rules.xml",
        "security/ir.model.access.csv",
        "views/budget_sales_manager_views.xml",
        "views/manager_work_day_views.xml",
        "views/manager_finance_views.xml",
        "views/fuel_prices_views.xml",
        "wizard/fuel_price_update.xml",
        "views/menu_views.xml",
        # "views/log_changes_views.xml",
        # "reports/finance_report_template.xml",
        # "data/demo_data.xml",
    ],
    "demo": ["data/demo_data.xml"],
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
    'images': [
        'static/description/icon.png'
    ],
}
