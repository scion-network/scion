""" Dataset agent plugin for a simulator sensor """

import math
import os
import random
import time

from pyon.public import log, get_ion_ts_millis
from ion.util.ntp_time import NTP4Time
from ion.agent.data_agent import DataAgentPlugin


class SIM01_DataAgentPlugin(DataAgentPlugin):

    def acquire_samples(self, max_samples=0):
        ts = time.time()
        sample = [NTP4Time.utcnow().to_ntp64(),
                  20 * math.sin(10 * ts) + 5,
                  10 * math.sin(15 * ts) + 10,
                  random.random()*100]

        sample_desc = dict(cols=["time", "wave1", "wave2", "random1"],
                           data=[sample])

        return sample_desc
