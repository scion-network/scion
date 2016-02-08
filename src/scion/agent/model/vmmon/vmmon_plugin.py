
import os
import psutil

from pyon.public import log, get_ion_ts_millis
from ion.agent.data_agent import DataAgentPlugin


class VMMON_DataAgentPlugin(DataAgentPlugin):

    def acquire_samples(self, max_samples=0):

        sample = [get_ion_ts_millis(), psutil.cpu_percent()]

        sample_desc = dict(cols=["time", "cpu_percent"],
                           data=[sample])

        return sample_desc
