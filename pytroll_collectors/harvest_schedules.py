#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2019 Trygve Aspenes

# Author(s):

#   Trygve Aspenes <trygveas@met.no>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Harvest schedules. Download schedules from EUM and parse to limit gatherer"""

import re
from datetime import datetime, timedelta
try:
    from urllib.request import urlopen
except ImportError:
    from urllib import urlopen

try:
    import urllib.error.HTTPError as httperror
except ImportError:
    httperror = IOError

import logging

LOG = logging.getLogger(__name__)

EUM_DOWNLOAD_URL = ''
EUM_BASE_URL = 'https://uns.eumetsat.int/downloads/ears/'
save_basename = '/tmp'
download_file = 'ears_{}_pass_prediction_'

eum_platform_name_translate = {'metopa': 'metop-a',
                               'metopb': 'metop-b',
                               'metopc': 'metop-c',
                               'noaa19': 'noaa 19',
                               'noaa20': 'noaa 20',
                               'npp': 'suomi npp',
                               'snpp': 'suomi npp',
                               'fy3d': 'fengyun 3d'}


sensor_translate = {'avhrr/3': 'avhrr'}
def harvest_schedules(params):
    LOG.debug("params: %s", params)
    planned_pass_start_time = min(params['planned_granule_times'])
    planned_pass_end_time = max(params['planned_granule_times'])
    planned_pass_mid_time = planned_pass_start_time + (planned_pass_end_time - planned_pass_start_time) / 2

    now = datetime.now()
    if 'sensor' in params:
        EUM_URL = EUM_BASE_URL + download_file.format(sensor_translate[params['sensor']]) + now.strftime('%y-%m-%d') + '.txt'
        LOG.debug("EUM_URL, %s", EUM_URL)
    else:
        LOG.error("sensor not given in params. Can not continue.")
        return (None, None)
    try:
        filedata = urlopen(EUM_URL)
    except httperror as httpe:
        LOG.error("Failed to download file: ", EUM_URL, httpe)
        return (None, None)

    passes = filedata.readlines()

    aos_los = re.compile('(\d{4})-(\d{2})-(\d{2})\s(\d{2}):(\d{2}),(\d{4})-(\d{2})-(\d{2})\s(\d{2}):(\d{2}),(.*)')

    min_time = None
    max_time = None
    for passe in passes:
        al = aos_los.match(passe.decode('utf-8'))
        if al:
            eum_aos = datetime(int(al.group(1)), int(al.group(2)), int(al.group(3)),
                               int(al.group(4)), int(al.group(5)))
            eum_los = datetime(int(al.group(6)), int(al.group(7)), int(al.group(8)),
                               int(al.group(9)), int(al.group(10)))
            eum_platform_name = al.group(11)
            platform_name = eum_platform_name_translate.get(eum_platform_name, eum_platform_name)
            if platform_name.upper() != params['platform_name'].upper():
                # print("SKipping platform: ", platform_name, params['platform_name'])
                continue
            planned_pass_mid_time = planned_pass_start_time + (planned_pass_end_time - planned_pass_start_time) / 2
            eum_pass_mid_time = eum_aos + (eum_los - eum_aos) / 2
            if abs(eum_pass_mid_time - planned_pass_mid_time) < timedelta(seconds=1000):
                LOG.debug("Found pass matching the current planned granule times: %s", str(passe))
                min_time = eum_aos
                max_time = eum_los
                break

    return (min_time, max_time)

if __name__ == "__main__":
    planned_granule_times = set([datetime(2019, 12, 13, 13, 19),
                                 datetime(2019, 12, 13, 13, 38),
                                 datetime(2019, 12, 13, 13, 27),
                                 datetime(2019, 12, 13, 13, 35),
                                 datetime(2019, 12, 13, 13, 16), datetime(2019, 12, 13, 13, 24), datetime(2019, 12, 13, 13, 13), datetime(2019, 12, 13, 13, 32), datetime(2019, 12, 13, 13, 21), datetime(2019, 12, 13, 13, 29), datetime(2019, 12, 13, 13, 18), datetime(2019, 12, 13, 13, 37), datetime(2019, 12, 13, 13, 26), datetime(2019, 12, 13, 13, 15), datetime(2019, 12, 13, 13, 34), datetime(2019, 12, 13, 13, 23), datetime(2019, 12, 13, 13, 31), datetime(2019, 12, 13, 13, 20), datetime(2019, 12, 13, 13, 28), datetime(2019, 12, 13, 13, 17), datetime(2019, 12, 13, 13, 36), datetime(2019, 12, 13, 13, 25), datetime(2019, 12, 13, 13, 14), datetime(2019, 12, 13, 13, 33), datetime(2019, 12, 13, 13, 22), datetime(2019, 12, 13, 13, 30)])
    params = {'planned_granule_times': planned_granule_times,
              'sensor': 'avhrr/3',
              'platform_name': 'Metop-A'}

    harvest_schedules(params)
