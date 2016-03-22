#!/usr/bin/python

import os
import sys
import pickle
import time
import subprocess
import threading
import shutil

class DataAgentPrototype():
  def __init__(self, plugin):
    self.sampling_gl = None
    self.sampling_gl_done = None
    self.plugin = plugin
    self.streaming_args = None

  def on_start_streaming(self, streaming_args):
    print 'DataAgent.on_start_streaming'

    self.plugin.on_start_streaming(streaming_args)
    self.streaming_args = streaming_args
    self.sampling_gl_done = threading.Event()
    self.sampling_gl = threading.Thread(target = self._sample_data_loop)
    self.sampling_gl.start()

  def on_stop_streaming(self):
    print 'DataAgent.on_stop_streaming'
    self.plugin.on_stop_streaming()
    self.sampling_gl_done.set()
    self.sampling_gl.join()

  def _sample_data_loop(self):
    print 'Sampling greenlet started.'
    while not self.sampling_gl_done.is_set():
      time.sleep(self.streaming_args['sample_interval'])
      self.plugin.acquire_samples()
    print 'sampling greenlet done, exiting.'

class OrbPluginPrototype():

  def __init__(self):
    self.proc = None
    self.acquire_thread = None
    self.streaming_args = None

  def on_start_streaming(self,streaming_args):
    print 'OrbPluginPrototype.on_start_streaming'
    self.streaming_args = streaming_args
    cmd_args = ['orb_reap', './orbstart.py', streaming_args['orb_name'], streaming_args['select']]
    if 'reject' in streaming_args:
      cmd_args.append('--reject').append(streaming_args['reject'])
    if 'after' in streaming_args:
      cmd_args.append('--after').append(streaming_args['after'])
    if 'timeout' in streaming_args:
      cmd_args.append('--timeout').append(streaming_args['timeout'])
    if 'qsize' in streaming_args:
      cmd_args.append('--qsize').append(streaming_args['qsize'])
    print str(cmd_args)
    self.proc = subprocess.Popen(cmd_args, executable='/opt/antelope/5.5/bin/python')
    print 'Orb reap process started, ', self.proc.pid
    self.data_dir = '/tmp/scion-data/%s/' % (streaming_args['select'].replace('/','-'))


  def on_stop_streaming(self):
    print 'OrbPluginPrototype.on_stop_streaming'
    self.proc.terminate()
    print 'Waiting for orb reap to terminate...'
    retcode = self.proc.wait()
    print 'Orb reap process terminated, ', self.proc.pid
    self.proc = None
  def acquire_samples(self):
    print 'Plugin acquiring samples...'
    if os.path.exists(self.data_dir):
      files = os.listdir(self.data_dir)
      print 'Samples present: '
      for f in files:
        fpath = self.data_dir + f
        print fpath


if __name__ == '__main__':

  # This test code is a placeholder for the 
  # SciON DataAgent control flow so we can
  # port it over easily.

  # Coming in from the agent config.
  streaming_args = {
    'orb_name' : 'taexport.ucsd.edu:usarrayTA',
    #'select' : 'TA_109C/MGENC/M40',
    'select' : 'TA_121A/MGENC/M40',
    '--timeout' : 5,
    'sample_interval' : 5
  }

  # Agent config specifies which class to construct.
  plugin = OrbPluginPrototype()

  # DataAgent
  agent = DataAgentPrototype(plugin)

  # Start streaming.
  agent.on_start_streaming(streaming_args)

  # Time passes.
  time.sleep(30)

  # DataAgent on_stop_streaming is activated.
  agent.on_stop_streaming()


