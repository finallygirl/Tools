from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
import sys
import os
import json
from datetime import datetime
import requests
import socket
import time

class ConnectionMonitor(QThread):
    status_changed = pyqtSignal(bool)

    def __init__(self, host, port, interval=5):
        super().__init__()
        self.host = host
        self.port = port
        self.interval = interval
        self.running = True

    def run(self):
        while self.running:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(5)
                    s.connect((self.host, self.port))
                    self.status_changed.emit(True)
            except Exception:
                self.status_changed.emit(False)
            time.sleep(self.interval)

    def stop(self):
        self.running = False
        self.wait()

class TestUI(QWidget):
    def __init__(self):
        super().__init__()
        self.test_values = []
        self.init_ui()
        self.init_files()
        self.start_monitor()

    def init_ui(self):
        self.setWindowTitle("STATION371 DCR_Test v3.0")
        self.setGeometry(100, 100, 1000, 750)

        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', 'Microsoft YaHei';
                font-size: 14px;
            }
            QLineEdit {
                border: 2px solid #ccc;
                border-radius: 8px;
                padding: 8px;
                font-size: 16px;
            }
            QLineEdit:focus {
                border: 2px solid #409EFF;
                outline: none;
            }
            QPushButton {
                background-color: #409EFF;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #66b1ff;
            }
            QLabel {
                font-size: 14px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # -------- area1: Top section --------
        area1 = QWidget()
        area1_layout = QHBoxLayout(area1)
        area1_layout.setSpacing(15)

        self.sn_input = QLineEdit()
        self.sn_input.setPlaceholderText("Input SN...")
        self.sn_input.returnPressed.connect(self.start_test)
        self.sn_input.setFixedHeight(40)

        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.start_test)
        self.start_btn.setFixedHeight(40)
        self.start_btn.setFixedWidth(100)

        left_up_layout = QHBoxLayout()
        left_up_layout.setSpacing(10)
        left_up_layout.addWidget(self.sn_input)
        left_up_layout.addWidget(self.start_btn)

        self.pass_label = QLabel("🟢 Pass: 0")
        self.fail_label = QLabel("🔴 Fail: 0")
        self.total_label = QLabel("🔵 Total: 0")
        self.yield_label = QLabel("🟡 Yield: 0%")

        left_down_layout = QHBoxLayout()
        left_down_layout.setSpacing(20)
        for label in [self.pass_label, self.fail_label, self.total_label, self.yield_label]:
            label.setStyleSheet("font-weight: bold;")
            left_down_layout.addWidget(label)

        left_layout = QVBoxLayout()
        left_layout.addLayout(left_up_layout)
        left_layout.addLayout(left_down_layout)

        self.meter_label = QLabel("Meter")
        self.meter_label.setAlignment(Qt.AlignCenter)
        self.meter_label.setFixedHeight(105)
        self.meter_label.setStyleSheet("""
            background-color: #F5F7FA; 
            border: 1px solid #ccc; 
            font-size: 20px;
            border-radius: 10px; 
            font-weight: bold;
            color:white;
        """)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.meter_label)
        right_layout.addStretch()

        area1_layout.addLayout(left_layout, 4)
        area1_layout.addLayout(right_layout, 1)

        # -------- area2: Center result display --------
        area2 = QWidget()
        area2_layout = QVBoxLayout(area2)

        self.result_display = QLabel("Ready for test")
        self.result_display.setAlignment(Qt.AlignCenter)
        self.result_display.setFixedHeight(120)
        self.set_result_color("ready")

        area2_layout.addWidget(self.result_display)

        # -------- area3: Bottom table --------
        area3 = QWidget()
        area3_layout = QVBoxLayout(area3)

        self.table = QTableWidget()
        table_title = ["Test item", "Test value", "Test result", "Test limits"]
        self.table.setColumnCount(len(table_title))
        self.table.setHorizontalHeaderLabels(table_title)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #fff;
                border: 1px solid #ccc;
                border-radius: 8px;
            }
            QHeaderView::section {
                padding: 5px;
                font-weight: bold;
            }
        """)

        self.test_items = ["Read_SN", "Check_UOP", "Detection_DUT", "First", "Second", "Third", "Average"]
        
        area3_layout.addWidget(self.table)

        # -------- Add to main layout --------
        layout.addWidget(area1, stretch=1)
        layout.addWidget(area2, stretch=1)
        layout.addWidget(area3, stretch=3)

        self.test_timer = QTimer()
        self.test_timer.timeout.connect(self.update_test_item)

    def init_files(self):
        # exec_path = os.path.dirname(sys.executable)
        exec_path = '/Users/kid.wang/Desktop'
        self.folder_path = os.path.join(exec_path, "DCR_Test")
        os.makedirs(self.folder_path, exist_ok=True)
        self.config_file = os.path.join(self.folder_path, "config.json")
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        self.counts_file = os.path.join(self.folder_path, "counts.json")
        if os.path.exists(self.counts_file):
            with open(self.counts_file, 'r') as f:
                self.counts = json.load(f)

    def set_result_color(self, status):
        bg_style = """
            background-color: {};
            border: 2px solid #ccc;
            font-size: 28px;
            font-weight: bold;
            border-radius: 12px;
        """
        if status == "ready":
            self.result_display.setText("Ready for test")
            self.result_display.setStyleSheet(bg_style.format("#F5F7FA"))
        elif status == "testing":
            self.result_display.setText("Testing...")
            self.result_display.setStyleSheet(bg_style.format("#FFF176"))
        elif status == "pass":
            self.result_display.setText("PASS")
            self.result_display.setStyleSheet(bg_style.format("#aaffaa"))
        elif status == "fail":
            self.result_display.setText("FAIL")
            self.result_display.setStyleSheet(bg_style.format("#ffaaaa"))

    def start_monitor(self):
        self.monitor = ConnectionMonitor(self.config['ip'],self.config['port'],self.config['interval'])
        self.monitor.status_changed.connect(self.update_status)
        self.monitor.start()
    
    def change_meter_label_color(self, color):
        self.meter_label.setStyleSheet(f"""
            background-color: {color}; 
            border: 1px solid #ccc; 
            font-size: 20px;
            border-radius: 10px; 
            font-weight: bold;
            color:white;
        """)

    def update_status(self, is_connected):
        color = "#00C853" if is_connected else "#F44336"
        self.change_meter_label_color(color)
        self.meter_label.setText("✔ Meter" if is_connected else "✖ Meter")

    def start_test(self):
        self.result_display.setText("Testing...")
        self.table.setRowCount(0)
        self.set_result_color("testing")
        self.start_btn.setEnabled(False)
        self.sn_input.setEnabled(False)
        self.current_test = 0
        self.test_timer.start(500)
    
    def update_row(self, row, item, value, result, limits=""):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(item))
            v = QTableWidgetItem(value)
            v.setToolTip(value)
            self.table.setItem(row, 1, v)
            self.table.setItem(row, 2, QTableWidgetItem(result))
            self.table.setItem(row, 3, QTableWidgetItem(limits))
            self.table.setRowHeight(row, 32)
    
    def stop_test(self, result:str):
        self.set_result_color(result.lower())
        self.sn_input.setEnabled(True)
        self.sn_input.clear()
        self.sn_input.setFocus()
        self.test_timer.stop()
        if hasattr(self, 'socket'):
            self.socket.close()
        self.start_btn.setEnabled(True)

    def check_uop(self):
        url = self.config["bobcat"]["url"]
        bobcat_query = self.config["bobcat"]["query"]
        bobcat_query["sn"] = self.sn
        uop_result = requests.post(url, data = bobcat_query).text
        return uop_result
    
    def upload_data(self, result, avg):
        url = self.config["bobcat"]["url"]

        bobcat_upload = self.config["bobcat"]["upload"]
        bobcat_upload["sn"] = self.sn
        bobcat_upload["dcr_avg"] = avg if avg < 999999 else 999999
        requests.post(url, data = bobcat_upload)

        bobcat_result = self.config["bobcat"]["pass"]
        bobcat_result["sn"] = self.sn
        bobcat_result["result"] = result
        bobcat_result["start_time"] = self.start_time
        bobcat_result["stop_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if result == "FAIL":
            bobcat_result.update(self.config["bobcat"]["fail"])
        requests.post(url, data = bobcat_result)

    def send(self, cmd:str):
        self.socket.sendall(f"{cmd.strip()}\n".encode())

    def send_and_read(self, cmd:str):
        self.send(cmd)
        data = self.socket.recv(1024)
        return data.decode().strip()

    def init_fixture(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        HOST = self.config.get('ip')
        PORT = int(self.config.get('port'))
        self.socket.settimeout(5)
        try:
            self.socket.connect((HOST, PORT))
            COMMANDS = self.config.get('init')
            for cmd in COMMANDS:
                self.send(cmd)
            return True
        except Exception as e:
            return False

    def update_stats(self):
        self.counts["Total"] = self.counts["Pass"] + self.counts["Fail"]
        self.counts["Yield"] = f'{self.counts["Pass"]/self.counts["Total"]*100:.2f}%'
        with open(self.counts_file, 'w', encoding='utf-8') as f:
            json.dump(self.counts, f)
        self.pass_label.setText(f'🟢 Pass: {self.counts["Pass"]}')
        self.fail_label.setText(f'🔴 Fail: {self.counts["Fail"]}')
        self.total_label.setText(f'🔵 Total: {self.counts["Total"]}')
        self.yield_label.setText(f'🟡 Yield: {self.counts["Yield"]}')
        

    def update_test_item(self):
        if self.current_test == 0:
            self.start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.sn = self.sn_input.text().strip()
            if self.sn:
                result = "PASS"
                value = self.sn 
            else:
                result = "FAIL"
                value = "SN cannot be empty"
                self.stop_test(result)
            
            self.update_row(self.current_test, self.test_items[self.current_test], value, result)
      
        elif self.current_test == 1:
            uop_text = self.check_uop()
            uop_result = "unit_process_check=OK" in uop_text
            result = "PASS" if uop_result else "FAIL"
            if not uop_result:
                self.stop_test(result)
            self.update_row(self.current_test, self.test_items[self.current_test], uop_text, result)
        
        elif self.current_test == 2:
            state = self.init_fixture()
            result = "FAIL"
            max_num = self.config["overload"]
            if not state:
                value = "Multimeter connection failed"
                self.stop_test(result)
            else:
                timeout = self.config["timeout"]
                start_time = time.time()
                while time.time() - start_time < timeout:
                    value = abs(float(self.send_and_read(self.config['reader'])))
                    if value < max_num:
                        result = "PASS"
                        break
                    else:
                        time.sleep(1)
                else:
                    if self.config["mes"]:
                        self.upload_data(result, value) 
                    self.counts["Fail"] = int(self.counts["Fail"]) + 1
                    self.update_stats()
                    self.stop_test(result)

            self.update_row(self.current_test, self.test_items[self.current_test], str(value), result, f"[0, {max_num}]")
        elif 3 <= self.current_test <= 5:
            value = self.send_and_read(self.config['reader'])
            self.test_values.append(abs(float(value)))
            self.update_row(self.current_test, self.test_items[self.current_test], str(value), "PASS")
        elif self.current_test == 6:
            avg = round(sum(self.test_values)/3, 4)
            self.test_values = []
            lower = self.config["limits"]["lower"]
            upper = self.config["limits"]["upper"]
            result = "PASS" if lower <= avg <= upper else "FAIL"
            if result == "PASS":
                self.counts["Pass"] = int(self.counts["Pass"]) + 1
            else:
                self.counts["Fail"] = int(self.counts["Fail"]) + 1
            if self.config["mes"]:
                self.upload_data(result, avg) 
            self.update_stats()
            self.stop_test(result)
            self.update_row(self.current_test, self.test_items[self.current_test], str(avg), result, f"[{lower}, {upper}]")
        self.current_test += 1


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestUI()
    window.show()
    sys.exit(app.exec_())
