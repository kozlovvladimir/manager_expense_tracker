"""
This module handles the work days, mileage, and financial transactions
of budget sales managers. It includes tracking of fuel prices, manager
finances, daily reports, and work day records. The module integrates with
Odoo's HR, accounting, fleet, and sales modules to provide a comprehensive
solution for budget sales management.

It includes views, reports, wizards, and security rules for managing the
entire workflow for budget sales managers.
"""

# Your imports and other initializations
from . import models
from . import wizard
