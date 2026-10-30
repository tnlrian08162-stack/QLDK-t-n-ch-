import sys
import os
from datetime import datetime as _dt
import traceback
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QDateTimeEdit, QMessageBox, QFormLayout, QGroupBox,
    QApplication, QMainWindow, QAbstractItemView, QLineEdit, QSpinBox, QCheckBox
)
from PyQt5.QtCore import Qt, QDateTime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models.method import HocKyModel
from models.admin import AdminModel

# UI nhà trường
class SchoolWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hệ thống Quản lý - Dành cho Nhà trường")
        self.resize(1000, 600)
        self.setup_ui()
        self._pending_dirty_schedule_conn = None
        self.load_data()

    def setup_ui(self):
        # Widget trung tâm
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Tiêu đề
        lbl_title = QLabel("BẢNG ĐIỀU KHIỂN NHÀ TRƯỜNG")
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; margin: 10px;")
        main_layout.addWidget(lbl_title)

        # Tab Widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Khởi tạo các Tab
        self.init_tab_hoc_ky()
        self.init_tab_hoc_phan()
        self.init_tab_thong_ke()

        self.tabs.addTab(self.tab_hoc_ky, "Quản lý Học kỳ")
        self.tabs.addTab(self.tab_hoc_phan, "Quản lý Học phần")
        self.tabs.addTab(self.tab_thong_ke, "Thống kê Đăng ký")

    def init_tab_hoc_ky(self):
        self.tab_hoc_ky = QWidget()
        layout = QVBoxLayout(self.tab_hoc_ky)

        # Bảng danh sách học kỳ
        self.table_hk = QTableWidget()
        self.table_hk.setColumnCount(5)
        self.table_hk.setHorizontalHeaderLabels(["Mã HK", "Tên Học Kỳ", "Năm Học", "Ngày Mở ĐK", "Ngày Đóng ĐK"])
        self.table_hk.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_hk.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_hk.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_hk.itemSelectionChanged.connect(self.on_hk_selected)
        layout.addWidget(self.table_hk)

        # Khung thiết lập thời gian
        group_box = QGroupBox("Thiết lập thời gian đăng ký học phần")
        form_layout = QFormLayout()

        self.cb_ma_hk = QComboBox()
        self.dt_mo = QDateTimeEdit(QDateTime.currentDateTime())
        self.dt_mo.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.dt_mo.setCalendarPopup(True)

        self.dt_dong = QDateTimeEdit(QDateTime.currentDateTime().addDays(30))
        self.dt_dong.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.dt_dong.setCalendarPopup(True)

        btn_luu = QPushButton("Lưu Thiết Lập")
        btn_luu.setMinimumHeight(40)
        btn_luu.setStyleSheet("background-color: #2e8b57; color: white; font-weight: bold;")
        btn_luu.clicked.connect(self.save_thoi_gian_dang_ky)

        btn_deadlock = QPushButton("Cập nhật HK (Deadlock Demo)")
        btn_deadlock.setMinimumHeight(40)
        btn_deadlock.setStyleSheet("background-color: #d9534f; color: white; font-weight: bold;")
        btn_deadlock.clicked.connect(self.do_deadlock_admin)
        btn_deadlock.setToolTip("Gây ra lỗi Deadlock nếu Sinh viên đang bấm Đăng ký (Deadlock Demo).")

        h_btn_layout = QHBoxLayout()
        h_btn_layout.addWidget(btn_luu)
        h_btn_layout.addWidget(btn_deadlock)

        form_layout.addRow("Chọn Học Kỳ:", self.cb_ma_hk)
        form_layout.addRow("Ngày Mở Đăng Ký:", self.dt_mo)
        form_layout.addRow("Ngày Đóng Đăng Ký:", self.dt_dong)
        form_layout.addRow("", h_btn_layout)

        group_box.setLayout(form_layout)
        layout.addWidget(group_box)

    def init_tab_hoc_phan(self):
        self.tab_hoc_phan = QWidget()
        layout = QVBoxLayout(self.tab_hoc_phan)

        # Bộ lọc
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Chọn Học Kỳ:"))
        self.cb_filter_hp_hk = QComboBox()
        self.cb_filter_hp_hk.currentIndexChanged.connect(self.load_quan_ly_hoc_phan)
        filter_layout.addWidget(self.cb_filter_hp_hk)
        
        btn_refresh_hp = QPushButton("Làm mới")
        btn_refresh_hp.clicked.connect(self.load_quan_ly_hoc_phan)
        filter_layout.addWidget(btn_refresh_hp)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Bảng danh sách học phần
        self.table_quan_ly_hp = QTableWidget()
        self.table_quan_ly_hp.setColumnCount(4)
        self.table_quan_ly_hp.setHorizontalHeaderLabels(["Mã Học Phần", "Tên Học Phần", "Số Tín Chỉ", "Bắt Buộc"])
        self.table_quan_ly_hp.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_quan_ly_hp.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_quan_ly_hp.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_quan_ly_hp.itemSelectionChanged.connect(self.on_quan_ly_hp_selected)
        layout.addWidget(self.table_quan_ly_hp)

        # Form chỉnh sửa
        form_group = QGroupBox("Thông tin Học phần ")
        f_layout = QFormLayout()

        self.txt_ma_hp = QLineEdit()
        self.txt_ten_hp = QLineEdit()
        self.spn_tc = QSpinBox()
        self.spn_tc.setRange(1, 10)
        self.chk_bb = QCheckBox("Môn Bắt buộc")

        f_layout.addRow("Mã Học Phần:", self.txt_ma_hp)
        f_layout.addRow("Tên Học Phần:", self.txt_ten_hp)
        f_layout.addRow("Số Tín Chỉ:", self.spn_tc)
        f_layout.addRow("", self.chk_bb)

        # Nút chức năng
        h_btn = QHBoxLayout()
        btn_them = QPushButton("➕ Thêm mới")
        btn_them.setStyleSheet("background-color: #17a2b8; color: white;")
        btn_them.clicked.connect(self.do_them_hp)
        btn_them.setToolTip("Gây ra lỗi Phantom Read nếu sinh viên đang xem danh sách.")
        
        btn_xoa = QPushButton("🗑️ Xóa")
        btn_xoa.setStyleSheet("background-color: #dc3545; color: white;")
        btn_xoa.clicked.connect(self.do_xoa_hp)
        
        btn_update = QPushButton("🔄 Cập nhật ")
        btn_update.setStyleSheet("background-color: #ffc107; color: black; font-weight: bold;")
        btn_update.clicked.connect(self.do_update_dirty_read)
        btn_update.setToolTip("Cập nhật với thông báo xác nhận. Tạm giữ Transaction chưa Commit.")

        h_btn.addWidget(btn_them)
        h_btn.addWidget(btn_xoa)
        h_btn.addWidget(btn_update)
        f_layout.addRow("", h_btn)

        form_group.setLayout(f_layout)
        layout.addWidget(form_group)

        # Bảng chi tiết lịch học của lớp học phần để admin chỉnh sửa
        schedule_group = QGroupBox("Chi tiết lịch học của lớp học phần")
        schedule_layout = QVBoxLayout(schedule_group)

        schedule_select_layout = QHBoxLayout()
        schedule_select_layout.addWidget(QLabel("Chọn Lớp HP:"))
        self.cb_schedule_lhp = QComboBox()
        self.cb_schedule_lhp.setMinimumWidth(260)
        self.cb_schedule_lhp.currentIndexChanged.connect(self.load_schedule_details)
        schedule_select_layout.addWidget(self.cb_schedule_lhp)

        btn_refresh_schedule = QPushButton("Tải lại lịch học")
        btn_refresh_schedule.clicked.connect(self.load_schedule_details)
        schedule_select_layout.addWidget(btn_refresh_schedule)
        schedule_select_layout.addStretch()
        schedule_layout.addLayout(schedule_select_layout)

        self.table_schedule_details = QTableWidget()
        self.table_schedule_details.setColumnCount(4)
        self.table_schedule_details.setHorizontalHeaderLabels(["Mã CTLHP", "Thứ học", "Ca học", "Phòng học"])
        self.table_schedule_details.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_schedule_details.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        schedule_layout.addWidget(self.table_schedule_details)

        btn_save_schedule = QPushButton("Lưu tạm (Dirty Read)")
        btn_save_schedule.setStyleSheet("background-color: #007bff; color: white; font-weight: bold;")
        btn_save_schedule.clicked.connect(self.save_schedule_changes)
        schedule_layout.addWidget(btn_save_schedule)

        btn_commit_schedule = QPushButton("Commit thay đổi")
        btn_commit_schedule.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")
        btn_commit_schedule.clicked.connect(self.commit_schedule_changes)
        btn_commit_schedule.setEnabled(False)
        schedule_layout.addWidget(btn_commit_schedule)
        self.btn_commit_schedule = btn_commit_schedule

        btn_rollback_schedule = QPushButton("Rollback thay đổi")
        btn_rollback_schedule.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold;")
        btn_rollback_schedule.clicked.connect(self.rollback_schedule_changes)
        btn_rollback_schedule.setEnabled(False)
        schedule_layout.addWidget(btn_rollback_schedule)
        self.btn_rollback_schedule = btn_rollback_schedule

        self.lbl_schedule_status = QLabel("Chưa chọn lớp học phần.")
        self.lbl_schedule_status.setStyleSheet("color: #666; margin-top: 4px;")
        schedule_layout.addWidget(self.lbl_schedule_status)

        layout.addWidget(schedule_group)

    def init_tab_thong_ke(self):
        self.tab_thong_ke = QWidget()
        layout = QVBoxLayout(self.tab_thong_ke)

        # Bộ lọc
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Chọn Học Kỳ:"))
        self.cb_filter_hk = QComboBox()
        self.cb_filter_hk.currentIndexChanged.connect(self.load_thong_ke)
        filter_layout.addWidget(self.cb_filter_hk)
        
        btn_refresh = QPushButton("Làm mới")
        btn_refresh.clicked.connect(self.load_thong_ke)
        filter_layout.addWidget(btn_refresh)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Bảng thống kê
        self.table_tk = QTableWidget()
        self.table_tk.setColumnCount(7)
        self.table_tk.setHorizontalHeaderLabels([
            "Mã Lớp HP", "Mã HP", "Tên Môn Học", "Sĩ Số Tối Đa", 
            "Đã Đăng Ký", "Còn Trống", "Tỷ lệ (%)"
        ])
        self.table_tk.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_tk.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_tk.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table_tk)

        # Timestamp – Phantom Read awareness
        self.lbl_tk_timestamp = QLabel("")
        self.lbl_tk_timestamp.setStyleSheet("color: #888; font-size: 11px; padding: 2px 4px;")
        self.lbl_tk_timestamp.setAlignment(Qt.AlignRight)
        layout.addWidget(self.lbl_tk_timestamp)

    def load_data(self):
        # Lấy dữ liệu học kỳ từ CSDL
        hks = HocKyModel.get_all()
        
        # Đổ dữ liệu vào bảng HK
        self.table_hk.setRowCount(0)
        self.cb_ma_hk.clear()
        self.cb_filter_hk.clear()
        self.cb_filter_hp_hk.clear()
        self.cb_filter_hp_hk.addItem("Tất cả Học phần (Mặc định)", "ALL")

        for row_idx, hk in enumerate(hks):
            self.table_hk.insertRow(row_idx)
            self.table_hk.setItem(row_idx, 0, QTableWidgetItem(hk["MaHK"]))
            self.table_hk.setItem(row_idx, 1, QTableWidgetItem(hk["TenHK"]))
            self.table_hk.setItem(row_idx, 2, QTableWidgetItem(hk["NamHoc"]))
            self.table_hk.setItem(row_idx, 3, QTableWidgetItem(hk["NgayMoDangKy"]))
            self.table_hk.setItem(row_idx, 4, QTableWidgetItem(hk["NgayDongDangKy"]))

            # Thêm vào combobox
            self.cb_ma_hk.addItem(f"{hk['MaHK']} - {hk['TenHK']} ({hk['NamHoc']})", hk["MaHK"])
            self.cb_filter_hk.addItem(f"{hk['MaHK']} - {hk['TenHK']}", hk["MaHK"])
            self.cb_filter_hp_hk.addItem(f"{hk['MaHK']} - {hk['TenHK']}", hk["MaHK"])
            
        # Load dữ liệu tab Học phần
        self.load_quan_ly_hoc_phan()
        self.load_schedule_selector()

        # Tải dữ liệu thống kê cho học kỳ đầu tiên
        self.load_thong_ke()

    def load_quan_ly_hoc_phan(self):
        ma_hk = self.cb_filter_hp_hk.currentData()
        hps = AdminModel.get_all_hoc_phan(ma_hk=ma_hk)
        self.table_quan_ly_hp.setRowCount(0)
        for r_idx, hp in enumerate(hps):
            self.table_quan_ly_hp.insertRow(r_idx)
            self.table_quan_ly_hp.setItem(r_idx, 0, QTableWidgetItem(hp["MaHP"]))
            self.table_quan_ly_hp.setItem(r_idx, 1, QTableWidgetItem(hp["TenHP"]))
            self.table_quan_ly_hp.setItem(r_idx, 2, QTableWidgetItem(str(hp["SoTinChi"])))
            self.table_quan_ly_hp.setItem(r_idx, 3, QTableWidgetItem("Có" if hp["BatBuoc"] else "Không"))

    def load_schedule_selector(self):
        self.cb_schedule_lhp.clear()
        for item in AdminModel.get_all_lop_hoc_phan_demo():
            self.cb_schedule_lhp.addItem(f"{item['MaLHP']} | {item['MaHP']} | HK {item['MaHK']}", item['MaLHP'])

    def load_schedule_details(self):
        ma_lhp = self.cb_schedule_lhp.currentData()
        self.table_schedule_details.setRowCount(0)
        if not ma_lhp:
            self.lbl_schedule_status.setText("Chưa chọn lớp học phần.")
            return

        rows = AdminModel.get_chi_tiet_lop_hoc_phan(ma_lhp)
        for row_idx, row in enumerate(rows):
            self.table_schedule_details.insertRow(row_idx)
            self.table_schedule_details.setItem(row_idx, 0, QTableWidgetItem(row.get("MaCTLHP", "")))
            self.table_schedule_details.setItem(row_idx, 1, QTableWidgetItem(row.get("ThuHoc", "")))
            self.table_schedule_details.setItem(row_idx, 2, QTableWidgetItem(row.get("CaHoc", "")))
            self.table_schedule_details.setItem(row_idx, 3, QTableWidgetItem(row.get("PhongHoc", "")))

        self.lbl_schedule_status.setText(f"Đã tải {len(rows)} dòng lịch học cho lớp {ma_lhp}.")

    def on_quan_ly_hp_selected(self):
        items = self.table_quan_ly_hp.selectedItems()
        if not items:
            return
        row = items[0].row()
        self.txt_ma_hp.setText(self.table_quan_ly_hp.item(row, 0).text())
        self.txt_ten_hp.setText(self.table_quan_ly_hp.item(row, 1).text())
        self.spn_tc.setValue(int(self.table_quan_ly_hp.item(row, 2).text()))
        self.chk_bb.setChecked(self.table_quan_ly_hp.item(row, 3).text() == "Có")
        
    def do_them_hp(self):
        ma = self.txt_ma_hp.text().strip()
        ten = self.txt_ten_hp.text().strip()
        tc = self.spn_tc.value()
        bb = self.chk_bb.isChecked()
        if not ma or not ten:
            QMessageBox.warning(self, "Thất bại", "Thiếu thông tin!")
            return
        
        ma_hk_demo = self.cb_filter_hp_hk.currentData()
        ok, msg = AdminModel.them_hoc_phan(ma, ten, tc, bb, ma_hk_demo)
        if ok:
            QMessageBox.information(self, "Thành công", "Thêm thành công!")
            self.load_quan_ly_hoc_phan()
        else:
            QMessageBox.warning(self, "Thất bại", "Thêm thất bại!")

    def do_xoa_hp(self):
        ma = self.txt_ma_hp.text().strip()
        if not ma: return
        reply = QMessageBox.question(self, "Xóa", f"Bạn có chắc muốn xóa {ma}?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            ok, msg = AdminModel.xoa_hoc_phan(ma)
            if ok:
                QMessageBox.information(self, "Thành công", "Xóa thành công!")
                self.load_quan_ly_hoc_phan()
                self.txt_ma_hp.clear(); self.txt_ten_hp.clear()
            else:
                QMessageBox.warning(self, "Thất bại", "Xóa thất bại!")

    def save_schedule_changes(self):
        if self._pending_dirty_schedule_conn is not None:
            QMessageBox.warning(self, "Giao dịch đang chờ", "Có một giao dịch chưa commit đang mở. Vui lòng Commit hoặc Rollback trước khi lưu thay đổi mới.")
            return

        ma_lhp = self.cb_schedule_lhp.currentData()
        if not ma_lhp:
            QMessageBox.warning(self, "Thất bại", "Vui lòng chọn lớp học phần.")
            return

        changes = []
        for row_idx in range(self.table_schedule_details.rowCount()):
            ma_ctlhp = self.table_schedule_details.item(row_idx, 0).text().strip() if self.table_schedule_details.item(row_idx, 0) else ""
            thu_hoc = self.table_schedule_details.item(row_idx, 1).text().strip() if self.table_schedule_details.item(row_idx, 1) else ""
            ca_hoc = self.table_schedule_details.item(row_idx, 2).text().strip() if self.table_schedule_details.item(row_idx, 2) else ""
            phong_hoc = self.table_schedule_details.item(row_idx, 3).text().strip() if self.table_schedule_details.item(row_idx, 3) else ""
            if not ma_ctlhp:
                continue
            changes.append({
                "MaCTLHP": ma_ctlhp,
                "ThuHoc": thu_hoc,
                "CaHoc": ca_hoc,
                "PhongHoc": phong_hoc,
            })

        if not changes:
            QMessageBox.warning(self, "Thất bại", "Không có dòng nào để cập nhật.")
            return

        conn, msg = AdminModel.start_update_chi_tiet_lop_hoc_phan_dirty_read(changes)
        if not conn:
            QMessageBox.critical(self, "Lỗi", msg)
            return

        self._pending_dirty_schedule_conn = conn
        self.btn_commit_schedule.setEnabled(True)
        self.btn_rollback_schedule.setEnabled(True)
        self.lbl_schedule_status.setText(
            "Đã lưu thay đổi vào transaction chưa commit. Sinh viên dùng NOLOCK sẽ thấy dữ liệu này."
        )
        QMessageBox.information(
            self,
            "Lưu tạm thành công",
            "Thay đổi đã được ghi vào transaction chưa commit. Sinh viên sẽ thấy thay đổi khi đọc NOLOCK."
        )

    def commit_schedule_changes(self):
        if not self._pending_dirty_schedule_conn:
            QMessageBox.warning(self, "Không có giao dịch", "Không có giao dịch nào đang mở để commit.")
            return

        try:
            self._pending_dirty_schedule_conn.commit()
            QMessageBox.information(self, "Commit", "Đã commit các thay đổi.")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi khi commit: {e}")
        finally:
            try:
                self._pending_dirty_schedule_conn.close()
            except Exception:
                pass
            self._pending_dirty_schedule_conn = None
            self.btn_commit_schedule.setEnabled(False)
            self.btn_rollback_schedule.setEnabled(False)
            self.lbl_schedule_status.setText("Đã commit thay đổi lịch học.")
            self.load_schedule_details()

    def rollback_schedule_changes(self):
        if not self._pending_dirty_schedule_conn:
            QMessageBox.warning(self, "Không có giao dịch", "Không có giao dịch nào đang mở để rollback.")
            return

        try:
            self._pending_dirty_schedule_conn.rollback()
            QMessageBox.information(self, "Rollback", "Đã rollback các thay đổi.")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi khi rollback: {e}")
        finally:
            try:
                self._pending_dirty_schedule_conn.close()
            except Exception:
                pass
            self._pending_dirty_schedule_conn = None
            self.btn_commit_schedule.setEnabled(False)
            self.btn_rollback_schedule.setEnabled(False)
            self.lbl_schedule_status.setText("Các thay đổi đã bị rollback.")
            self.load_schedule_details()

    def do_update_dirty_read(self):
        ma = self.txt_ma_hp.text().strip()
        ten = self.txt_ten_hp.text().strip()
        tc = self.spn_tc.value()
        bb = self.chk_bb.isChecked()
        if not ma: return

        # Mở Transaction nhưng KHÔNG Commit
        conn, msg = AdminModel.start_update_hoc_phan_dirty_read(ma, ten, tc, bb)
        if not conn:
            QMessageBox.critical(self, "Thất bại", "Lỗi kết nối!")
            return

        # Hiển thị Popup xác nhận. Trong lúc Popup này hiện lên, DB đang bị "Treo" (Dirty)
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Xác nhận Cập nhật ")
        msg_box.setText("Bạn có chắc muốn lưu dữ liệu này vào CSDL không?")
        btn_commit = msg_box.addButton("Lưu ", QMessageBox.YesRole)
        btn_rollback = msg_box.addButton("Hủy ", QMessageBox.NoRole)
        
        msg_box.exec_()

        if msg_box.clickedButton() == btn_commit:
            try:
                conn.commit()
                QMessageBox.information(self, "Thành công", "Cập nhật thành công!")
            except Exception as e:
                pass
        else:
            try:
                conn.rollback()
                QMessageBox.information(self, "Thành công", "Hủy cập nhật thành công!")
            except Exception as e:
                pass
        
        try:
            conn.close()
        except: pass
        self.load_quan_ly_hoc_phan()


    def on_hk_selected(self):
        selected_items = self.table_hk.selectedItems()
        if not selected_items:
            return
        
        row = selected_items[0].row()
        ma_hk = self.table_hk.item(row, 0).text()
        ngay_mo = self.table_hk.item(row, 3).text()
        ngay_dong = self.table_hk.item(row, 4).text()

        # Update combobox
        index = self.cb_ma_hk.findData(ma_hk)
        if index >= 0:
            self.cb_ma_hk.setCurrentIndex(index)
        
        # Update datetime pickers
        if ngay_mo:
            dt1 = QDateTime.fromString(ngay_mo[:19], "yyyy-MM-dd HH:mm:ss")
            if dt1.isValid(): self.dt_mo.setDateTime(dt1)
        if ngay_dong:
            dt2 = QDateTime.fromString(ngay_dong[:19], "yyyy-MM-dd HH:mm:ss")
            if dt2.isValid(): self.dt_dong.setDateTime(dt2)

    def save_thoi_gian_dang_ky(self):
        ma_hk = self.cb_ma_hk.currentData()
        if not ma_hk:
            QMessageBox.warning(self, "Thất bại", "Vui lòng chọn học kỳ!")
            return

        ngay_mo = self.dt_mo.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        ngay_dong = self.dt_dong.dateTime().toString("yyyy-MM-dd HH:mm:ss")

        if self.dt_mo.dateTime() >= self.dt_dong.dateTime():
            QMessageBox.warning(self, "Thất bại", "Ngày đóng phải sau ngày mở!")
            return

        ok, msg = AdminModel.set_thoi_gian_dang_ky(ma_hk, ngay_mo, ngay_dong)
        if ok:
            QMessageBox.information(self, "Thành công", "Lưu thành công!")
            self.load_data() # Refresh table
        else:
            QMessageBox.critical(self, "Thất bại", "Lưu thất bại!")

    def do_deadlock_admin(self):
        ma_hk = self.cb_ma_hk.currentData()
        if not ma_hk:
            QMessageBox.warning(self, "Thất bại", "Vui lòng chọn học kỳ!")
            return

        selected_items = self.table_hk.selectedItems()
        row = None
        if selected_items:
            row = selected_items[0].row()
        else:
            for r in range(self.table_hk.rowCount()):
                if self.table_hk.item(r, 0).text() == ma_hk:
                    row = r
                    break

        if row is None:
            QMessageBox.warning(self, "Thất bại", "Vui lòng chọn học kỳ trong bảng trước khi demo Deadlock.")
            return

        ten_hk = self.table_hk.item(row, 1).text()
        nam_hoc_text = self.table_hk.item(row, 2).text()
        try:
            nam_hoc = int(nam_hoc_text)
        except ValueError:
            nam_hoc = 0
        ngay_mo = self.table_hk.item(row, 3).text()
        ngay_dong = self.table_hk.item(row, 4).text()

        ok, msg = AdminModel.demo_deadlock_admin(ma_hk, ten_hk, nam_hoc, ngay_mo, ngay_dong)
        if ok:
            QMessageBox.information(self, "Thành công", "Đã khởi tạo Deadlock demo phía Nhà trường.")
        else:
            QMessageBox.critical(self, "Thất bại", f"Thất bại:\n{msg}")

    def load_thong_ke(self, index=None):
        try:
            text = self.cb_filter_hk.currentText()
            if not text:
                return
            ma_hk = text.split(" - ")[0].strip()
            print(f"load_thong_ke called. ma_hk={ma_hk}")

            data = AdminModel.get_lop_hoc_phan(ma_hk)
            print(f"Fetched {len(data)} items for ma_hk={ma_hk}")
            
            self.table_tk.setRowCount(0)

            for row_idx, item in enumerate(data):
                self.table_tk.insertRow(row_idx)
                self.table_tk.setItem(row_idx, 0, QTableWidgetItem(str(item.get("MaLHP", ""))))
                self.table_tk.setItem(row_idx, 1, QTableWidgetItem(str(item.get("MaHP", ""))))
                self.table_tk.setItem(row_idx, 2, QTableWidgetItem(str(item.get("TenHP", ""))))
                
                siso = QTableWidgetItem(str(item.get("SiSoToiDa", 0)))
                siso.setTextAlignment(Qt.AlignCenter)
                self.table_tk.setItem(row_idx, 3, siso)

                dadk = QTableWidgetItem(str(item.get("SoLuongDangKy", 0)))
                dadk.setTextAlignment(Qt.AlignCenter)
                self.table_tk.setItem(row_idx, 4, dadk)

                controng = QTableWidgetItem(str(item.get("SoChoConLai", 0)))
                controng.setTextAlignment(Qt.AlignCenter)
                self.table_tk.setItem(row_idx, 5, controng)

                tyle = QTableWidgetItem(f"{item.get('PhanTramDaDangKy', 0):.1f}%")
                tyle.setTextAlignment(Qt.AlignCenter)
                self.table_tk.setItem(row_idx, 6, tyle)
                
            print(f"table_tk rowCount is now {self.table_tk.rowCount()}")

            # Cập nhật timestamp (Phantom Read awareness)
            
            self.lbl_tk_timestamp.setText(f"📊 Số liệu cập nhật lúc: {_dt.now().strftime('%H:%M:%S')} | Lưu ý: số liệu có thể thay đổi khi SV đăng ký đồng thời")
        except Exception as e:
            traceback.print_exc()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SchoolWindow()
    window.show()
    sys.exit(app.exec_())
