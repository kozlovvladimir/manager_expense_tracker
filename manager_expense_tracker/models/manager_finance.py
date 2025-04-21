from odoo import models, fields, api


class ManagerFinance(models.Model):
    """
    Financial data model for budget sales managers.
    Tracks income, manual and automatic expenses, balance,
    and fuel price information per date.
    """

    _name = "manager.finance"
    _description = "Manager's Finance"

    manager_id = fields.Many2one(
        comodel_name="budget.sales.manager",
        string="Manager",
        required=True
    )

    date = fields.Date(required=True)

    income = fields.Float(required=True)

    expenses_other = fields.Float(
        string="Other Expenses",
        required=True
    )

    expenses_auto = fields.Float(
        string="Auto Expenses",
        compute="_compute_auto_expenses",
        store=True
    )

    initial_balance = fields.Float(
        string="Initial Balance",
        store=True,
        readonly=True
    )

    balance = fields.Float(
        string="Balance",
        compute="_compute_balance",
        store=True
    )

    approved = fields.Boolean(string="Approved")

    fuel_price_id = fields.Many2one(
        "fuel.prices",
        string="Fuel Price Record",
        compute="_compute_fuel_price",
        store=True
    )

    @api.depends(
        "income", "expenses_other", "expenses_auto", "initial_balance"
    )
    def _compute_balance(self):
        """Calculate balance = initial + income - (manual + auto expenses)."""
        for record in self:
            record.balance = (
                    record.initial_balance +
                    record.income -
                    (record.expenses_other + record.expenses_auto)
            )

    @api.depends(
        "manager_id", "date",
        "manager_id.fuel_price_ids.fuel_price",
        "manager_id.fuel_price_ids.consumption",
        "manager_id.fuel_price_ids.depreciation",
        "manager_id.fuel_price_ids.date",
        "manager_id.fuel_price_ids.write_date",
    )
    def _compute_auto_expenses(self):
        """
        Compute auto expenses based on distance, consumption, depreciation.
        Auto-expense = fuel_cost + depreciation, if work_day exists.
        """
        for record in self:
            if not record.manager_id or not record.date:
                record.expenses_auto = 0
                continue

            work_day = self.env["manager.work.day"].search([
                ("manager_id", "=", record.manager_id.id),
                ("date", "=", record.date)
            ], limit=1)

            fuel_data = self.env["fuel.prices"].sudo().search([
                ("manager_id", "=", record.manager_id.id),
                ("date", "<=", record.date)
            ], order="date desc", limit=1)

            record.fuel_price_id = fuel_data

            if work_day and fuel_data:
                fuel_consumption = work_day.km * fuel_data.consumption / 100
                fuel_cost = fuel_consumption * fuel_data.fuel_price
                depreciation_cost = work_day.km * fuel_data.depreciation
                record.expenses_auto = fuel_cost + depreciation_cost
            else:
                record.expenses_auto = 0

    @api.depends(
        "manager_id", "date",
        "manager_id.fuel_price_ids.fuel_price",
        "manager_id.fuel_price_ids.consumption",
        "manager_id.fuel_price_ids.depreciation",
        "manager_id.fuel_price_ids.date",
        "manager_id.fuel_price_ids.write_date"
    )
    def _compute_fuel_price(self):
        """
        Get most recent fuel price before or on the current record's date.
        """
        for record in self:
            record.fuel_price_id = self.env["fuel.prices"].search([
                ("manager_id", "=", record.manager_id.id),
                ("date", "<=", record.date)
            ], order="date desc", limit=1)

    @api.onchange("manager_id", "date")
    def _onchange_initial_balance(self):
        """
        Auto-fill initial balance when manager or date is changed.
        """
        if self.manager_id and self.date:
            previous = self.search([
                ("manager_id", "=", self.manager_id.id),
                ("date", "<", self.date)
            ], order="date desc", limit=1)
            self.initial_balance = previous.balance if previous else 0.0

    def write(self, vals):
        """
        Sync financial changes (income, expenses, balance)
        with manager.daily.report if exists, and update following reports.
        """
        res = super().write(vals)
        for record in self:
            if not self.env.context.get("sync_from_report"):
                report = self.env["manager.daily.report"].search([
                    ("manager_id", "=", record.manager_id.id),
                    ("date", "=", record.date)
                ], limit=1)
                if report:
                    report.with_context(sync_from_finance=True).write({
                        "income": record.income,
                        "expenses_manual": record.expenses_other,
                        "balance": record.balance,
                    })
            record._update_following_daily_reports()
        return res

    def _update_following_daily_reports(self):
        """
        Update all following daily reports' initial_balance and balance
        starting from the day after current record.
        """
        for record in self:
            # We receive all the following daily reports
            next_reports = self.env["manager.daily.report"].search([
                ("manager_id", "=", record.manager_id.id),
                ("date", ">", record.date)
            ], order="date")

            prev_balance = record.balance

            for report in next_reports:
                report.initial_balance = prev_balance
                report._compute_total_expenses()
                report._compute_balance()
                prev_balance = report.balance

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            # Find a previous financial record
            previous = self.search([
                ("manager_id", "=", record.manager_id.id),
                ("date", "<", record.date)
            ], order="date desc", limit=1)

            record.initial_balance = previous.balance if previous else 0

            # Sync or create a daily report
            daily = self.env["manager.daily.report"].search([
                ("manager_id", "=", record.manager_id.id),
                ("date", "=", record.date)
            ], limit=1)
            if not daily:
                self.env["manager.daily.report"].create({
                    "manager_id": record.manager_id.id,
                    "date": record.date,
                    "income": record.income,
                    "expenses_manual": record.expenses_other,
                    "initial_balance": record.initial_balance,
                })
        return records

    def _should_remove_daily_report(self, manager_id, date):
        work_day_exists = self.env["manager.work.day"].search_count([
            ("manager_id", "=", manager_id),
            ("date", "=", date)
        ]) > 0

        finance_exists = self.env["manager.finance"].search_count([
            ("manager_id", "=", manager_id),
            ("date", "=", date),
            ("id", "!=", self.id)
        ]) > 0

        return not work_day_exists and not finance_exists

    def unlink(self):
        if self.env.context.get("from_daily_report"):
            return super().unlink()

        def _is_zero_or_none(val):
            return val is None or abs(val) < 0.0001

        for record in self:
            report = self.env["manager.daily.report"].search([
                ("manager_id", "=", record.manager_id.id),
                ("date", "=", record.date)
            ], limit=1)

            if report:
                if self._should_remove_daily_report(record.manager_id.id,
                                                    record.date):
                    report.unlink()
                else:
                    report.with_context(sync_from_finance=True).write({
                        "income": 0.0,
                        "expenses_manual": 0.0,
                        "initial_balance": 0.0,
                    })

        return super().unlink()






