import glob
import shutil
import tempfile
from threading import Lock
from .proc import Process
from .utils import *
from logging import getLogger


EXES_PATH = Path(__file__).with_name('exes')
logger = getLogger(__name__)


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


class LineParserAsr(object):

    def __init__(self):
        self.json_string = ""
        self.flag = False

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
                    return rv['progress']


class LineParser200A(object):

    def parse(self, line):
        if "Successfully to prepare temp folder file for wtptp download" in line:
            return "RESET"

        if "Download percentage" in line:
            return int(line.strip().split(' ')[-1])

        if "flash percentage" in line:
            return int(line.strip().split(' ')[-1])


class LineParserBG95(object):

    def __init__(self):
        self.progress = 0

    def parse(self, line):

        if '[1]DL-' in line:
            self.progress += 2
            return self.progress

        if '[1]Total upgrade time is' in line:
            return 100

        if '[1]FW upgrade fail' in line:
            raise Exception('BG95 FW Download Failed.')


class LineParserNB(object):

    def parse(self, line):
        if '[1]FW upgrade fail.' in line:
            raise Exception('NB FW Download Failed.')

        if "[1]Upgrade:" in line:
            progress = int(line.replace("[1]Upgrade:", '').strip()[:-1])
            return progress


class LineParserUnisoc(object):

    def __init__(self):
        self.progress = 0

    def parse(self, line):

        if "Downloading..." in line:
            self.progress += 1
            return self.progress * 10

        if "DownLoad Passed" in line:
            return 100

        if "[ERROR] DownLoad Failed" in line:
            raise Exception('Unisoc FW Download Failed.')


def run_cmd(cmd, process_type, cwd):
    logger.info('enter run_cmd method, args: {}'.format((cmd, process_type, cwd,)))

    with DownloadLogFile() as f:

        proc = Process(cmd, cwd)
        proc.run()
        running_timeout = 60

        if process_type == "unisoc":
            parser = LineParserUnisoc()
        elif process_type == "NB":
            parser = LineParserNB()
        elif process_type == "BG95":
            parser = LineParserBG95()
        elif process_type == '200A':
            parser = LineParser200A()
        else:
            parser = LineParserAsr()

        for line in proc.read_lines(timeout=running_timeout):
            f.write(line)
            rv = parser.parse(line)
            if rv:
                yield rv


class FwDownloadHandler(object):

    def __init__(self, firmware_file_path, com_info):
        self.fw_filepath = Path(firmware_file_path)
        self.com_info = com_info

    def download(self):
        logger.info('enter FwDownloadHandler.download method.')
        if Path(self.fw_filepath).exists():
            logger.info('fw_filepath with suffix \"{}\".'.format(self.fw_filepath.suffix))
            if self.fw_filepath.suffix == ".pac":
                return self.rdaFwDownload()
            elif self.fw_filepath.suffix == ".lod":
                return self.nbFwDownload()
            elif self.fw_filepath.suffix == ".blf":
                return self.blfFwDownload()
            elif self.fw_filepath.suffix == ".mbn":
                return self.mbnFwDownload()
            else:
                return self.asrFwDownload()
        else:
            raise Exception('固件文件不存在。')

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

    def fw_download(self, download_exe_path, fw_filepath):
        logger.info('enter FwDownloadHandler.fw_download method.')

        if self.fw_filepath.suffix == ".pac":
            cmd = [download_exe_path, '-pac', fw_filepath]
            logger.info('------------------unisoc downloading upgrade package------------------')
            downloadProcess = 'unisoc'
        elif self.fw_filepath.suffix == ".lod":
            cmd = [download_exe_path, self.com_info['port'][3:], self.com_info['baudrate'], fw_filepath]
            logger.info('------------------NB downloading upgrade package------------------')
            downloadProcess = 'NB'
        elif self.fw_filepath.suffix == ".blf":
            cmd = [download_exe_path, '-f', fw_filepath]
            logger.info('------------------200A download downloading factory package(blf)------------------')
            downloadProcess = '200A'
        elif self.fw_filepath.suffix == ".mbn":
            cmd = [download_exe_path, self.com_info['port'][3:], self.com_info['baudrate'], fw_filepath]
            logger.info('------------------BG95 download downloading factory package(mbn)------------------')
            downloadProcess = 'BG95'
        else:
            cmd = [
                download_exe_path, '-p', self.com_info['port'],
                '-a', '-q', '-r', '-s', self.com_info['baudrate'], fw_filepath
            ]
            logger.info('------------------adownload downloading factory package------------------')
            downloadProcess = '"progress" :'

        logger.info('run cmd: {}'.format(cmd))
        return run_cmd(cmd, downloadProcess, str(Path(download_exe_path).parent))
