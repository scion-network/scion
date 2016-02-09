
import os
import psutil

from pyon.public import log, get_ion_ts_millis
from pyon.util.ion_time import IonTime
from ion.agent.data_agent import DataAgentPlugin


class VMMON_DataAgentPlugin(DataAgentPlugin):

    def acquire_samples(self, max_samples=0):

        sample = [IonTime().to_ntp64(), psutil.cpu_percent()]

        sample_desc = dict(cols=["time", "cpu_percent"],
                           data=[sample])

        return sample_desc
