import os
import subprocess
import shutil
import re
import datetime
import requests
from pyon.public import log
from ion.agent.data_agent import DataAgentPlugin
from ion.util.ntp_time import NTP4Time


#           1(year)   2(month)  3(day)    4(hour)   5(min)    6(Hs)        7(Tp)        8(Dp)    9(Ta)       10(Temp)
#                                                             meters       seconds      degrees  seconds     celcius 
pattern = '^(\d{4})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s*$'

"""
YEAR MO DY HR MN   Hs   Tp   Dp    Depth   Ta    Pres   Wspd Wdir Temp   Temp   Temp   Temp
      UTC           m   sec  deg     m     sec    mB     m/s  deg Air(C) Sfc(C) Mid(C) Bot(C)
2016 05 28 22 25  2.67  9.09 322           6.35                           11.0
2016 05 28 22 55  3.01  9.09 324           6.54                           11.0
2016 05 28 23 25  2.90  8.33 320           6.39                           11.0
...
"""

"""
Station Summary (metadata) 
Current status: operational
Most recent location: 37 56.899' (N), 123 28.050' (W)  [change lat/lon format]
Instrument description: Datawell directional buoy
Most recent water depth:  1804.46 (ft)  [change units]
Measured parameters: wave energy,wave direction,sea temperature
Approximate location: 21.5 nm W of Point Reyes
Nautical chart: 18645
Funding: CDBW/USACE
Operator: CDIP
"""


class CDIP_DataAgentPlugin(DataAgentPlugin):
    def on_start_streaming(self, streaming_args):
        log.info('CDIP_DataAgentPlugin..on_start_streaming: args %s' % str(streaming_args))
        self.streaming_args = streaming_args
        self.last_sample = None

    def on_stop_streaming(self):
        log.info('CDIP_DataAgentPlugin.on_stop_streaming')

    def acquire_samples(self):
        log.debug('CDIP_DataAgentPlugin.acquire_samples')

        # Read server, extract last sample.
        data = requests.get(self.streaming_args.url)
        for m in re.finditer(pattern, data.text, flags=re.MULTILINE):
            pass
        if not m:
            log.warning('CDIP_DataAgentPlugin.acquire_samples: No data found.')
            return None

        year = int(m.group(1))
        month = int(m.group(2))
        day = int(m.group(3))
        hour = int(m.group(4))
        minute = int(m.group(5))
        Hs = float(m.group(6))
        Tp = float(m.group(7))
        Dp = int(m.group(8))
        Ta = float(m.group(9))
        Temp = float(m.group(10))

        # Create sample.
        # [ntp64_ts, Hs, Tp, Dp, Ta, Temp]
        # ['\xdb\x07\x00,\x00\x00\x00\x00', 2.66, 9.09, 328, 6.67, 12.2]
        dt = datetime.datetime(year, month, day, hour, minute)
        ts = NTP4Time(dt).to_ntp64()
        sample = [ts, Hs, Tp, Dp, Ta, Temp]

        # Compare to last reading.
        if self.last_sample == sample:
            log.debug('CDIP_DataAgentPlugin.acquire_samples: No new data.')
            return None

        # Update, pack and return.
        log.debug('CDIP_DataAgentPlugin.acquire_samples: Got new data.')
        log.debug('CDIP data: %s' % str(sample))
        self.last_sample = sample
        sample_desc = dict(cols=["time", "Hs", "Tp", "Dp", "Ta", "Temp"],
            data=[sample])
        return sample_desc
        


