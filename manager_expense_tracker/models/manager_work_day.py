from odoo import models, fields, api

class ManagerWorkDay(models.Model):
    _name = "manager.work.day"
    _description = "Manager's Work Day"

    manager_id = fields.Many2one(
        "budget.sales.manager",
        string="Manager",
        required=True
    )
    date = fields.Date(
        required=True
    )
    start_time = fields.Float(
        string="Start Time",
        required=True
    )
    end_time = fields.Float(
        string="End Time",
        required=True
    )
    responsible_id = fields.Many2one(
        "res.users",
        string="Responsible Person",
        required=True
    )

    odometer_start = fields.Float(
        string="Odometer (Start of the Day)",
        required=True
    )
    odometer_end = fields.Float(
        string="Odometer (End of the Day)",
        required=True
    )
    distance = fields.Float(
        string="Distance (km)",
        compute="_compute_distance",
        store=True
    )
    is_holiday = fields.Boolean(
        string="Holiday"
    )

    @api.depends("odometer_start", "odometer_end")
    def _compute_distance(self):
        """Computes the distance traveled during the work day."""
        for record in self:
            record.distance = max(record.odometer_end -
                                  record.odometer_start, 0)
