"""QuecPython编程套件主窗口"""
from threading import Thread
from pathlib import Path
from logging import getLogger
from serial import Serial
from serial.tools import list_ports
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
from thonny import get_workbench
from .api import DownLoadFWApi
from .fw.utils import get_com_port
from .locale import tr


logger = getLogger(__name__)


class QuecView(tk.Frame):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('borderwidth', 10)
        super().__init__(*args, **kwargs)

        # >>> 串口配置
        serial_label_frame = tk.LabelFrame(master=self, text=tr('Serial Settings'), labelanchor=tk.N)
        serial_label_frame.pack(anchor=tk.NW, expand=False, fill=tk.X, pady=(5, 5))
        for index in range(14):
            serial_label_frame.columnconfigure(index, weight=1)

        serial_label = tk.Label(serial_label_frame, text=tr('Serial')+':')
        serial_label.grid(row=0, column=0, sticky=tk.N, padx=(5, 0), pady=(5, 5))
        self.port_combobox = ttk.Combobox(master=serial_label_frame, postcommand=self.list_valid_ports)
        self.port_combobox.grid(row=0, column=1, ipadx=40, sticky=tk.W, padx=(0, 5), pady=(5, 5))
        self.list_valid_ports()

        baudrate_label = tk.Label(serial_label_frame, text=tr('Baudrate')+':')
        baudrate_label.grid(row=0, column=2, sticky=tk.N, padx=(5, 0), pady=(5, 5))
        self.baudrate_combobox = ttk.Combobox(master=serial_label_frame, values=Serial.BAUDRATES, width=7)
        self.baudrate_combobox.set('115200')
        self.baudrate_combobox.grid(row=0, column=3, sticky=tk.W, padx=(0, 5), pady=(5, 5))

        stopbits_label = tk.Label(serial_label_frame, text=tr('Stopbits')+':')
        stopbits_label.grid(row=0, column=4, sticky=tk.N, padx=(5, 0), pady=(5, 5))
        self.stopbits_combobox = ttk.Combobox(master=serial_label_frame, values=Serial.STOPBITS, width=5)
        self.stopbits_combobox.set('1')
        self.stopbits_combobox.grid(row=0, column=5, sticky=tk.W, padx=(0, 5), pady=(5, 5))

        parity_label = tk.Label(serial_label_frame, text=tr('Parity')+':')
        parity_label.grid(row=0, column=6, sticky=tk.N, padx=(5, 0), pady=(5, 5))
        self.parity_combobox = ttk.Combobox(master=serial_label_frame, values=Serial.PARITIES, width=5)
        self.parity_combobox.set('N')
        self.parity_combobox.grid(row=0, column=7, sticky=tk.W, padx=(0, 5), pady=(5, 5))

        bytesize_label = tk.Label(serial_label_frame, text=tr('Bytesize')+':')
        bytesize_label.grid(row=0, column=8, sticky=tk.N, padx=(5, 0), pady=(5, 5))
        self.bytesize_combobox = ttk.Combobox(master=serial_label_frame, values=Serial.BYTESIZES, width=5)
        self.bytesize_combobox.set('8')
        self.bytesize_combobox.grid(row=0, column=9, sticky=tk.W, padx=(0, 5), pady=(5, 5))

        flow_control_label = tk.Label(serial_label_frame, text=tr('Flow')+':')
        flow_control_label.grid(row=0, column=10, sticky=tk.N, padx=(5, 0), pady=(5, 5))
        self.flow_control_combobox = ttk.Combobox(master=serial_label_frame, values=['No', 'HW', 'SW'], width=5)
        self.flow_control_combobox.set('No')
        self.flow_control_combobox.grid(row=0, column=11, sticky=tk.W, padx=(0, 5), pady=(5, 5))

        self.open_serial_button = tk.Button(
            serial_label_frame, text=tr('OpenPort'),
            command=self.switch_serial_handler
        )
        self.open_serial_button.grid(row=0, column=12, sticky=tk.EW, padx=(5, 5), pady=(5, 5))
        # <<<

        # >>> 固件下载
        fw_label_frame = tk.LabelFrame(master=self, text=tr('Firmware Download'), labelanchor=tk.N)
        fw_label_frame.pack(anchor=tk.NW, expand=False, fill=tk.X, pady=(5, 5))
        for index in range(14):
            fw_label_frame.columnconfigure(index, weight=1)

        fw_file_path_label = tk.Label(fw_label_frame, text=tr('firmware path')+':')
        fw_file_path_label.grid(row=1, column=0, sticky=tk.EW, padx=(5, 0), pady=(5, 5))
        self.firmware_file_path_stringvar = tk.StringVar()
        self.firmware_file_path_stringvar.trace_variable('w', self.on_fw_file_path_write)
        fw_file_path_entry = tk.Entry(fw_label_frame, textvariable=self.firmware_file_path_stringvar, state='readonly')
        fw_file_path_entry.grid(row=1, column=1, columnspan=11, sticky=tk.EW, padx=(0, 5), pady=(5, 5))

        self.fw_file_choose_button = tk.Button(
            fw_label_frame, text=tr('select'),
            command=self.ask_for_firmware_file_path
        )
        self.fw_file_choose_button.grid(row=1, column=12, sticky=tk.EW, padx=(5, 5), pady=(5, 5))

        self.fw_download_button = tk.Button(
            fw_label_frame, text=tr('download'),
            command=self.download_firmware_handler
        )
        self.fw_download_button.grid(row=1, column=13, sticky=tk.EW, padx=(5, 5), pady=(5, 5))

        progress_label = tk.Label(fw_label_frame, text=tr('progress')+':')
        progress_label.grid(row=2, column=0, sticky=tk.EW, padx=(5, 0), pady=(5, 5))
        self.bar = ttk.Progressbar(master=fw_label_frame, maximum=100)
        self.bar.grid(row=2, column=1, columnspan=11, sticky=tk.EW, padx=(0, 5), pady=(5, 5))

        self.progress_stringvar = tk.StringVar()
        self.progress_stringvar.set('0%')
        progress_entry = tk.Label(fw_label_frame, textvariable=self.progress_stringvar)
        progress_entry.grid(row=2, column=12, sticky=tk.W, padx=(5, 5), pady=(5, 5))

        log_label = tk.Label(fw_label_frame, text=tr('logging')+':')
        log_label.grid(row=3, column=0, sticky=tk.EW, padx=(5, 0), pady=(5, 5))
        self.log_stringvar = tk.StringVar()
        self.log_stringvar.set(tr('ready'))
        log_entry = tk.Label(fw_label_frame, textvariable=self.log_stringvar)
        log_entry.grid(row=3, column=1, sticky=tk.W, padx=(0, 5), pady=(5, 5))
        # <<<

        # >>> 订阅
        DownLoadFWApi.bind(self.update_progress)
        # <<<

        # >>> 串口通信对象
        self.serial = None
        # <<<

    def switch_serial_handler(self):
        if self.serial is None:
            try:
                # TODO: 流控未处理: self.flow_control_combobox
                self.serial = Serial(
                    port=self.port_combobox.get().split('-')[0],
                    baudrate=int(self.baudrate_combobox.get()),
                    bytesize=int(self.bytesize_combobox.get()),
                    parity=self.parity_combobox.get(),
                    stopbits=int(self.stopbits_combobox.get())
                )
            except Exception as e:
                messagebox.showerror(
                    title=tr('Open Port Failed!'),
                    message='{}'.format(str(e)),
                    master=self
                )
                return
            self.open_serial_button['text'] = tr('ClosePort')
            self.set_com_widgets_state(tk.DISABLED)
        else:
            if self.serial.isOpen():
                self.serial.close()
                self.serial = None
            self.open_serial_button['text'] = tr('OpenPort')
            self.set_com_widgets_state(tk.ACTIVE)

    def set_com_widgets_state(self, state):
        self.port_combobox.config(state=state)
        self.baudrate_combobox.config(state=state)
        self.stopbits_combobox.config(state=state)
        self.parity_combobox.config(state=state)
        self.bytesize_combobox.config(state=state)
        self.flow_control_combobox.config(state=state)

    def list_valid_ports(self):
        rv = []
        for p in list_ports.comports():
            rv.append("{}-{}".format(p.device, p.description))

        self.port_combobox['value'] = rv
        current_port_str = self.port_combobox.get()
        if current_port_str in rv:
            self.port_combobox.set(current_port_str)
        else:
            self.port_combobox.current(0)

    def get_validated_com_port(self, firmware_file_path):
        comport = get_com_port(Path(firmware_file_path))
        logger.info('detect comport is: {}'.format(comport))
        if comport is None:
            messagebox.showerror(
                title=tr('Choose a COM Port'),
                message=tr('Device not found!'),
                master=self
            )
            return

        rv = {'port': comport, 'baudrate': '115200'}

        if comport in ("NB_DOWNLOAD", "mbn_DOWNLOAD"):
            if (self.serial is None) or (not self.serial.isOpen()):
                messagebox.showinfo(
                    title=tr('Choose a COM Port'),
                    message=tr('please open one COM Port for downloading.'),
                    master=self
                )
                return
            else:
                if comport == "NB_DOWNLOAD":
                    if not messagebox.askyesno(
                        title=tr('Respect'),
                        message=tr('Long press Power button, and then click ok.'),
                        master=self
                    ):
                        self.log_stringvar.set(tr('progress canceled!'))
                        return

                self.switch_serial_handler()
                rv['port'] = self.port_combobox.get().split('-')[0]
                rv['baudrate'] = self.baudrate_combobox.get()

        logger.info('real comport is: {}'.format(comport))
        return rv

    def ask_for_firmware_file_path(self):
        firmware_file_path = filedialog.askopenfilename(title=tr('choose firmware file'))
        if firmware_file_path:
            self.firmware_file_path_stringvar.set(firmware_file_path)

    def on_fw_file_path_write(self, *args, **kwargs):
        firmware_file_path = self.firmware_file_path_stringvar.get()
        comport = get_com_port(Path(firmware_file_path))
        if comport in ("NB_DOWNLOAD", "mbn_DOWNLOAD"):
            self.set_com_widgets_state(tk.ACTIVE)
        else:
            self.set_com_widgets_state(tk.DISABLED)

    def get_validated_fw_file_path(self):
        firmware_file_path = self.firmware_file_path_stringvar.get()
        logger.info('firmware_file_path: {}'.format(firmware_file_path))
        if not firmware_file_path:
            messagebox.showerror(
                title=tr('Error'),
                message=tr('no firmware file path selected!'),
                master=self
            )
            return
        return firmware_file_path

    def download_widgets_ready(self):
        self.fw_file_choose_button.config(state=tk.DISABLED)
        self.fw_download_button.config(state=tk.DISABLED)
        self.bar["value"] = 0
        self.progress_stringvar.set("{}%".format(0))
        self.log_stringvar.set(tr("ready"))
        self.update()

    def download_firmware_handler(self):
        firmware_file_path = self.get_validated_fw_file_path()
        if not firmware_file_path:
            return

        com_info = self.get_validated_com_port(firmware_file_path)
        if not com_info:
            return

        self.download_widgets_ready()
        Thread(target=DownLoadFWApi(firmware_file_path, com_info)).start()

    def update_progress(self, payload):
        if payload.code == DownLoadFWApi.OK:
            if payload.data == "RESET":
                messagebox.showinfo(
                    title=tr('Respect'),
                    message=tr('click RESET button, and then click "OK" continue.'),
                    master=self
                )
                return
            self.progress_stringvar.set("{}%".format(payload.data))
            self.bar["value"] = payload.data
            self.log_stringvar.set(tr('downloading...'))
            self.update()
        elif payload.code == DownLoadFWApi.EXIT:
            if payload.exec:
                messagebox.showerror(
                    title=tr('Error'),
                    message='{}!\n{}'.format(tr('Download Firmware Error'), str(payload.exec)),
                    master=self
                )
            else:
                self.log_stringvar.set(tr('download process exited.'))
                messagebox.showinfo(
                    title=tr('Information'),
                    message=tr('Download Firmware Progress Finished!'),
                    master=self
                )
            self.fw_file_choose_button.config(state=tk.ACTIVE)
            self.fw_download_button.config(state=tk.ACTIVE)
        else:
            # nothing
            pass


def open_quecview():
    get_workbench().show_view('QuecView')

