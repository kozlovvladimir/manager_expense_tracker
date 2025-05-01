from odoo import models, fields, api, _
import requests
from bs4 import BeautifulSoup
import logging
import traceback

_logger = logging.getLogger(__name__)


class FuelPriceHistory(models.Model):
    _name = 'fuel.price.history'
    _description = 'WOG Fuel Price History (A-95 Euro5 only)'
    _rec_name = 'date'  # The name of the entry is the date

    date = fields.Date(
        required=True,
        default=fields.Date.today,
        index=True,
        help=_("Date when the fuel price was recorded.")
    )
    price = fields.Float(
        string='A-95 Price (UAH/L)',
        required=True,
        help=_("Price of A-95 Euro5 fuel in UAH per liter.")
    )

    def fetch_a95_price_button(self):
        # Calling the basic logic
        result = self._fetch_and_save()

        # If successfully updated, reload the form
        if isinstance(
                result, dict
        ) and result.get("params", {}).get("type") == "success":
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }

        return result

    @api.model
    def fetch_a95_price(self, *args, **kwargs):
        # Call via server action
        return self._fetch_and_save()

    def _fetch_and_save(self):
        """Fetch and store the A-95 Euro5 fuel price
        from Minfin WOG page using requests."""
        url = "https://index.minfin.com.ua/markets/fuel/tm/wog/"
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"
                          " AppleWebKit/537.36 (KHTML, like Gecko)"
                          " Chrome/136 Safari/537.36"
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            html = response.text
        except Exception as e:
            _logger.error("❌ Failed to fetch page:\n%s",
                          traceback.format_exc())
            return self._notify_error(_('Connection Error'),
                                      _('Failed to fetch fuel price page: %s')
                                      % str(e))

        soup = BeautifulSoup(html, "html.parser")
        tables = soup.find_all("table")

        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True)
                    if ("А-95 Євро 5" in label or "A-95 Euro 5" in label or
                            "А-95 Евро 5" in label):
                        try:
                            price_tag = row.find("big")
                            if not price_tag:
                                _logger.warning(
                                    "No <big> tag found in row: %s",
                                    row
                                )
                                continue
                            price_raw = price_tag.get_text(strip=True).replace(
                                ",", ".")
                            price_value = float(price_raw)
                        except Exception:
                            return self._notify_error(_('Parsing Error'),
                                                      _('Could not parse '
                                                        'A-95 price value.'))

                        if not price_value or price_value == 0.0:
                            _logger.warning(
                                "Parsed price is zero or invalid: %s",
                                price_raw)
                            return self._notify_warning(
                                _('Parsed price is 0.0 '
                                  '— skipping record creation.'))

                        today = fields.Date.today()
                        existing_record = self.env[
                            'fuel.price.history'
                        ].search([('date', '=', today)], limit=1)

                        if existing_record:
                            if existing_record.price == 0:
                                existing_record.write({'price': price_value})
                                _logger.info(
                                    "Updated A-95 price "
                                    "to %.2f UAH for %s", price_value,
                                    today)
                                return {
                                    'type': 'ir.actions.client',
                                    'tag': 'display_notification',
                                    'params': {
                                        'title': _('Success'),
                                        'message': _(
                                            'A-95 Euro5 price updated:'
                                            ' %.2f UAH' % price_value),
                                        'type': 'success',
                                        'next': {'type': 'ir.actions.client',
                                                 'tag': 'reload'},
                                    }
                                }
                            else:
                                return self._notify_info(
                                    _('A-95 price for today already exists.'))
                        else:
                            self.env['fuel.price.history'].create({
                                'price': price_value,
                                'date': today
                            })
                            _logger.info(
                                "Created A-95 price %.2f UAH for %s",
                                price_value, today)
                            return {
                                'type': 'ir.actions.client',
                                'tag': 'display_notification',
                                'params': {
                                    'title': _('Success'),
                                    'message': _(
                                        'A-95 Euro5 price saved: %.2f UAH'
                                        % price_value),
                                    'type': 'success',
                                    'next': {
                                        'type': 'ir.actions.client',
                                        'tag': 'reload'},
                                }
                            }

        with open('/tmp/wog_debug.html', 'w', encoding='utf-8') as f:
            f.write(html)

        return self._notify_warning(
            _('A-95 Euro5 price not found on Minfin page.'))

    def _notify_success(self, message):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }

    def _notify_info(self, message):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Info'),
                'message': message,
                'type': 'info',
                'sticky': False,
            }
        }

    def _notify_warning(self, message):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Warning'),
                'message': message,
                'type': 'warning',
                'sticky': True,
            }
        }

    def _notify_error(self, title, message):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'type': 'danger',
                'sticky': True,
            }
        }
