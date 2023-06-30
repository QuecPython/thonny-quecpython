import os
import time
import json
import zipfile
import serial
import configparser
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


def get_com_port(fw_filepath):
    cmd = 'at+qdownload=1'
    fw_config = json.load(open(str(Path(__file__).with_name('fw_config.json')), 'r'))
    if fw_filepath.suffix == ".pac":
        at_port = get_com_port_number(
            fw_config["firmware"]["vid_pid_work"],
            fw_config["firmware"]["Quectel_USB_DIAG_Port"]
        )
    elif fw_filepath.suffix == ".lod":
        return "NB_DOWNLOAD"
    elif fw_filepath.suffix == ".blf":
        return "blf_DOWNLOAD"
    elif fw_filepath.suffix == ".mbn":
        return "mbn_DOWNLOAD"
    else:
        at_port = get_com_port_number(
            fw_config["firmware"]["vid_pid_work"],
            fw_config["firmware"]["Quectel_USB_AT_Port"]
        )

    if at_port is not None:
        try:
            s = QuecPort(at_port)
            s.OpenConn()
            s.SendCmd(cmd)
            s.CloseConn()
            wait_to_port(fw_config["firmware"]["vid_pid_dwload"])
        except Exception as e:
            return

    download_port = get_com_port_number(fw_config["firmware"]["vid_pid_dwload"])
    return download_port


class myconf(configparser.ConfigParser):
    def __init__(self, defaults=None):
        configparser.ConfigParser.__init__(self, defaults=defaults)

    def optionxform(self, optionstr):
        return optionstr