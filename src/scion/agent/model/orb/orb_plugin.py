import os
import subprocess
import shutil
import json
from pyon.public import log
from ion.agent.data_agent import DataAgentPlugin
from ion.util.ntp_time import NTP4Time


class Orb_DataAgentPlugin(DataAgentPlugin):
    def on_start_streaming(self, streaming_args):
        log.info('Orb_DataAgentPlugin..on_start_streaming: args %s' % str(streaming_args))
        self.streaming_args = streaming_args
        cmd_args = ['orb_reap', 'src/scion/agent/model/orb/orbstart.py', streaming_args['orb_name'],
                    streaming_args['select']]
        if 'reject' in streaming_args:
            cmd_args.append('--reject').append(streaming_args['reject'])
        if 'after' in streaming_args:
            cmd_args.append('--after').append(streaming_args['after'])
        if 'timeout' in streaming_args:
            cmd_args.append('--timeout').append(streaming_args['timeout'])
        if 'qsize' in streaming_args:
            cmd_args.append('--qsize').append(streaming_args['qsize'])
        log.info('Orb reap args: ' + str(cmd_args))
        self.data_dir = '/tmp/scion-data/%s/' % (streaming_args['select'].replace('/', '-'))
        if os.path.exists(self.data_dir):
            shutil.rmtree(self.data_dir)
        self.proc = subprocess.Popen(cmd_args, executable='/opt/antelope/5.5/bin/python')
        log.info('Orb reap process started, %i' % self.proc.pid)

    def on_stop_streaming(self):
        log.info('Orb_DataAgentPlugin.on_stop_streaming')
        self.proc.terminate()
        log.info('Waiting for orb reap to terminate...')
        #retcode = self.proc.wait()
        #log.info('Orb reap process terminated, %i' % self.proc.pid)
        #self.proc = None

    def acquire_samples(self):
        log.debug('Orb_DataAgentPlugin.acquire_samples')
        if os.path.exists(self.data_dir):
            files = os.listdir(self.data_dir)
            cols = []
            rows = []
            for f in files:
                fpath = self.data_dir + f
                with open(fpath) as fh:
                    try:
                        pkt = json.load(fh)
                        if not cols:
                            cols = [str(c['chan']) for c in pkt['channels']]              
                        row = self._extract_row(pkt, cols)
                        dims = [len(c) for c in row[:3]]
                        if all(d==400 for d in dims):
                            rows.append(row)
                        else:
                            log.warning('Inconsistent dimensions %s, %s' % (str(dims), fpath))
                        fh.close()
                        os.remove(fpath)
                        log.info('sample: ' + fpath)
                    except Exception as ex:
                        log.warn(ex)
                        log.warn('Incomplete packet %s' % fpath)
                        
            if cols and rows:
                coltypes = {}
                for c in cols:
                    coltypes[c] = '400u2'
                cols.append('time')
                samples = dict(cols=cols, data=rows, coltypes=coltypes)
                return samples

    def _extract_row(self, pkt, cols):
        row = []
        for c in cols:
            for ch in pkt['channels']:
                if ch['chan'] == c:
                    row.append(tuple(ch['data']))
                    break
        orbtime = pkt['channels'][0]['time']
        row.append(NTP4Time(orbtime).to_ntp64())
        return row
