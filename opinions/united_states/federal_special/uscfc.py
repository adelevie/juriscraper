# -*- coding: utf-8 -*-

"""Scraper for the United States Court of Federal Claims
CourtID: uscfc
Court Short Name: Fed. Cl.

Notes:
    Scraper adapted for new website as of February 20, 2014.
"""

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import titlecase
import re
import time
from datetime import date
from lxml import html


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.uscfc.uscourts.gov/aggregator/sources/8'
        self.back_scrape_iterable = range(1, 4)
        self.court_id = self.__module__

    def _get_case_dates(self):
        dates = []
        for t in self.html.xpath('//span[@class="feed-item-date"]/text()'):
            # Text has contents like "Filed 05/09/2014"
            t = t.strip().split(' ')[1]
            dates.append(date.fromtimestamp(time.mktime(time.strptime(
                t.strip(), '%m/%d/%Y'))))
        return dates

    def _get_case_names(self):
        case_names = []
        for t in self.html.xpath('//h3[@class="feed-item-title"]//text()'):
            t = ' '.join(t.split())  # Normalize whitespace
            if t.strip():
                # If there is something other than whitespace...
                t = t.encode('utf8').split(' • ')[1].strip()
                t = titlecase(t.lower())
                case_names.append(t)
        return case_names

    def _get_download_urls(self):
        path = '//h3[@class="feed-item-title"]/a/@href'
        return list(self.html.xpath(path))

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        docket_numbers = []
        for t in self.html.xpath('//h3[@class="feed-item-title"]//text()'):
            if t.strip():
                # If there is something other than whitespace...
                t = t.encode('utf8').split(' • ')[0].strip()
                docket_numbers.append(t)
        return docket_numbers

    def _get_summaries(self):
        summaries = []
        path = '//div[@class="feed-item-body"]'
        for e in self.html.xpath(path):
            s = html.tostring(e, method='text', encoding='unicode')
            s = s.split('Keywords:')[0]
            summaries.append(s)

        return summaries

    def _get_judges(self):
        path = '//div[@class="feed-item-body"]'
        judges = []
        splitters = [
            'Signed by Chief Judge',
            'Signed by Judge',
            'Signed by Chief Special Master',  # Vaccine courts have odd names for judges
            'Signed by Special Master',
        ]
        for e in self.html.xpath(path):
            t = html.tostring(e, method='text', encoding='unicode')
            t = t.split('Keywords:')[0]
            for splitter in splitters:
                judge_parts = t.rsplit(splitter)
                if len(judge_parts) == 1:
                    # No splits found...
                    judge = ''
                    continue
                else:
                    judge = judge_parts[1]
                    break

            # Often the text looks like: 'Judge Susan G. Braden. (jt1) Copy to parties.' In that case we only
            # want the name, not the rest.
            length_of_match = 2
            m = re.search('[a-z]{%s}\.' % length_of_match, judge)  # Two lower case letters followed by a period
            if m:
                judge = judge[:m.start() + length_of_match]
            else:
                judge = ''
            judge.strip('.')
            judges.append(judge)
        return judges

    def _download_backwards(self, page):
        self.url = 'http://www.uscfc.uscourts.gov/aggregator/sources/8?page=%s' % page
        self.html = self._download()

