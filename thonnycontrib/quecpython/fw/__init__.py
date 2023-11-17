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

import glob
import json
import tempfile
from threading import Lock
from logging import getLogger
from ..locale import tr
from .utils import *
from .proc import run_cmd, DownloadLogFile


EXES_PATH = Path(__file__).with_name('exes')
logger = getLogger(__name__)


class FwDownloadHandler(object):

    def __init__(self, firmware_file_path, platform, com_info):
        self.fw_filepath = Path(firmware_file_path)
        self.com_info = com_info
        self.platform = platform

    def download(self):
        logger.info('enter FwDownloadHandler.download method.')
        if Path(self.fw_filepath).exists():
            logger.info('fw_filepath: \"{}\".'.format(self.fw_filepath))
            if self.platform.upper() in ["ASR", "ASR1601", "ASR1606"]:
                return self.asrFwDownload()
            elif self.platform.upper() in ["UNISOC", "UNISOC8910", "UNISOC8850"]:
                return self.rdaFwDownload()
            elif self.platform.upper() == "RDA8908A":
                return self.nbFwDownload()
            elif self.platform.upper() == "MDM9X05":
                return self.mbnFwDownload()
            elif self.platform.upper() == "ASR1803S":
                return self.blfFwDownload()
            elif self.platform.upper() == "FCM360W":
                return self.wifi360FwDownload()
            elif self.platform.upper() == "FC41D":
                return self.wifi41DFwDownload()
            elif self.platform.upper() == "EIGEN":
                return self.EigenFwDownload()
            else:
                raise Exception(tr('firmware not supported'))
        else:
            raise Exception(tr('fw filepath not exists'))

    def rdaFwDownload(self):
        logger.info('enter FwDownloadHandler.rdaFwDownload method.')
        tmp_path = tempfile.mkdtemp()
        config_pac = myconf()
        config_pac.read(str(EXES_PATH / "rda/ResearchDownload.ini"))
        if config_pac["Options"]["EraseAll"] != "0":
            config_pac["Options"]["EraseAll"] = "0"
            with open(EXES_PATH / "rda/ResearchDownload.ini", 'w+') as configfile:
                config_pac.write(configfile)
        logger.info("EraseAll: {}".format(config_pac["Options"]["EraseAll"]))

        tmp_fw_filepath = Path(tmp_path) / self.fw_filepath.name
        shutil.copyfile(self.fw_filepath, str(tmp_fw_filepath))
        logger.info('copy {} to {}.'.format(self.fw_filepath, tmp_fw_filepath))

        rdaFile_list = glob.glob(str(EXES_PATH / "rda/*"))
        for i in rdaFile_list:
            shutil.copy(i, str(Path(tmp_path)))
        logger.info('copy {} to {}'.format(str(EXES_PATH / "rda/*"), str(Path(tmp_path))))

        tmp_download_exe_path = Path(tmp_path) / "CmdDloader.exe"
        return self.fw_download(str(tmp_download_exe_path), str(tmp_fw_filepath))

    def nbFwDownload(self):
        logger.info('enter FwDownloadHandler.nbFwDownload method.')

        tmp_path = tempfile.mkdtemp()
        tmp_fw_filepath = Path(tmp_path) / self.fw_filepath.name
        shutil.copyfile(self.fw_filepath, str(tmp_fw_filepath))
        logger.info("tmp_fw_filepath: {}".format(tmp_fw_filepath))

        nb_dir = str(EXES_PATH / 'NB')
        tmp_nb_dir = str(Path(tmp_path) / 'NB')
        shutil.copytree(nb_dir, tmp_nb_dir)
        logger.info('copy tree {} to {}.'.format(nb_dir, tmp_nb_dir))

        tmp_download_exe_path = Path(tmp_nb_dir) / "QMulti_DL_CMD_V2.1.exe"
        return self.fw_download(str(tmp_download_exe_path), tmp_fw_filepath)

    def blfFwDownload(self):
        logger.info('enter FwDownloadHandler.blfFwDownload method.')
        tmp_path = tempfile.mkdtemp()

        download_exe_path = EXES_PATH / "blf_tools/SWDConsole.exe"
        tmp_download_exe_path = Path(tmp_path) / "SWDConsole.exe"
        shutil.copyfile(str(download_exe_path), str(tmp_download_exe_path))
        logger.info('copy {} to {}.'.format(download_exe_path, tmp_download_exe_path))

        tmp_fw_filedir = Path(tmp_path) / self.fw_filepath.parent.name
        shutil.copytree(self.fw_filepath.parent, str(tmp_fw_filedir))
        logger.info('copy {} to {}.'.format(self.fw_filepath.parent, tmp_fw_filedir))

        tmp_fw_filepath = tmp_fw_filedir / self.fw_filepath.name
        return self.fw_download(str(tmp_download_exe_path), str(tmp_fw_filepath))

    def mbnFwDownload(self):
        logger.info('enter FwDownloadHandler.mbnFwDownload method.')
        tmp_path = tempfile.mkdtemp()

        fdir1_name = self.fw_filepath.parent.name
        fdir2 = str(self.fw_filepath.parent.parent)
        fdir2_name = self.fw_filepath.parent.parent.name

        tmp_fdir2 = str(Path(tmp_path) / fdir2_name)
        shutil.copytree(fdir2, tmp_fdir2)
        logger.info('copy {} to {}'.format(fdir2, tmp_fdir2))

        nb_path = str(EXES_PATH / "NB")
        tmp_nb_path = str(Path(tmp_path) / "NB")
        shutil.copytree(nb_path, tmp_nb_path)
        logger.info('copy {} to {}'.format(nb_path, tmp_nb_path))

        return self.fw_download(str(Path(tmp_nb_path) / "QMulti_DL_CMD_V2.1.exe"),
                                str(Path(tmp_path) / fdir2_name / fdir1_name / self.fw_filepath.name))

    def asrFwDownload(self):
        logger.info('enter FwDownloadHandler.asrFwDownload method.')
        tmp_path = tempfile.mkdtemp()
        if self.fw_filepath.suffix == '.bin':
            temp_zip_filename = self.fw_filepath.with_suffix('.zip').name
        else:
            temp_zip_filename = self.fw_filepath.name
        temp_zip_file_path = str(Path(tmp_path) / temp_zip_filename)
        logger.info("temp_zip_file_path: {}".format(temp_zip_file_path))

        shutil.copyfile(self.fw_filepath, temp_zip_file_path)
        logger.info('copy {} to {}'.format(self.fw_filepath, temp_zip_file_path))

        exe_path = str(EXES_PATH / "aboot/adownload.exe")
        tmp_exe_path = str(Path(tmp_path) / "adownload.exe")
        shutil.copyfile(exe_path, tmp_exe_path)
        logger.info('copy {} to {}'.format(exe_path, tmp_exe_path))

        unzipFile(temp_zip_file_path, str(Path(tmp_path) / "images"))
        logger.info('unzip {} to dir {}.'.format(temp_zip_file_path,  str(Path(tmp_path) / "images")))

        if checkZipFile(str(Path(tmp_path) / "images")):
            return self.fw_download(
                str(tmp_exe_path),
                temp_zip_file_path
            )
        else:
            raise Exception('检查固件zip包是否未解压,请解压后重试')

    def wifi360FwDownload(self):
        tmp_path = tempfile.mkdtemp()
        logger.info("tmp_path: {}".format(tmp_path))
        tempZip_filename = self.fw_filepath.with_suffix('.zip').name
        logger.info("临时文件名: " + tempZip_filename)
        shutil.copyfile(
            str(self.fw_filepath),
            str(Path(tmp_path) / tempZip_filename)
        )
        shutil.copyfile(
            str(EXES_PATH / "FCM360W/EswinFlashTool.exe"),
            str(Path(tmp_path) / "EswinFlashTool.exe")
        )

        return self.fw_download(
            str(Path(tmp_path) / "EswinFlashTool.exe"),
            str(Path(tmp_path) / tempZip_filename)
        )

    def wifi41DFwDownload(self):
        pass

    def EigenFwDownload(self):
        tmp_path = tempfile.mkdtemp()
        logger.info("tmp_path: {}".format(tmp_path))
        fdir1 = str(self.fw_filepath.parent)
        shutil.copytree(fdir1, str(Path(tmp_path) / "fw"))
        shutil.copytree(str(EXES_PATH / "Eigen"), str(Path(tmp_path) / "Eigen"))

        extra = dict()
        try:
            config = configparser.ConfigParser(interpolation=None)
            logger.info('quec_download_config.ini path: {}'.format(str(Path(tmp_path) / "fw/quec_download_config.ini")))
            config.read(str(Path(tmp_path) / "fw/quec_download_config.ini"))
            File_Count = int(config.get('File', 'File_Count'))
            extra['File_Count'] = File_Count

            ap_application_addr = config.get('File_1', 'START_ADDR')
            ap_application_max = config.get('File_1', 'MAX_SIZE')
            flexfile2 = [ap_application_addr, ap_application_max]
            extra['flexfile2'] = flexfile2

            ap_updater_addr = config.get('File_2', 'START_ADDR')
            ap_updater_max = config.get('File_2', 'MAX_SIZE')
            flexfile3 = [ap_updater_addr, ap_updater_max]
            extra['flexfile3'] = flexfile3

            customer_fs_addr = config.get('File_3', 'START_ADDR')
            customer_fs_max = config.get('File_3', 'MAX_SIZE')
            flexfile4 = [customer_fs_addr, customer_fs_max]
            extra['flexfile4'] = flexfile4

            binpkg_config = configparser.ConfigParser(interpolation=None)
            binpkg_config_ini = str(Path(tmp_path) / "Eigen/config.ini")
            binpkg_config.read(binpkg_config_ini)

            binpkg_config.set('package_info', 'arg_pkg_path_val', str(Path(tmp_path) / "fw" / self.fw_filepath.name))

            binpkg_config.set('bootloader', 'blpath', str(Path(tmp_path) / "blloadskip = 0"))
            binpkg_config.set('system', 'syspath', str(Path(tmp_path) / "sysloadskip = 0"))
            binpkg_config.set('cp_system', 'cp_syspath', str(Path(tmp_path) / "cp_sysloadskip = 0"))

            binpkg_config.set('flexfile2', 'filepath', str(Path(tmp_path) / "fw/ap_application.bin"))
            binpkg_config.set('flexfile2', 'burnaddr', ap_application_addr)

            binpkg_config.set('flexfile3', 'filepath', str(Path(tmp_path) / "fw/ap_updater.bin"))
            binpkg_config.set('flexfile3', 'burnaddr', ap_updater_addr)

            binpkg_config.set('flexfile4', 'filepath', str(Path(tmp_path) / "fw/customer_fs.bin"))
            binpkg_config.set('flexfile4', 'burnaddr', customer_fs_addr)

            if File_Count == 4:
                customer_backup_fs_addr = config.get('File_4', 'START_ADDR')
                customer_backup_fs_max = config.get('File_4', 'MAX_SIZE')
                flexfile5 = [customer_backup_fs_addr, customer_backup_fs_max]
                extra['flexfile5'] = flexfile5

                binpkg_config.set('flexfile5', 'filepath',
                                       str(Path(tmp_path) / "fw/customer_backup_fs.bin"))
                binpkg_config.set('flexfile5', 'burnaddr', customer_backup_fs_addr)
            else:
                binpkg_config.remove_section('flexfile5')

        except Exception as e:
            raise Exception(tr("please check if the firmware is ok."))

        binpkg_config.set('config', 'line_0_com', self.com_info['port'])
        with open(binpkg_config_ini, "w+", encoding='utf-8') as f:
            binpkg_config.write(f)

        return self.fw_download(
            str(Path(tmp_path) / "Eigen/flashtoolcli1.exe"),
            str(Path(tmp_path) / "fw" / self.fw_filepath.name),
            binpkg_config_ini=binpkg_config_ini,
            **extra
        )

    def fw_download(self, download_exe_path, fw_filepath, **extra):
        logger.info('enter FwDownloadHandler.fw_download method.')

        if self.platform.upper() in ["ASR", "ASR1601", "ASR1606"]:
            cmd = [
                download_exe_path, '-p', self.com_info['port'][3:],
                '-a', '-q', '-r', '-s', self.com_info['baudrate'], fw_filepath
            ]
            logger.info('------------------adownload downloading factory package------------------')
        elif self.platform.upper() in ["UNISOC", "UNISOC8910", "UNISOC8850"]:
            cmd = [download_exe_path, '-pac', fw_filepath]
            logger.info('------------------unisoc downloading upgrade package------------------')
        elif self.platform.upper() == "RDA8908A":
            cmd = [download_exe_path, self.com_info['port'][3:], '115200', fw_filepath]
            logger.info('------------------NB downloading upgrade package------------------')
        elif self.platform.upper() == "ASR1803S":
            cmd = [download_exe_path, '-f', fw_filepath]
            logger.info('------------------200A download downloading factory package(blf)------------------')
        elif self.platform.upper() == "MDM9X05":
            cmd = [download_exe_path, self.com_info['port'][3:], '115200', fw_filepath]
            logger.info('------------------BG95 download downloading factory package(mbn)------------------')
        elif self.platform.upper() == "EIGEN":
            binpkg_config_ini = extra['binpkg_config_ini']
            cmd = [download_exe_path, '--cfgfile', binpkg_config_ini,  '--port', self.com_info['port']]
            print('------------------Eigen downloading upgrade package(binpkg): ------------------')
        elif self.platform.upper() == "FCM360W":
            cmd = [download_exe_path, '-p', self.com_info['port'][3:], '-b', "921600", '-file', fw_filepath]
            print('------------------ FCM360W downloading factory package: ------------------')
        elif self.platform.upper() == "FC41D":
            raise ValueError('{} not supported!'.format(self.platform))
        else:
            raise ValueError('{} not supported!'.format(self.platform))

        logger.info('run cmd: {}'.format(cmd))
        return run_cmd(cmd, self.platform, str(Path(download_exe_path).parent), **extra)
