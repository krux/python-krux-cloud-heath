# -*- coding: utf-8 -*-
#
# © 2016-2018 Salesforce.com, inc.
#

#
# Standard libraries
#

from __future__ import absolute_import
import unittest
import pprint
from datetime import datetime, timedelta
import calendar
from StringIO import StringIO
import re

#
# Third party libraries
#

from mock import MagicMock, patch
from six import iteritems

#
# Internal libraries
#

from krux_cloud_health import __version__
from krux_cloud_health.cloud_health import Interval
from bin.cloud_health_to_graphite import Application, main


class CloudHealthAPITest(unittest.TestCase):

    NAME = 'cloud-health-tech'
    API_KEY = '12345'
    REPORT_ID = 67890L
    REPORT_ID_ARG = str(REPORT_ID)
    REPORT_NAME_ARG = 'fake report'
    REPORT_NAME = re.sub('[ \.]+', '_', REPORT_NAME_ARG)
    SET_DATE = '2016-05-01'
    DATE_FORMAT = '%Y-%m-%d %H:%M'
    INTERVAL = Interval.daily

    _DEFAULT_DATE_FORMAT = '%Y-%m-%d'
    _DEFAULT_TIME_INTERVAL = Interval.hourly
    _STDOUT_FORMAT = 'cloud_health.{env}.{report_name}.{category} {cost} {date}\n'

    @staticmethod
    def _get_cloud_health_return(
        report_id,
        category=None,
        date_format=_DEFAULT_DATE_FORMAT,
        time_interval=_DEFAULT_TIME_INTERVAL,
    ):
        """
        Creates a fake data to mock Cloud Health API
        """
        result = {
            'Total': {'key1': 'value1', 'key2': None},
        }

        dt = datetime.today()
        dt_diff = {
            # GOTCHA: This is technically not always a month incremental. However, the main purpose
            #         of this mocking is to test the datetime format string. Thus, leaving this as is
            #         for the maintainability and readability.
            Interval.monthly: {'days': 30},
            Interval.weekly: {'days': 7},
            Interval.daily: {'days': 1},
            Interval.hourly: {'hours': 1},
        }

        for index in range(0, 11):
            result[dt.strftime(date_format)] = {
                'key1': 'value1',
                'key2': None,
            }
            dt = dt - timedelta(**dt_diff[time_interval])

        if category is None:
            return result
        else:
            return {
                category: result.get(category, {})
            }

    @patch('sys.argv', ['prog', API_KEY, REPORT_ID_ARG, '--report-name', REPORT_NAME_ARG])
    def setUp(self):
        self.app = Application()
        self.app.logger = MagicMock()
        self.app.cloud_health.get_custom_report = MagicMock(side_effect=CloudHealthAPITest._get_cloud_health_return)

    def test_init(self):
        """
        Cloud Health to Graphite: All private fields are properly created in __init__
        """
        # Verify report_name field is created
        self.assertEqual(self.REPORT_NAME, self.app.report_name)

        # Verify the version info is specified
        self.assertIn(Application.NAME, self.app._VERSIONS)
        self.assertEqual(__version__, self.app._VERSIONS[Application.NAME])

    def test_add_cli_arguments(self):
        """
        Cloud Health to Graphite: All arguments from present in the args
        """
        self.assertIn('api_key', self.app.args)
        self.assertIn('report_id', self.app.args)
        self.assertIn('report_name', self.app.args)
        self.assertIn('set_date', self.app.args)
        self.assertIn('date_format', self.app.args)

        self.assertEqual(self.API_KEY, self.app.args.api_key)
        self.assertEqual(self.REPORT_ID, self.app.args.report_id)
        self.assertEqual(self.REPORT_NAME_ARG, self.app.args.report_name)
        self.assertIsNone(self.app.args.set_date)
        self.assertEqual(self._DEFAULT_DATE_FORMAT, self.app.args.date_format)

    def test_run_error(self):
        """
        Cloud Health to Graphite: The application correctly errors out when report data cannot be retrieved
        from Cloud Health
        """
        error = ValueError('Error message')

        self.app.cloud_health.get_custom_report = MagicMock(side_effect=error)
        with self.assertRaises(SystemExit) as cm:
            self.app.run()
        self.assertEqual(cm.exception.code, 1)
        self.app.logger.error.assert_called_once_with(str(error))

    @patch('sys.stdout', new_callable=StringIO)
    def test_run_without_set_date(self, mock_stdout):
        """
        Cloud Health to Graphite: Cloud Health's report data is correctly displayed to stdout to be sent to graphite.
        """
        self.app.run()

        self.app.cloud_health.get_custom_report.assert_called_once_with(
            report_id=self.REPORT_ID,
            category=None,
            time_interval=Interval.hourly,
        )
        self.app.logger.debug.assert_called_once_with(
            pprint.pformat(CloudHealthAPITest._get_cloud_health_return(self.REPORT_ID))
        )

        prints = ''

        for date, values in iteritems(CloudHealthAPITest._get_cloud_health_return(self.REPORT_ID)):
            if date is 'Total':
                continue

            date = int(calendar.timegm(datetime.strptime(date, '%Y-%m-%d').utctimetuple()))

            for category, cost in iteritems(values):
                if cost is not None:
                    prints += self._STDOUT_FORMAT.format(
                        env=self.app.args.stats_environment,
                        report_name=self.REPORT_NAME,
                        category=category,
                        cost=cost,
                        date=date,
                    )

        self.assertEqual(prints, mock_stdout.getvalue())

    @patch('sys.argv', ['prog', API_KEY, REPORT_ID_ARG, '--report-name', REPORT_NAME_ARG, '--set-date', SET_DATE])
    @patch('sys.stdout', new_callable=StringIO)
    def test_run_with_set_date(self, mock_stdout):
        """
        Cloud Health to Graphite: Only the designated date's data is displayed to stdout when --set-date is used
        """
        app = Application()
        app.cloud_health.get_custom_report = MagicMock(side_effect=CloudHealthAPITest._get_cloud_health_return)

        app.run()

        prints = ''

        for date, values in iteritems(CloudHealthAPITest._get_cloud_health_return(self.REPORT_ID, self.SET_DATE)):
            date = int(calendar.timegm(datetime.strptime(self.SET_DATE, '%Y-%m-%d').utctimetuple()))

            for category, cost in iteritems(values):
                if cost is not None:
                    prints += self._STDOUT_FORMAT.format(
                        env=self.app.args.stats_environment,
                        report_name=self.REPORT_NAME,
                        category=category,
                        cost=cost,
                        date=date,
                    )

        self.assertEqual(prints, mock_stdout.getvalue())

    @patch('sys.argv', ['prog', API_KEY, REPORT_ID_ARG, '--report-name', REPORT_NAME_ARG, '--date-format', DATE_FORMAT])
    @patch('sys.stdout', new_callable=StringIO)
    def test_run_with_date_format(self, mock_stdout):
        """
        Cloud Health to Graphite: The date in the data is correctly parsed with the passed --date-format
        """
        app = Application()
        # Create a lambda function that calls _get_cloud_health_return() with CloudHealthAPITest.DATE_FORMAT
        # This is because side_effect can only take a function pointer
        app.cloud_health.get_custom_report = MagicMock(
            side_effect=lambda report_id, category, time_interval: CloudHealthAPITest._get_cloud_health_return(
                report_id=report_id, date_format=CloudHealthAPITest.DATE_FORMAT, time_interval=time_interval
            )
        )

        app.run()

        prints = ''

        api_data = CloudHealthAPITest._get_cloud_health_return(
            self.REPORT_ID, date_format=self.DATE_FORMAT,
        )
        for date, values in iteritems(api_data):
            if date is 'Total':
                continue

            date = int(calendar.timegm(datetime.strptime(date, self.DATE_FORMAT).utctimetuple()))

            for category, cost in iteritems(values):
                if cost is not None:
                    prints += self._STDOUT_FORMAT.format(
                        env=self.app.args.stats_environment,
                        report_name=self.REPORT_NAME,
                        category=category,
                        cost=cost,
                        date=date,
                    )

        self.assertEqual(prints, mock_stdout.getvalue())

    @patch('sys.argv', ['prog', API_KEY, REPORT_ID_ARG, '--report-name', REPORT_NAME_ARG, '--interval', INTERVAL.name])
    @patch('sys.stdout', new_callable=StringIO)
    def test_run_with_interval(self, mock_stdout):
        """
        Cloud Health to Graphite: The date in the data is correctly parsed with the passed --interval
        """
        app = Application()
        app.cloud_health.get_custom_report = MagicMock(side_effect=CloudHealthAPITest._get_cloud_health_return)

        app.run()

        prints = ''

        api_data = CloudHealthAPITest._get_cloud_health_return(
            self.REPORT_ID, time_interval=self.INTERVAL,
        )
        for date, values in iteritems(api_data):
            # API always returns a set of dates and a total for the keys of the dictionary. We don't need the total
            # value. Ignore it here.
            if date is 'Total':
                continue

            posix_date = int(calendar.timegm(datetime.strptime(date, self._DEFAULT_DATE_FORMAT).utctimetuple()))

            for category, cost in iteritems(values):
                if cost is not None:
                    prints += self._STDOUT_FORMAT.format(
                        env=self.app.args.stats_environment,
                        report_name=self.REPORT_NAME,
                        category=category,
                        cost=cost,
                        date=posix_date,
                    )

        self.assertEqual(prints, mock_stdout.getvalue())

    def test_main(self):
        """
        Cloud Health to Graphite: Application is instantiated and run() is called in main()
        """
        app = MagicMock()
        app_class = MagicMock(return_value=app)

        with patch('bin.cloud_health_to_graphite.Application', app_class):
            main()

        app_class.assert_called_once_with()
        app.run.assert_called_once_with()
