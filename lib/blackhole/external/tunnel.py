import subprocess
import threading
import re
import os
import tempfile
from string import Template

from ..utils import Event


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
        threading.Thread.__init__(self, daemon=True)
        cmd = 'ngrok -config="{}" -log="stdout" start {}'.format(fil.name, ' '.join(services))
        self.cmd = cmd

        self.onMsg = Event()

    def run(self):
        self.proc = subprocess.Popen(self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                bufsize=0)

        for line in self.proc.stdout:
            print('>>>>>', line)
            m = re.search(rb'Tunnel established at https?://(.*)\n', line)
            if m:
                host = m.group(1)
                self.onMsg('connect', host.decode('utf-8'))

    def stop(self):
        self.proc.terminate()


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