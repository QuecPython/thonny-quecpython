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

import os
import time
import json
import zipfile
import serial
import configparser
import sys
import shutil
import codecs
from pathlib import Path
from serial.tools import list_ports


def unzipFile(src, dst):
    with zipfile.ZipFile(src, 'r') as zip_ref:
        zip_ref.extractall(dst)


def checkZipFile(filePath):
    for filename in os.listdir(filePath):
        if filename == 'customer_fs.bin':
            return True
    return False


class QuecPort(object):
    def __init__(self, port):
        self._port = port
        self._baudrate = 115200
        self._conn = None

    def OpenConn(self):
        try:
            self._conn = serial.Serial(self._port, self._baudrate)
            return self._conn
        except:
            print("Failed to open port %s " % str(self._port))

    def CloseConn(self):
        self._conn.close()

    def SendCmd(self, cmd):
        self._conn.write((cmd + '\r\n').encode())

    def RecvCmd(self):
        return self._conn.read(20)

    # PETAR
    def RecvCmdUntil(self):
        time.sleep(0.1)
        try:
            num = self._conn.inWaiting()
            try:
                # res = self._conn.read_until(b"end=1\r\n")
                print(num)
                res = self._conn.read(num)
                return res
            except:
                return b""
        except:
            print("Failed to open port %s " % str(self._port))


def get_com_port_number(vid_pid, port=""):
    for p in list(list_ports.comports()):
        for i in vid_pid.values():
            if port == "":
                if i in p.hwid:
                    return p.device
            else:
                if i and port in p.hwid:
                    return p.device


def wait_to_port(vid_pid, port=""):
    for i in range(60):
        time.sleep(0.5)
        if get_com_port_number(vid_pid, port) is not None:
            break


class myconf(configparser.ConfigParser):
    def __init__(self, defaults=None):
        configparser.ConfigParser.__init__(self, defaults=defaults)

    def optionxform(self, optionstr):
        return optionstr


def extractFileName(path):
    return path.split("\\")[-1]


def readJSON(jsonName):
    with codecs.open(jsonName, 'r', 'utf-8') as f:
        data = json.load(f)
    return data


def isZip(path):
    return zipfile.is_zipfile(path)


def ifExist(Path):
    # Determine if a file/directory exists
    return os.path.exists(Path)


def makeCleanDir(Dir):
    if os.path.exists(Dir) is False:
        try:
            os.makedirs(Dir)
            return True
        except:
            info = sys.exc_info()
            print("make clean Dir error0.")
            print(info[0], info[1])
            return False
    else:
        try:
            shutil.rmtree(Dir)
            while True:
                time.sleep(0.1)
                if ifExist(Dir) is False:
                    break
            os.makedirs(Dir)
            return True
        except:
            info = sys.exc_info()
            print("make clean Dir error1.")
            print(info[0], info[1])
            return False


def get_com_port(fw_file_path, platform):
    cmd = 'at+qdownload=1'
    fw_config = json.load(open(str(Path(__file__).with_name('fw_config.json')), 'r'))
    if platform.upper() in ["UNISOC", "UNISOC8910", "UNISOC8850"]:
        atPort = get_com_port_number(
            fw_config["firmware"]["vid_pid_work"], fw_config["firmware"]["Quectel_USB_DIAG_Port"]
        )
    elif platform.upper() == "RDA8908A":
        return "NB_DOWNLOAD"
    elif platform.upper() == "ASR1803S":
        return "ASR1803S_DOWNLOAD"
    elif platform.upper() == "MDM9X05":
        return "mbn_DOWNLOAD"
    elif platform.upper() == "EIGEN":
        atPort = get_com_port_number(
            fw_config["firmware"]["vid_pid_work"]
        )
        return atPort
    elif platform.upper() in ["ASR", "ASR1601", "ASR1606"]:
        atPort = get_com_port(fw_config["firmware"]["vid_pid_work"], fw_config["firmware"]["Quectel_USB_AT_Port"])
    else:
        return "WIFI_DOWNLOAD"

    print('atPort: {}'.format(atPort))
    if atPort:
        try:
            s = QuecPort(atPort)
            s.OpenConn()
            s.SendCmd(cmd)
            s.CloseConn()
            wait_to_port(fw_config["firmware"]["vid_pid_dwload"])
        except Exception as e:
            return
        downloadPort = get_com_port_number(fw_config["firmware"]["vid_pid_dwload"])
        return downloadPort


def get_fw_and_platform(fw_filepath):
        if isZip(fw_filepath):
            newFWFolder = str(Path(__file__).parent / 'newFW')
            makeCleanDir(newFWFolder)
            unzipFile(fw_filepath, newFWFolder)
            if ifExist(newFWFolder + "\\platform_config.json"):
                try:
                    data = readJSON(newFWFolder + "\\platform_config.json")
                    platform = data["platform"].strip()
                    if platform.upper() in ["ASR", "ASR1601", "ASR1606"]:
                        newFW = [i for i in os.listdir(newFWFolder) if i != "platform_config.json"][0]
                    elif platform.lower() in ["unisoc", "unisoc8910", "unisoc8850"]:
                        newFW = [i for i in os.listdir(newFWFolder) if i != "platform_config.json"][0]
                    elif platform.upper() == "RDA8908A":
                        newFW = [i for i in os.listdir(newFWFolder) if i != "platform_config.json"][0]
                    elif platform.upper() == "MDM9X05":
                        newFW = [i for i in os.listdir(newFWFolder) if i != "platform_config.json"][
                                    0] + "\\firehose\\partition.mbn"
                    elif platform.upper() == "ASR1803S":
                        newFW = [i for i in os.listdir(newFWFolder) if i != "platform_config.json"][
                                    0] + "\\Falcon_EVB_QSPI_Nor_LWG_Only_Nontrusted_PM802_LPDDR2.blf"
                    elif platform.upper() == "FCM360W":
                        newFW = [i for i in os.listdir(newFWFolder) if i != "platform_config.json"][0]
                    elif platform.upper() == "FC41D":
                        newFW = [i for i in os.listdir(newFWFolder) if i != "platform_config.json"][0]
                    elif platform.upper() == "EIGEN":
                        newFW = [i for i in os.listdir(newFWFolder) if i != "platform_config.json"][
                                    0] + "\\at_command.binpkg"
                    else:
                        return None
                    newFW = os.path.join(newFWFolder, newFW)
                    if not ifExist(newFW):
                        return None
                except Exception as e:
                    logger.error(e)
                    return None
            else:
                if ifExist(newFWFolder + "\\system.img"):
                    logger.info("asr fw")
                    platform = "ASR1601"
                    newFW = fw_fileName
                else:
                    return None
        else:
            newFW = fw_filepath
            if fw_filepath[-3:].lower() == "pac":
                platform = "unisoc"
            elif fw_filepath[-3:].lower() == "lod":
                platform = "RDA8908A"
            elif fw_filepath[-3:].lower() == "blf":
                platform = "ASR1803S"
            elif fw_filepath[-3:].lower() == "mbn":
                platform = "MDM9X05"
            elif fw_filepath[-6:].lower() == "binpkg":
                platform = "EIGEN"
            elif fw_filepath[-3:].lower() == "bin":
                if fw_filepath.upper().find("FCM360W") != -1:
                    platform = "FCM360W"
                elif fw_filepath.upper().find("FC41D") != -1:
                    platform = "FC41D"
                else:
                    return None
            else:
                return None
        return newFW, platform
