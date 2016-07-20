# -*- coding: utf-8 -*-
#
# © 2016 Krux Digital, Inc.
#
"""
CLI tools for accessing Krux Cloud Health Tech
"""

#
# Standard libraries
#

from __future__ import absolute_import
import pprint

#
# Third party libraries
#


#
# Internal libraries
#

import krux.cli
from krux.logging import get_logger
from krux.cli import get_group
from krux_cloud_health.cloud_health import CloudHealth, Interval, NAME, add_cloud_health_cli_arguments, get_cloud_health


class Application(krux.cli.Application):
    def __init__(self, name=NAME):

        # Call to the superclass to bootstrap.
        super(Application, self).__init__(name=name)

        self.logger = get_logger(name)

        try:
            self.cloud_health = get_cloud_health(args=self.args, logger=self.logger, stats=self.stats)
        except ValueError as e:
            self.logger.error(e.message)
            self.exit(1)

        self.interval = Interval[self.args.interval]

        if self.args.set_date is not None:
            self.date_input = self.args.set_date
        else:
            self.date_input = None

    def add_cli_arguments(self, parser):
        """
        Add CloudHealth-related command-line arguments to the given parser.

        :argument parser: parser instance to which the arguments will be added
        """

        add_cloud_health_cli_arguments(parser)

        group = get_group(parser, self.name)

        group.add_argument(
            '--interval',
            type=str,
            choices=[i.name for i in Interval],
            default=Interval.daily.name,
            help="Set time interval of data (default: %(default)s)",
        )

        group.add_argument(
            '--set-date',
            type=str,
            default=None,
            help="Retrieve cost history data for specific date, depending on interval. (ex: 'YYYY-MM-DD' for daily)",
        )

    def run(self):
        try:
            cost_history = self.cloud_health.cost_history(self.interval, self.date_input)
            self.logger.debug(pprint.pformat(cost_history))
        except (ValueError, IndexError) as e:
            self.logger.error(e.message)
            self.exit(1)

        # If no date_input, cost_data is most recent data available for given time interval in cost_history
        if self.date_input is None:
            cost_data = cost_history.pop()
            self.date_input = cost_data.keys()[0]
        # If date_input provided, search through cost_history until dictionary corresponding to date_input is found
        else:
            cost_data = [cost_history[i] for i in range(len(cost_history)) if cost_history[i].keys()[0] == self.date_input][0]

        for item, data in cost_data[self.date_input].iteritems():
            self.stats.incr(item, data)


def main():
    app = Application()
    with app.context():
        app.run()

# Run the application stand alone
if __name__ == '__main__':
    main()
