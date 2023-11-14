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

import shlex

from thonnycontrib.quecpython.backend.connection import QuecPythonConnection


class SshProcessConnection(QuecPythonConnection):
    def __init__(self, client, cwd, cmd):
        super().__init__()
        import threading

        self._client = client

        cmd_line_str = (
            "echo $$ ;"
            + ((" cd %s  2> /dev/null ;" % shlex.quote(cwd) if cwd else ""))
            + (" exec " + " ".join(map(shlex.quote, cmd)))
        )
        self._stdin, self._stdout, _ = self._client.exec_command(
            cmd_line_str, bufsize=0, timeout=None, get_pty=True
        )

        # stderr gets directed to stdout because of pty
        self._pid = self._stdout.readline().strip()

        self._reading_thread = threading.Thread(target=self._listen_output, daemon=True)
        self._reading_thread.start()

    def write(self, data: bytes) -> int:
        if isinstance(data, str):
            data = data.encode(self.encoding)
        self._stdin.write(data)
        self._stdin.flush()
        return len(data)

    def _listen_output(self):
        "NB! works in background thread"
        try:
            while not self._reader_stopped:
                data = self._stdout.read(1)
                if len(data) > 0:
                    self._make_output_available(data)
                else:
                    self._error = "EOF"
                    break

        except Exception as e:
            self._error = str(e)

    def close(self):
        self._client.exec_command("kill -s SIGKILL %s" % self._pid)
        self._reading_thread.join()
        self._client = None
        self._reading_thread = None
