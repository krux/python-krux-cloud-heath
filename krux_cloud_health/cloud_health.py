# -*- coding: utf-8 -*-
#
# © 2016 Krux Digital, Inc.
#
"""
Class to retrieve data from Cloud Health Tech API
"""

#
# Standard libraries
#

from __future__ import absolute_import
import sys
import urlparse
import pprint

#
# Third party libraries
#

import requests

#
# Internal libraries
#

from krux.cli import Application
from krux.logging import get_logger
from krux.stats import get_stats
from krux.cli import get_parser, get_group

API_ENDPOINT = "https://apps.cloudhealthtech.com/"


class CloudHealth(object):
    """
    """
    def __init__(self, api_key, stats):
        self.api_key = api_key
        self.stats = stats

    def costHistory(self):

        report = "olap_reports/cost/history"

        uri_args = {'api_key': self.api_key}
        uri = urlparse.urljoin(API_ENDPOINT, report)
        r = requests.get(uri, params=uri_args)
        call = r.json()

        curr_month = "2016-06"
        months = call["dimensions"][0]["time"]
        month_index = [index for index, month in enumerate(months) if month["name"] == curr_month][0]
        month_list = [str(month["name"]) for month in months]

        items_list = call["dimensions"][1]["AWS-Service-Category"]
        #items_list = [item for item in items]
        #items_dict = {str(item["label"]): items_list[item.get("parent") + 1]["label"] for item in items_list if item.get("parent") >= 0}

        # total_data = []

        # for month_index in range(len(month_list)):

        curr_month_info = {}
        curr_month_info[curr_month] = {}

        data_nested = call["data"][month_index]
        data_list = [data for sublist in data_nested for data in sublist]
        data_list = [float("%.2f" % data) if isinstance(data, float) else data for data in data_list]

        for i in range(len(items_list)):
            item = items_list[i]
            #print pprint.pformat(item, indent=2, width=20)
            if item.get("parent") >= 0 and item["label"] != "Total":
                curr_month_info[curr_month][item["label"]] = data_list[i]
                self.stats.incr(item["label"], data_list[i])

        return curr_month_info

            #month_info = {month_list[month_index]: dict(zip(items_list, data_list))}

            # if month_list[month_index] != "total":
            #     print month_list[month_index] + ".S3 - API: ", month_info[month_list[month_index]]["S3 - API"]
            #     self.stats.incr(month_list[month_index] + ".S3 - API", month_info[month_list[month_index]]["S3 - API"])

            # total_data.append(month_info)

        # return total_data

        # data_nested = call["data"][month_index]
        # data_list = [data for sublist in data_nested for data in sublist]

        # data_list = [float("%.2f" % data) if isinstance(data, float) else data for data in data_list]

        # curr_month_info = {curr_month: dict(zip(items_list, data_list))}

        # for item, data in curr_month_info[curr_month].iteritems():
        #     print item, ": ", data
        #     self.stats.incr(item, data)

    def costCurrent(self):

        report = "olap_reports/cost/current"

        uri_args = {'api_key': self.api_key}
        uri = urlparse.urljoin(API_ENDPOINT, report)
        r = requests.get(uri, params=uri_args)
        call = r.json()

        aws_accounts = call["dimensions"][0]["AWS-Account"]
        aws_accounts_list = [str(aws_account["label"]) for aws_account in aws_accounts]

        items_dict = call["dimensions"][1]["AWS-Service-Category"]
        items_list = [str(item["label"]) for item in items_dict]

        total_data = []

        for index in range(len(aws_accounts_list)):
            data_nested = call["data"][index]
            data_list = [data for sublist in data_nested for data in sublist]
            data_list = [float("%.2f" % data) if isinstance(data, float) else data for data in data_list]
            account_info = {aws_accounts_list[index]: dict(zip(items_list, data_list))}

            total_data.append(account_info)

        return total_data

    def costSavings(self):
        report = "olap_reports/cost/savings/saved"

        uri_args = {'api_key': self.api_key}
        uri = urlparse.urljoin(API_ENDPOINT, report)
        r = requests.get(uri, params=uri_args)
        call = r.json()

        print pprint.pformat(call, indent=2, width=20)

    def costAmortized(self):
        report = "olap_reports/cost/current/amortized"

        uri_args = {'api_key': self.api_key}
        uri = urlparse.urljoin(API_ENDPOINT, report)
        r = requests.get(uri, params=uri_args)
        call = r.json()

        print pprint.pformat(call, indent=2, width=20)

    # Not working
    def budgetVsActual(self):
        report = "reports/aws/budget-vs-actual"

    def ec2Instance(self):
        report = "olap_reports/cost/current/instance"

        uri_args = {'api_key': self.api_key}
        uri = urlparse.urljoin(API_ENDPOINT, report)
        r = requests.get(uri, params=uri_args)
        call = r.json()

        print pprint.pformat(call, indent=2, width=20)

    def ec2Volume(self):
        report = "olap_reports/cost/volume"

        uri_args = {'api_key': self.api_key}
        uri = urlparse.urljoin(API_ENDPOINT, report)
        r = requests.get(uri, params=uri_args)
        call = r.json()

        print pprint.pformat(call, indent=2, width=20)

    def ec2RiAmortization(self):
        report = "olap_reports/cost/ri/amortization"

        uri_args = {'api_key': self.api_key}
        uri = urlparse.urljoin(API_ENDPOINT, report)
        r = requests.get(uri, params=uri_args)
        call = r.json()

        print pprint.pformat(call, indent=2, width=20)

    def costS3(self):
        report = "olap_reports/cost/s3"

        uri_args = {'api_key': self.api_key}
        uri = urlparse.urljoin(API_ENDPOINT, report)
        r = requests.get(uri, params=uri_args)
        call = r.json()

        print pprint.pformat(call, indent=2, width=20)

    def costRDS(self):
        report = "olap_reports/cost/rds"

        uri_args = {'api_key': self.api_key}
        uri = urlparse.urljoin(API_ENDPOINT, report)
        r = requests.get(uri, params=uri_args)
        call = r.json()

        print pprint.pformat(call, indent=2, width=20)

    def costDynamoDB(self):
        report = "olap_reports/cost/dynamo_db"

        uri_args = {'api_key': self.api_key}
        uri = urlparse.urljoin(API_ENDPOINT, report)
        r = requests.get(uri, params=uri_args)
        call = r.json()

        print pprint.pformat(call, indent=2, width=20)
