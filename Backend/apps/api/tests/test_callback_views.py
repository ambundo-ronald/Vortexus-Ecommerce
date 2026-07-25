from datetime import datetime
from zoneinfo import ZoneInfo

from django.test import SimpleTestCase

from apps.api.callback_views import callback_respond_by


class CallbackRespondByTests(SimpleTestCase):
    timezone = ZoneInfo('Africa/Nairobi')

    def deadline(self, year, month, day, hour):
        created_at = datetime(year, month, day, hour, tzinfo=self.timezone)
        return callback_respond_by(created_at).astimezone(self.timezone)

    def test_request_during_workday_is_due_three_hours_later(self):
        self.assertEqual(self.deadline(2026, 7, 27, 10), datetime(2026, 7, 27, 13, tzinfo=self.timezone))

    def test_evening_request_rolls_remaining_time_to_next_workday(self):
        self.assertEqual(self.deadline(2026, 7, 27, 19), datetime(2026, 7, 28, 9, tzinfo=self.timezone))

    def test_friday_evening_request_rolls_to_monday(self):
        self.assertEqual(self.deadline(2026, 7, 31, 19), datetime(2026, 8, 3, 9, tzinfo=self.timezone))

    def test_weekend_request_starts_sla_on_monday(self):
        self.assertEqual(self.deadline(2026, 8, 1, 10), datetime(2026, 8, 3, 10, tzinfo=self.timezone))
