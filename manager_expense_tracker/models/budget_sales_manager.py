"""Defines the Budget Sales Manager model.

This model links budget sales managers to system users, storing their
contact information, 1C integration code, and relationships with fuel price
and finance records. It is essential for managing and tracking the
operational and financial data of sales managers.
"""

from odoo import models, fields, api

"""
This module defines the Budget Sales Manager model,
which links budget sales managers to users
and manages their contact details, integration with the 1C system,
and relationships with fuel prices
and financial records. It provides fields to store essential information
about the manager and their
associated financial and fuel data.

The model includes:
- A computed 'name' field, derived from the manager's associated user's name.
- A 'manager_id' field that links the budget sales manager to a user (manager).
- Fields for storing the manager's phone number and integration code with 1C.
- Relationships to store fuel prices
and financial records linked to the manager.

The model is essential for tracking budget sales managers' activities,
financials, and fuel pricing.
"""


class BudgetSalesManager(models.Model):
    """
    This class represents the Budget Sales Manager model in the system.
    It links budget sales managers to users
    and manages their contact information,
    integration with the 1C system, and relationships with fuel prices
    and financial records.

    Fields:
    - name: The name of the budget sales manager,
    computed from the associated manager's name.
    - manager_id: A reference to the res.users model,
    linking a manager to the budget sales manager.
    - phone: The phone number of the manager.
    - active: A boolean indicating whether the record is active.
    - code_1c: A unique identifier for integration with the 1C system.
    - fuel_price_ids: A one-to-many relationship
    linking the fuel prices to the manager.
    - finances_ids: A one-to-many relationship
    linking the financial records to the manager.
    """
    _name = "budget.sales.manager"
    _description = "Budget Sales Manager"

    # Name of the budget sales manager, computed based on the manager's name
    name = fields.Char(
        compute="_compute_name",
        store=True
    )

    # Many-to-one relation with the res.users model to link a manager
    # to the budget sales manager
    manager_id = fields.Many2one(
        comodel_name="res.users",
        string="Manager",
        required=True
    )

    # Phone number of the manager
    phone = fields.Char()

    # Indicates if the budget sales manager record is active
    active = fields.Boolean(default=True)

    # Unique identifier for integration with 1C system
    code_1c = fields.Char(
        size=50,
        help="Unique identifier for integration with 1C system"
    )

    # One-to-many relationship to the fuel.prices model,
    # linking fuel prices to the manager
    fuel_price_ids = fields.One2many(
        "fuel.prices",
        "manager_id",
        string="Fuel Prices"
    )

    # One-to-many relationship to the manager.finance model,
    # linking financial records to the manager
    finances_ids = fields.One2many(
        "manager.finance",
        "manager_id",
        string="Financial Records"
    )

    @api.depends("manager_id")
    def _compute_name(self):
        """
        Automatically fills in the manager's name based
        on the related manager.
        This method ensures that the 'name' field
        is updated whenever the manager
        associated with the sales manager changes.
        """
        for record in self:
            record.name = (
                record.manager_id.name) if record.manager_id else "N/A"

    @api.depends("manager_id")
    def _compute_display_name(self):
        """
        Computes the display name for the manager using the manager's name.
        """
        for record in self:
            record.display_name = record.manager_id.name
