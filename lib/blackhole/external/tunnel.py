import subprocess
import threading
import re
import os
import sys
import tempfile
from string import Template
import atexit

from ..utils import Event


import logging
logger = logging.getLogger(__name__)

config_tmpl = Template('''
server_addr: ${server}
tunnels:
''')

item_tmpl = Template('''
  ${service}:
    hostname: "${host}"
    proto:
      http: ${port}
''')

class Tunnel(threading.Thread):
    def __init__(self, port, hosts=[], server='ngrok.com:4443'):

        threading.Thread.__init__(self, daemon=True)

        # build yaml
        with tempfile.NamedTemporaryFile(delete=False) as fil:
            buf = []
            services = []
            buf.append(config_tmpl.substitute(server=server))
            for i, host in enumerate(hosts):
                service = 'service'+str(i)
                services.append(service)
                buf.append(item_tmpl.substitute(host=host, port=port, service=service))
            s = '\n'.join(buf).encode('utf-8')
            fil.write(s)

        logger.info('Ngrok config up at %s' % fil.name)

        if sys.platform == 'win32':
            self.shell = False
            cmd = './data/bin/ngrok.exe -config="{}" -log="stdout" start {}'.format(fil.name, ' '.join(services))
        else:
            self.shell = True
            cmd = 'ngrok -config="{}" -log="stdout" start {}'.format(fil.name, ' '.join(services))

        self.cmd = cmd
        self.proc = None

        self.onMsg = Event()
        atexit.register(self.stop)

    def run(self):
        '''
        Server failed to allocate tunnel: The tunnel http://amd.mttweb.html5.qq.com is already registered.

        '''
        logger.info('Running command: %s' % self.cmd)

        # hide console window on windows
        if sys.platform == 'win32':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        else:
            startupinfo = None

        self.proc = subprocess.Popen(self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=self.shell,
                startupinfo=startupinfo,
                bufsize=0)

        for line in self.proc.stdout:
            line = line.decode('utf-8')
            logger.debug('ngrok: ' + line)
            m = re.search(r'Tunnel established at https?://(.*)\n', line)
            
            if m:
                host = m.group(1)
                self.onMsg('connect', host)

    def stop(self):
        if self.proc and not self.proc.poll():
            logger.info('Kill running proc: %s' % self.cmd)
            self.proc.terminate()

        atexit.unregister(self.stop)


'''
TODO:
    external programs should go into this package
'''
if __name__ == '__main__':
    def log(host):
        print(host, 'connected')

    p = Tunnel('8000')
    p.onMsg += log
    p.start()

    import time
    time.sleep(3)
    p.stop()
