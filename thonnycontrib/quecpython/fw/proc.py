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
import json
import subprocess
from pathlib import Path
from queue import Queue, Empty
from threading import Thread, Lock
from logging import getLogger
from logging import getLogger


logger = getLogger(__name__)


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


class DownloadLogFile(object):
    log_file_path = Path(__file__).parent / 'download.log'
    lock = Lock()

    def __init__(self):
        self.fb = None

    def __enter__(self):
        self.lock.acquire()
        self.fb = open(self.log_file_path, 'w', encoding='utf-8')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.fb.close()
        self.lock.release()

    def write(self, data):
        if self.fb is None:
            raise Exception('DownloadLogFile not open.')
        self.fb.write(data)

    def read(self):
        if self.fb is None:
            raise Exception('DownloadLogFile not open.')
        self.fb.read()


class BaseExecutor(object):

    def __init__(self, cmd, cwd, **extra):
        self.cmd = cmd
        self.cwd = cwd
        self.extra = extra

    def progress_rate(self):
        proc = Process(self.cmd, self.cwd)
        proc.run()
        with DownloadLogFile() as f:
            for line in proc.read_lines(timeout=60):
                f.write(line)
                logger.info(line)
                rv = self.parse(line)
                if rv:
                    yield rv

    def parser(self, line):
        raise NotImplementedError


class _AsrExecutor(BaseExecutor):

    def __init__(self, cmd, cwd, **extra):
        self.json_string = ""
        self.flag = False
        self.progress = 0
        self.log_string = ""
        super().__init__(cmd, cwd, **extra)

    def parse(self, line):
        if line.startswith('{'):
            self.json_string += line
            self.flag = True
            return

        if self.flag:
            if not line.startswith('}'):
                self.json_string += line
                return
            else:
                self.json_string += line
                rv = json.loads(self.json_string)
                self.json_string = ""
                self.flag = False
                if rv and rv['status'] != 'OFFLINE':
                    self.progress = rv['progress']
                    return self.log_string, self.progress
        else:
            self.log_string = line
            return self.log_string, self.progress

class _200AExecutor(BaseExecutor):

    def __init__(self, cmd, cwd, **extra):
        self.progress = 0
        super().__init__(cmd, cwd, **extra)

    def parse(self, line):
        if "Successfully to prepare temp folder file for wtptp download" in line:
            return "RESET"
        elif "Download percentage" in line:
            self.progress = int(line.strip().split(' ')[-1])
            return line, self.progress
        elif "flash percentage" in line:
            self.progress = int(line.strip().split(' ')[-1])
            return line, self.progress
        else:
            return line, self.progress


class _BG95Executor(BaseExecutor):

    def __init__(self, cmd, cwd, **extra):
        self.progress = 0
        super().__init__(cmd, cwd, **extra)

    def parse(self, line):

        if '[1]DL-' in line:
            self.progress += 2
            return line, self.progress
        elif '[1]FW upgrade success.' in line:
            return line, 100
        elif '[1]FW upgrade fail' in line:
            raise Exception('BG95 FW Download Failed.')
        else:
            return line, self.progress


class _NBExecutor(BaseExecutor):

    def __init__(self, cmd, cwd, **extra):
        self.progress = 0
        super().__init__(cmd, cwd, **extra)

    def parse(self, line):
        if '[1]FW upgrade fail.' in line:
            raise Exception('NB FW Download Failed.')

        if "[1]Upgrade:" in line:
            self.progress = int(line.replace("[1]Upgrade:", '').strip()[:-1])
            return line, self.progress
        else:
            return line, self.progress


class _UnisocExecutor(BaseExecutor):

    def __init__(self, cmd, cwd, **extra):
        self.progress = 0
        super().__init__(cmd, cwd, **extra)

    def parse(self, line):

        if "Downloading..." in line:
            self.progress += 1
            return line[:50], self.progress * 10

        if "DownLoad Passed" in line:
            return line[:50], 100

        if "[ERROR] DownLoad Failed" in line:
            raise Exception('Unisoc FW Download Failed.')


class _360WExecutor(BaseExecutor):

    def parse(self, line):
        try:
            data = json.loads(line)
        except Exception as e:
            return line, 1

        if data['Status'] == 'Programming':
            return line, data['Progress']
        else:
            if data['Status'] == 'Ready':
                return line, 5
            elif data['Status'] == 'Finished' and data['Message'] == 'Success':
                return line, 100
            else:
                raise Exception('360W Download Failed!')


class _EIGENExecutor(BaseExecutor):

    def __init__(self, cmd, cwd, **extra):
        self.progress = 0
        super().__init__(cmd, cwd, **extra)

    def progress_rate(self):
        with DownloadLogFile() as f:
            # 检测连接
            logger.info("---------- detect link ----------")
            cmd1 = self.cmd + ["probe"]
            logger.info('cmd1: {}'.format(cmd1))
            p = Process(cmd1)
            p.run()
            for line in p.read_lines(timeout=60):
                f.write(line)
                logger.info(line)
                self.parse(line)
                yield line, self.progress

            # pkg2img
            logger.info("---------- pkg2img ----------")
            cmd2 = self.cmd[:3] + ["pkg2img"]
            logger.info('cmd2: {}'.format(cmd2))
            p = Process(cmd2)
            p.run()
            for line in p.read_lines(timeout=60):
                f.write(line)
                logger.info(line)
                self.parse(line)
                yield line, self.progress

            # 烧录固件
            logger.info("---------- Burn firmware ----------")
            cmd3 = self.cmd[:1] + ["--skipconnect", "1"] + self.cmd[1:] + ["burn"]
            logger.info('cmd3: {}'.format(cmd3))
            p = Process(cmd3)
            p.run()
            for line in p.read_lines(60):
                f.write(line)
                logger.info(line)
                self.parse(line)
                yield line, self.progress

            # 下载 ap_application.bin文件
            logger.info("---------- Download ap_application.bin flasherase ----------")
            flexfile2 = self.extra['flexfile2']
            cmd4 = self.cmd[:1] + ["--skipconnect", "1"] + self.cmd[1:] + ["flasherase"] + [flexfile2]
            logger.info('cmd4: {}'.format(cmd4))
            p = Process(cmd4)
            p.run()
            for line in p.read_lines(60):
                f.write(line)
                logger.info(line)
                self.parse(line)
                yield line, self.progress
            logger.info("---------- Download ap_application.bin burnone ----------")
            cmd5 = self.cmd[:1] + ["--skipconnect", "1"] + self.cmd[1:] + ["burnone", "flexfile2"]
            logger.info('cmd5: {}'.format(cmd5))
            p = Process(cmd5)
            p.run()
            for line in p.read_lines(60):
                f.write(line)
                logger.info(line)
                self.parse(line)
                yield line, self.progress

            # 下载 ap_updater.bin文件
            logger.info("---------- Download ap_updater.bin flasherase ----------")
            flexfile3 = self.extra['flexfile3']
            cmd6 = self.cmd[:1] + ["--skipconnect", "1"] + self.cmd[1:] + ["flasherase"] + [flexfile3]
            logger.info('cmd6: {}'.format(cmd6))
            p = Process(cmd6)
            p.run()
            for line in p.read_lines(60):
                f.write(line)
                logger.info(line)
                self.parse(line)
                yield line, self.progress
            logger.info("---------- Download ap_updater.bin burnone ----------")
            cmd7 = self.cmd[:1] + ["--skipconnect", "1"] + self.cmd[1:] + ["burnone", "flexfile3"]
            logger.info('cmd7: {}'.format(cmd7))
            p = Process(cmd7)
            p.run()
            for line in p.read_lines(60):
                f.write(line)
                logger.info(line)
                self.parse(line)
                yield line, self.progress

            # 下载 customer_fs.bin文件
            logger.info("---------- Download customer_fs.bin flasherase ----------")
            flexfile4 = self.extra['flexfile4']
            cmd8 = self.cmd[:1] + ["--skipconnect", "1"] + self.cmd[1:] + ["flasherase"] + [flexfile4]
            logger.info('cmd8: {}'.format(cmd8))
            p = Process(cmd8)
            p.run()
            for line in p.read_lines(60):
                f.write(line)
                logger.info(line)
                self.parse(line)
                yield line, self.progress
            logger.info("---------- Download customer_fs.bin burnone ----------")
            cmd9 = self.cmd[:1] + ["--skipconnect", "1"] + self.cmd[1:] + ["burnone", "flexfile4"]
            logger.info('cmd9: {}'.format(cmd9))
            p = Process(cmd9)
            p.run()
            for line in p.read_lines(60):
                f.write(line)
                logger.info(line)
                self.parse(line)
                yield line, self.progress

            if self.extra['File_Count'] == 4:
                # 下载 customer_backup_fs.bin 文件
                logger.info("---------- Download customer_backup_fs.bin flasherase ----------")
                flexfile5 = self.extra['flexfile5']
                cmd10 = self.cmd[:1] + ["--skipconnect", "1"] + self.cmd[1:] + ["flasherase"] + [flexfile5]
                logger.info('cmd10: {}'.format(cmd10))
                p = Process(cmd10)
                p.run()
                for line in p.read_lines(60):
                    f.write(line)
                    logger.info(line)
                    self.parse(line)
                    yield line, self.progress
                logger.info("---------- Download customer_backup_fs.bin burnone ----------")
                cmd11 = self.cmd[:1] + ["--skipconnect", "1"] + self.cmd[1:] + ["burnone", "flexfile5"]
                logger.info('cmd11: {}'.format(cmd11))
                p = Process(cmd11)
                p.run()
                for line in p.read_lines(60):
                    f.write(line)
                    logger.info(line)
                    self.parse(line)
                    yield line, self.progress

            # 重启模块
            logger.info("---------- sysreset ----------")
            cmd12 = self.cmd[:1] + ["--skipconnect", "1"] + self.cmd[1:] + ["sysreset"]
            logger.info('cmd12: {}'.format(cmd12))
            p = Process(cmd12)
            p.run()
            for line in p.read_lines(timeout=60):
                f.write(line)
                logger.info(line)
                self.parse(line)
                yield line, self.progress
            yield 100

    def parse(self, line):
        if "RtsConditionAssign" in line:
            self.progress += 1
        elif "files transferred" in line:
            self.progress += 1
        else:
            pass


def run_cmd(cmd, platform, cwd, **extra):
    logger.info('enter run_cmd method, args: {}'.format((cmd, platform, cwd,)))

    if platform.upper() in ["ASR", "ASR1601", "ASR1606"]:
        executor = _AsrExecutor(cmd, cwd)
    elif platform.upper() in ["UNISOC", "UNISOC8910", "UNISOC8850"]:
        executor = _UnisocExecutor(cmd, cwd)
    elif platform.upper() == "RDA8908A":
        executor = _NBExecutor(cmd, cwd)
    elif platform.upper() == "ASR1803S":
        executor = _200AExecutor(cmd, cwd)
    elif platform.upper() == "MDM9X05":
        executor = _BG95Executor(cmd, cwd)
    elif platform.upper() == "EIGEN":
        executor = _EIGENExecutor(cmd, cwd, **extra)
    elif platform.upper() == "FCM360W":
        executor = _360WExecutor(cmd, cwd)
    else:
        pass

    return executor.progress_rate()
