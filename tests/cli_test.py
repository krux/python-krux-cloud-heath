# -*- coding: utf-8 -*-
#
# © 2016 Krux Digital, Inc.
#

#
# Standard libraries
#

from __future__ import absolute_import
import unittest
import sys

#
# Third party libraries
#

from mock import MagicMock, patch

#
# Internal libraries
#

from krux_cloud_health.cli import Application, main
from krux_cloud_health.cloud_health import Interval, NAME
from krux.stats import DummyStatsClient

class CLItest(unittest.TestCase):

    NAME = 'cloud-health-tech'
    API_KEY = '12345'

    @patch('krux_cloud_health.cli.get_logger')
    @patch('krux_cloud_health.cli.get_cloud_health')
    @patch('sys.argv', ['api-key', '12345'])
    def setUp(self, mock_get_cloud_health, mock_get_logger):
        self.app = Application()
        self.mock_get_cloud_health = mock_get_cloud_health
        self.mock_get_logger = mock_get_logger

    def test_init(self):
        """
        CLI Test: CLI constructor creates all the required private properties
        """
        self.assertEqual(self.NAME, self.app.name)
        self.assertEqual(self.NAME, self.app.parser.description)
        # The dummy stats client has no awareness of the name. Just check the class.
        self.assertIsInstance(self.app.stats, DummyStatsClient)

        self.mock_get_cloud_health.assert_called_once_with(
            args=self.app.args,
            logger=self.app.logger,
            stats=self.app.stats
        )

    def test_add_cli_arguments(self):
        """
        CLI Test: All arguments from Cloud Health Tech are present in the args
        """
        self.assertIn('api_key', self.app.args)
        self.assertEqual(self.API_KEY, self.app.args.api_key)

    def test_run(self):
        """
        CLI Test: Cloud Health's cost_history and cost_current methods are correctly called in self.app.run()
        """
        self.mock_get_cloud_health.cost_history.return_value = {
            'dimensions': [
                {
                    'time': [
                        {'name': '2016-05'},
                        {'name': '2016-06'}
                    ]
                },
                {
                    'AWS-Service-Category': [
                        {'label': 'Label-1'},
                        {'label': 'Label-2'}
                    ]
                }
            ],
            'data': [
                [
                    ['a'],
                    ['b']
                ],
                [
                    ['c'],
                    ['d']
                ]
            ]
        }

        self.mock_get_cloud_health.cost_current.return_value = {
            'dimensions': [
                {
                    'AWS-Account': [
                        {'name': 'Krux Ops'},
                        {'name': 'Krux IT'}
                    ]
                },
                {
                    'AWS-Service-Category': [
                        {'label': 'Label-1'},
                        {'label': 'Label-2'}
                    ]
                }
            ],
            'data': [
                [
                    ['a'],
                    ['b']
                ],
                [
                    ['c'],
                    ['d']
                ]
            ]
        }
        self.app.run()
        self.mock_get_cloud_health.cost_current.called_once_with(Interval.weekly)
        self.mock_get_cloud_health.cost_current.called_once_with("Krux IT")

    def test_main(self):
        """
        CLI Test: Application is instantiated and run() is called in main()
        """
        app = MagicMock()
        app_class = MagicMock(return_value=app)

        with patch('krux_cloud_health.cli.Application', app_class):
            main()

        app_class.assert_called_once_with()
        app.run.assert_called_once_with()

