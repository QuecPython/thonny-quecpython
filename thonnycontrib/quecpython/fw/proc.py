# Copyright (c) Quectel Wireless Solution, Co., Ltd.All Rights Reserved.
#  
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#  
#     http://www.apache.org/licenses/LICENSE-2.0
#  
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import subprocess
from queue import Queue, Empty
from threading import Thread


class ProcRunTimeout(Exception):
    pass


class Process(object):

    def __init__(self, cmd, cwd=None):
        self.cmd = cmd
        self.cwd = cwd
        self.proc = None
        self.output_thread = None
        self.queue = Queue()

    def run(self):
        self.proc = subprocess.Popen(
            self.cmd,
            cwd=self.cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        self.output_thread = Thread(target=self._readerthread)
        self.output_thread.daemon = True
        self.output_thread.start()

    def _readerthread(self):
        for line in self.proc.stdout:
            self.queue.put(line)
        self.queue.put(None)

    def read_lines(self, timeout=60):
        while True:
            try:
                line = self.queue.get(timeout=timeout)
            except Empty:
                self.proc.kill()
                raise ProcRunTimeout('process running timeout. cmd: {}'.format(self.cmd))

            if line is None:
                break

            yield line

    def stop(self):
        self.queue.put(None)
        self.proc.kill()


if __name__ == '__main__':
    cmd1 = ['adownload.exe', '-p', '19', '-a', '-q', '-r', '-s', '115200', 'QPY_OCPU_V0007_EC600N_CNLA_FW.bin']
    proc = Process(cmd1)
    proc.run()
    for line in proc.read_lines():
        print(line)
