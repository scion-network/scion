import os
import subprocess

from pyon.public import log
from ion.agent.data_agent import DataAgentPlugin


class Orb_DataAgentPlugin(DataAgentPlugin):


    def on_start_streaming(self,streaming_args):
      log.info('Orb_DataAgentPlugin..on_start_streaming: args %s' % str(streaming_args))
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
      log.info('Orb reap args: ' + str(cmd_args))
      self.proc = subprocess.Popen(cmd_args, executable='/opt/antelope/5.5/bin/python')
      log.info('Orb reap process started, %i' % self.proc.pid)
      self.data_dir = '/tmp/scion-data/%s/' % (streaming_args['select'].replace('/','-'))

    def on_stop_streaming(self):
      log.info('Orb_DataAgentPlugin.on_stop_streaming')
      self.proc.terminate()
      log.info('Waiting for orb reap to terminate...')
      retcode = self.proc.wait()
      log.info('Orb reap process terminated, %i' % self.proc.pid)
      self.proc = None

    def acquire_samples(self):
      log.info('Orb_DataAgentPlugin.acquire_samples') 
      #if os.path.exists(self.data_dir):
      #  files = os.listdir(self.data_dir)
      #  print 'Samples present: '
      #  for f in files:
      #    fpath = self.data_dir + f 
      #    print fpath

    """
    Sample return format.
    {'data': [['\xda\x99z\x1d\x13[@\x00', 3.2]], 'cols': ['time', 'cpu_percent']}
    """


    """
    def acquire_samples(self, max_samples=0):

        sample = [NTP4Time.utcnow().to_ntp64(), psutil.cpu_percent()]

        sample_desc = dict(cols=["time", "cpu_percent"],
                           data=[sample])

        #log.info("vmmon sample returning: %s" % str(sample_desc))
        return sample_desc
    """



