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

from collections import namedtuple
from logging import getLogger
from pubsub import pub
from .fw import FwDownloadHandler, DownloadLogFile


logger = getLogger(__name__)


class BaseApi(object):
    # communicate topic
    UPDATE_TOPIC = 'update'  # must be different

    # status code
    OK = 0x00
    EXIT = 0x02

    # transmission payload
    Payload = namedtuple('Payload', ['code', 'data', 'exec'])

    @classmethod
    def bind(cls, handler):
        pub.subscribe(handler, cls.UPDATE_TOPIC)

    def emit(self, data):
        pub.sendMessage(
            self.UPDATE_TOPIC,
            payload=self.Payload(code=self.OK, data=data, exec=None)
        )

    def exit(self, exec_=None):
        pub.sendMessage(
            self.UPDATE_TOPIC,
            payload=self.Payload(code=self.EXIT, data=None, exec=exec_)
        )

    def run(self):
        raise NotImplementedError('you must implement this method in sub class.')

    def __call__(self):
        try:
            self.run()
        except Exception as e:
            self.exit(exec_=e)
        else:
            self.exit()


class DownLoadFWApi(BaseApi):
    UPDATE_TOPIC = 'UPDATE_PROGRESS'

    def __init__(self, firmware_file_path, platform, com_info):
        self.firmware_file_path = firmware_file_path
        self.platform = platform
        self.com_info = com_info

    def run(self):
        logger.info('enter download_firmware_api function. args: {}'.format((self.firmware_file_path,)))
        fw_download_handler = FwDownloadHandler(self.firmware_file_path, self.platform, self.com_info)
        for data in fw_download_handler.download():
            self.emit(data)

    def exit(self, exec_=None):
        if exec_ is not None:
            error_message = '{}\nsee log: {}'.format(str(exec_), DownloadLogFile.log_file_path)
            exec_ = Exception(error_message)
        super().exit(exec_=exec_)
