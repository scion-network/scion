""" Dataset agent plugin for replayed ORB data """

import math
import os
import random
import time
import yaml

from pyon.public import log, get_ion_ts_millis
from ion.util.ntp_time import NTP4Time
from ion.agent.data_agent import DataAgentPlugin


class ORBReplay_DataAgentPlugin(DataAgentPlugin):

    def on_connect(self, connect_args=None):
        self.replay_filename = self.agent_config["replay_file"]
        self.replay_scenario = self.agent_config["replay_scenario"]
        with open(self.replay_filename, "r") as f:
            file_cont = f.read()
        replay_data = yaml.load(file_cont)
        scenario_data = replay_data["scenarios"][self.replay_scenario]
        self.samples = scenario_data["data"]
        self.sample_index = 0

    def acquire_samples(self, max_samples=0):
        if len(self.samples) <= self.sample_index:
            log.warn("Out of samples at index %s", self.sample_index)
            self.sample_index += 1
            return None

        data_row = self.samples[self.sample_index]
        self.sample_index += 1

        sample = [NTP4Time(data_row["time"]).to_ntp64(),
                  tuple(data_row["sample_vector"])
                  ]

        sample_desc = dict(cols=["time", "sample_vector"],
                           coltypes=dict(sample_vector="10i2"),
                           data=[sample])

        print sample_desc

        return sample_desc
