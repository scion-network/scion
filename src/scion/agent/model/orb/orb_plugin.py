import os
import subprocess
import shutil
import json
from pyon.public import log, get_sys_name, Container
from ion.agent.data_agent import DataAgentPlugin
from ion.util.ntp_time import NTP4Time

from pyon.public import CFG


class Orb_DataAgentPlugin(DataAgentPlugin):
    def on_start_streaming(self, streaming_args):
        log.info('Orb_DataAgentPlugin..on_start_streaming: args %s' % str(streaming_args))
        self.streaming_args = streaming_args
        script_path = os.path.dirname(__file__) + "/orbstart.py"   # On production, run from inside an egg
        data_dir = Container.instance.file_system.get("TEMP/orb_data")
        cmd_args = ['orb_reap', script_path, streaming_args['orb_name'],
                    streaming_args['select'], "--datadir", data_dir]
        if 'reject' in streaming_args:
            cmd_args.append('--reject')
            cmd_args.append(streaming_args['reject'])
        if 'after' in streaming_args:
            cmd_args.append('--after')
            cmd_args.append(streaming_args['after'])
        if 'timeout' in streaming_args:
            cmd_args.append('--timeout')
            cmd_args.append(streaming_args['timeout'])
        if 'qsize' in streaming_args:
            cmd_args.append('--qsize')
            cmd_args.append(streaming_args['qsize'])
        log.info('Orb reap args: ' + str(cmd_args))
        self.data_dir = data_dir + '/%s/' % (streaming_args['select'].replace('/', '-'))
        if os.path.exists(self.data_dir):
            shutil.rmtree(self.data_dir)
        antelope_path = CFG.get_safe("scion.antelope.path", "/opt/antelope/5.6")
        cmd_args = [str(arg) for arg in cmd_args]
        self.proc = subprocess.Popen(cmd_args, executable=antelope_path+'/bin/python')
        log.info('Orb reap process started, %i' % self.proc.pid)

    def on_stop_streaming(self):
        log.info('Orb_DataAgentPlugin.on_stop_streaming')
        self.proc.terminate()
        log.info('Waiting for orb reap to terminate...')
        #retcode = self.proc.wait()
        #log.info('Orb reap process terminated, %i' % self.proc.pid)
        #self.proc = None

    def acquire_samples(self, max_samples=0):
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
                    coltypes[c] = '400i4'
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
