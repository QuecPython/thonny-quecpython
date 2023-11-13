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

import signal
import sys

from thonny.plugins.quecpython.backend.connection import QuecPythonConnection


class SubprocessConnection(QuecPythonConnection):
    def __init__(self, executable, args=[]):
        import threading

        try:
            import ptyprocess
        except ImportError:
            print(
                "ERROR: This back-end requires a Python package named 'ptyprocess'.\n"
                + "Install it via system package manager or 'Tools => Manage plug-ins'."
            )
            sys.exit(1)

        super().__init__()
        cmd = [executable] + args
        self._proc = ptyprocess.PtyProcessUnicode.spawn(cmd, echo=False)
        # print(dir(self._proc))
        # self._poll = select.poll()
        # self._poll.register(self._proc, select.POLLIN)

        # self._stdout = self._proc.stdout

        self._reading_thread = threading.Thread(target=self._listen_output, daemon=True)

        self._reading_thread.start()

    def write(self, data: bytes) -> int:
        if isinstance(data, (bytes, bytearray)):
            data = data.decode(self.encoding)
        self._proc.write(data)
        self._proc.flush()
        return len(data)

    def _listen_output(self):
        "NB! works in background thread"
        try:
            while True:
                chars = self._proc.read(1)
                if len(chars) > 0:
                    as_bytes = chars.encode(self.encoding)
                    self._make_output_available(as_bytes)
                else:
                    self._error = "EOF"
                    break

        except Exception as e:
            self._error = str(e)

    def close(self):
        if self._proc is not None:
            self._proc.kill(signal.SIGKILL)
            # self._reading_thread.join() # 0.2 secs!
            self._proc = None
            self._reading_thread = None
