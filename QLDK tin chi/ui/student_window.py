import sys
import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QSplitter, QMessageBox, QGroupBox,
    QApplication, QAbstractItemView, QFrame, QSizePolicy,
    QTabWidget, QStackedWidget
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models.sinh_vien import SinhVien
from models.method import HocKyModel
from concurrency.transaction_handler import execute_with_retry


def _is_within_registration_period(ma_hk: str) -> tuple[bool, str]:
    """
    Kiểm tra thời gian đăng ký của học kỳ.
    Trả về (is_open, status_message).
    """
    hk = HocKyModel.get_by_id(ma_hk)
    if not hk:
        return False, "Không tìm thấy học kỳ."
    
    ngay_mo_str = hk.get("NgayMoDangKy", "")
    ngay_dong_str = hk.get("NgayDongDangKy", "")
    
    if not ngay_mo_str or not ngay_dong_str:
        return False, "⛔ Nhà trường chưa thiết lập thời gian đăng ký cho học kỳ này."
    
    try:
        ngay_mo   = datetime.strptime(ngay_mo_str[:19], "%Y-%m-%d %H:%M:%S")
        ngay_dong = datetime.strptime(ngay_dong_str[:19], "%Y-%m-%d %H:%M:%S")
        now       = datetime.now()
        
        if now < ngay_mo:
            return False, f"⛔ Chưa đến thời gian đăng ký. Mở từ: {ngay_mo.strftime('%d/%m/%Y %H:%M')}"
        if now > ngay_dong:
            return False, f"⛔ Đã hết hạn đăng ký. Đóng lúc: {ngay_dong.strftime('%d/%m/%Y %H:%M')}"
        
        return True, f"✅ Đang trong đợt đăng ký. Đóng lúc: {ngay_dong.strftime('%d/%m/%Y %H:%M')}"
    except ValueError:
        return False, "Lỗi định dạng thời gian."


class StudentWindow(QWidget):
    def __init__(self, ma_sv: str):
        super().__init__()
        self.sv = SinhVien.get_by_id(ma_sv)
        if not self.sv:
            QMessageBox.critical(None, "Lỗi", f"Không tìm thấy sinh viên: {ma_sv}")
            sys.exit(1)
        
        self.setWindowTitle(f"Đăng ký Học phần – {self.sv.ho_ten} ({self.sv.ma_sv})")
        self.resize(1200, 800)
        self._selected_lhp = None   # MaLHP đang được chọn ở Bảng 2
        self.setup_ui()
        self.load_hoc_ky()

    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        root.addWidget(self._build_header())
        root.addWidget(self._build_status_bar())

        # Main Tab Widget
        self.main_tabs = QTabWidget()
        root.addWidget(self.main_tabs)

        # Tab 1: Học mới (The main registration UI)
        self.tab_hoc_moi = QWidget()
        layout_moi = QVBoxLayout(self.tab_hoc_moi)
        layout_moi.setContentsMargins(0, 10, 0, 0)
        
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.addWidget(self._build_top_panel())   # Bảng 1 + Bảng 2 + Bảng 3
        self.splitter.addWidget(self._build_bottom_panel()) # Bảng 4
        self.splitter.setSizes([520, 240])
        layout_moi.addWidget(self.splitter)
        
        self.main_tabs.addTab(self.tab_hoc_moi, "Đăng ký Học mới")

        # Tab 2: Học cải thiện
        self.tab_cai_thien = self._build_updating_tab("Học cải thiện")
        self.main_tabs.addTab(self.tab_cai_thien, "Học cải thiện")

        # Tab 3: Học lại
        self.tab_hoc_lai = self._build_updating_tab("Học lại")
        self.main_tabs.addTab(self.tab_hoc_lai, "Học lại")

    def _build_updating_tab(self, name: str) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        lbl = QLabel(f"<b>Chức năng {name} đang trong quá trình cập nhật...</b>")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("font-size: 18px; color: #666;")
        v.addWidget(lbl)
        return w

    # Header
    def _build_header(self) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)

        lbl = QLabel(f"<b>ĐĂNG KÝ HỌC PHẦN</b>")
        lbl.setFont(QFont("Arial", 16))

        h.addWidget(lbl)
        h.addStretch()

        h.addWidget(QLabel("Học kỳ:"))
        self.cb_hk = QComboBox()
        self.cb_hk.setMinimumWidth(220)
        self.cb_hk.currentIndexChanged.connect(self._on_hk_changed)
        h.addWidget(self.cb_hk)

        h.addStretch()
        return w

    # Status Bar
    def _build_status_bar(self) -> QLabel:
        self.lbl_status = QLabel("Vui lòng chọn học kỳ...")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setMinimumHeight(30)
        self.lbl_status.setStyleSheet(
            "background-color: #f5f5f5; border: 1px solid #ddd; "
            "border-radius: 4px; padding: 4px; font-size: 13px;"
        )
        return self.lbl_status

    # Top Panel (Bảng 1 | Bảng 2+3)
    def _build_top_panel(self) -> QSplitter:
        sp = QSplitter(Qt.Horizontal)

        # Bảng 1 – Học phần
        left = QGroupBox("Bảng 1 – Học phần có thể đăng ký")
        lv = QVBoxLayout(left)

        self.table_hp = QTableWidget()
        self.table_hp.setColumnCount(5)
        self.table_hp.setHorizontalHeaderLabels(["Mã HP", "Tên Môn Học", "TC", "BB", "Điều kiện ĐK"])
        self.table_hp.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_hp.horizontalHeader().setStretchLastSection(True)
        self.table_hp.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_hp.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_hp.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table_hp.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table_hp.itemSelectionChanged.connect(self._on_hp_selected)
        lv.addWidget(self.table_hp)
        sp.addWidget(left)

        # Bảng 2 + Bảng 3 + nút Đăng ký
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)

        sp_inner = QSplitter(Qt.Horizontal)

        # Bảng 2 – Lớp HP
        gb2 = QGroupBox("Bảng 2 – Lớp học phần")
        v2 = QVBoxLayout(gb2)

        # Toolbar Bảng 2: nút Làm mới + checkbox lọc trùng lịch
        toolbar2 = QHBoxLayout()
        self.btn_lam_moi_b2 = QPushButton("🔄 Làm mới dữ liệu")
        self.btn_lam_moi_b2.setFixedWidth(130)
        self.btn_lam_moi_b2.setToolTip(
            "Nhấn để tải lại toàn bộ thông tin Môn học và Sĩ số mới nhất từ CSDL"
        )
        self.btn_lam_moi_b2.clicked.connect(self._refresh_data)
        toolbar2.addWidget(self.btn_lam_moi_b2)

        self.btn_reload_chi_tiet = QPushButton("🔄 Reload lịch chi tiết")
        self.btn_reload_chi_tiet.setFixedWidth(150)
        self.btn_reload_chi_tiet.setToolTip(
            "Chỉ tải lại Danh sách Lớp HP và Chi tiết lịch của lớp đang chọn, tránh chậm khi có Dirty Read."
        )
        self.btn_reload_chi_tiet.clicked.connect(self._refresh_selected_schedule)
        toolbar2.addWidget(self.btn_reload_chi_tiet)

        self.chk_loc_trung = QCheckBox("ỌLọc trùng lịch")
        self.chk_loc_trung.setChecked(True)
        self.chk_loc_trung.setStyleSheet("font-weight: bold; color: #d35400; font-size: 13px;")
        self.chk_loc_trung.stateChanged.connect(self._on_hp_selected)
        toolbar2.addWidget(self.chk_loc_trung)
        toolbar2.addStretch()
        v2.addLayout(toolbar2)

        self.table_lhp = QTableWidget()
        self.table_lhp.setColumnCount(4)
        self.table_lhp.setHorizontalHeaderLabels(["Mã Lớp HP", "SL ĐK", "Sĩ Số", "%"])
        self.table_lhp.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_lhp.horizontalHeader().setStretchLastSection(True)
        self.table_lhp.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_lhp.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_lhp.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table_lhp.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table_lhp.itemSelectionChanged.connect(self._on_lhp_selected)
        v2.addWidget(self.table_lhp)

        # Label timestamp (Dirty Read / Non-Repeatable Read)
        self.lbl_b2_timestamp = QLabel("")
        self.lbl_b2_timestamp.setStyleSheet("color: #888; font-size: 11px;")
        self.lbl_b2_timestamp.setAlignment(Qt.AlignRight)
        v2.addWidget(self.lbl_b2_timestamp)

        sp_inner.addWidget(gb2)

        # Bảng 3 – Chi tiết lịch học
        gb3 = QGroupBox("Bảng 3 – Chi tiết lịch học")
        v3 = QVBoxLayout(gb3)
        self.table_lich = QTableWidget()
        self.table_lich.setColumnCount(4)
        self.table_lich.setHorizontalHeaderLabels(["Thứ", "Ca học", "Phòng", "Ngày bắt đầu"])
        self.table_lich.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_lich.horizontalHeader().setStretchLastSection(True)
        self.table_lich.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_lich.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_lich.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table_lich.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        v3.addWidget(self.table_lich)
        sp_inner.addWidget(gb3)

        rv.addWidget(sp_inner)

        # Nút ĐĂNG KÝ
        self.btn_dang_ky = QPushButton("✅  ĐĂNG KÝ")
        self.btn_dang_ky.setMinimumHeight(44)
        self.btn_dang_ky.setFont(QFont("Arial", 12, QFont.Bold))
        self.btn_dang_ky.setStyleSheet(
            "QPushButton { background-color: #2e8b57; color: white; border-radius: 6px; }"
            "QPushButton:disabled { background-color: #aaa; color: #eee; }"
            "QPushButton:hover:enabled { background-color: #246b43; }"
        )
        self.btn_dang_ky.setEnabled(False)
        self.btn_dang_ky.clicked.connect(self._do_dang_ky)
        rv.addWidget(self.btn_dang_ky)

        # Nút Demo Deadlock SV
        self.btn_deadlock_demo = QPushButton("Demo Deadlock SV")
        self.btn_deadlock_demo.setMinimumHeight(44)
        self.btn_deadlock_demo.setFont(QFont("Arial", 11, QFont.Bold))
        self.btn_deadlock_demo.setStyleSheet(
            "QPushButton { background-color: #d9534f; color: white; border-radius: 6px; }"
            "QPushButton:disabled { background-color: #aaa; color: #eee; }"
            "QPushButton:hover:enabled { background-color: #c9302c; }"
        )
        self.btn_deadlock_demo.setEnabled(False)
        self.btn_deadlock_demo.clicked.connect(self._do_demo_deadlock)
        self.btn_deadlock_demo.setToolTip("Kích hoạt stored procedure demo Deadlock sinh viên.")
        rv.addWidget(self.btn_deadlock_demo)

        sp.addWidget(right)
        sp.setSizes([380, 620])
        return sp


    # Bottom Panel (Bảng 4)
    def _build_bottom_panel(self) -> QGroupBox:
        gb = QGroupBox("Bảng 4 – Học phần đã đăng ký trong học kỳ này")
        v = QVBoxLayout(gb)

        self.table_da_dk = QTableWidget()
        self.table_da_dk.setColumnCount(7)
        self.table_da_dk.setHorizontalHeaderLabels(
            ["Thao tác", "Mã Lớp HP", "Mã HP", "Tên Môn Học", "TC", "Trạng thái", "Loại ĐK"]
        )
        self.table_da_dk.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_da_dk.horizontalHeader().setStretchLastSection(True)
        self.table_da_dk.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_da_dk.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table_da_dk.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Dòng Tổng tín chỉ
        self.lbl_tong_tc = QLabel("Tổng tín chỉ đã đăng ký: 0 TC")
        self.lbl_tong_tc.setAlignment(Qt.AlignRight)
        self.lbl_tong_tc.setStyleSheet("font-weight: bold; padding-right: 8px;")

        v.addWidget(self.table_da_dk)
        v.addWidget(self.lbl_tong_tc)
        return gb

    def load_hoc_ky(self):
        """Nạp danh sách học kỳ vào ComboBox."""
        hks = SinhVien.get_danh_sach_hoc_ky()
        self.cb_hk.blockSignals(True)
        self.cb_hk.clear()
        for hk in hks:
            label = f"{hk['MaHK']} – {hk['TenHK']} ({hk['NamHoc']})"
            self.cb_hk.addItem(label, hk["MaHK"])
        self.cb_hk.blockSignals(False)
        if self.cb_hk.count() > 0:
            self._on_hk_changed()

    def _get_current_ma_hk(self) -> str | None:
        text = self.cb_hk.currentText()
        if not text:
            return None
        return text.split(" – ")[0].strip()

    def _on_hk_changed(self, *_):
        """Khi đổi học kỳ: kiểm tra đợt ĐK, refresh bảng 1 + bảng 4."""
        ma_hk = self._get_current_ma_hk()
        if not ma_hk:
            return

        is_open, status_msg = _is_within_registration_period(ma_hk)
        self._set_status(is_open, status_msg)
        self._load_bang1()
        self._load_bang4()

    def _set_status(self, is_open: bool, msg: str):
        """Cập nhật thanh trạng thái và bật/tắt nút đăng ký."""
        self.lbl_status.setText(msg)
        color = "#d4edda" if is_open else "#f8d7da"
        border = "#28a745" if is_open else "#dc3545"
        self.lbl_status.setStyleSheet(
            f"background-color: {color}; border: 1px solid {border}; "
            "border-radius: 4px; padding: 4px; font-size: 13px;"
        )
        # Nút ĐĂNG KÝ chỉ enable khi trong đợt ĐK VÀ đã chọn lớp
        self._reg_period_open = is_open
        self._update_dang_ky_btn()

    def _update_dang_ky_btn(self):
        """Bật nút chỉ khi (đang trong đợt ĐK) VÀ (đã chọn lớp HP)."""
        ok = getattr(self, "_reg_period_open", False) and self._selected_lhp is not None
        self.btn_dang_ky.setEnabled(ok)
        if hasattr(self, 'btn_deadlock_demo'):
            self.btn_deadlock_demo.setEnabled(ok)

    def _load_bang1(self, *_):
        """Tải Bảng 1 – Danh sách học phần SV có thể đăng ký."""
        ma_hk = self._get_current_ma_hk()
        self.table_hp.setRowCount(0)
        self.table_lhp.setRowCount(0)
        self.table_lich.setRowCount(0)
        self._selected_lhp = None
        self._update_dang_ky_btn()

        if not ma_hk:
            return

        ds = self.sv.get_hoc_phan_co_the_dang_ky(ma_hk)
        
        # NOTE: Ẩn học phần đã đăng ký thành công (Trạng thái KHÔNG chứa chữ 'Huy')
        da_dk = self.sv.get_danh_sach_da_dang_ky(ma_hk)
        ma_hp_da_dk = [d["MaHP"] for d in da_dk if "Huy" not in (d["TrangThai"] or "")]

        row_idx = 0
        for hp in ds:
            if hp["MaHP"] in ma_hp_da_dk:
                continue
                
            self.table_hp.insertRow(row_idx)
            self.table_hp.setItem(row_idx, 0, QTableWidgetItem(hp["MaHP"]))
            self.table_hp.setItem(row_idx, 1, QTableWidgetItem(hp["TenHP"]))

            tc = QTableWidgetItem(str(hp["SoTinChi"]))
            tc.setTextAlignment(Qt.AlignCenter)
            self.table_hp.setItem(row_idx, 2, tc)

            bb = QTableWidgetItem("✅" if hp["BatBuoc"] else "")
            bb.setTextAlignment(Qt.AlignCenter)
            self.table_hp.setItem(row_idx, 3, bb)

            dk = hp.get("DieuKienDangKy", "") or ""
            self.table_hp.setItem(row_idx, 4, QTableWidgetItem(dk))

            # Tô màu đỏ nhạt nếu chưa đủ điều kiện
            if not hp.get("DatTienQuyet", True) or not hp.get("DatSongHanh", True):
                for c in range(5):
                    item = self.table_hp.item(row_idx, c)
                    if item:
                        item.setBackground(QColor("#ffe0e0"))
            
            row_idx += 1

    def _on_hp_selected(self):
        """Khi SV click chọn 1 học phần → nạp Bảng 2."""
        self.table_lhp.setRowCount(0)
        self.table_lich.setRowCount(0)
        self._selected_lhp = None
        self._update_dang_ky_btn()

        items = self.table_hp.selectedItems()
        if not items:
            return
        row = items[0].row()
        ma_hp = self.table_hp.item(row, 0).text()
        ma_hk = self._get_current_ma_hk()
        if not ma_hp or not ma_hk:
            return

        lops = SinhVien.get_lop_hoc_phan(ma_hp, ma_hk)
        r_idx = 0
        for lop in lops:
            # NOTE: Lọc trùng lịch (nếu checkbox được tích)
            if self.chk_loc_trung.isChecked():
                if self.sv.kiem_tra_trung_lich(lop["MaLHP"]):
                    continue

            self.table_lhp.insertRow(r_idx)
            self.table_lhp.setItem(r_idx, 0, QTableWidgetItem(lop["MaLHP"]))

            sl = QTableWidgetItem(str(lop["SoLuongDangKy"]))
            sl.setTextAlignment(Qt.AlignCenter)
            self.table_lhp.setItem(r_idx, 1, sl)

            ss = QTableWidgetItem(str(lop["SiSoToiDa"]))
            ss.setTextAlignment(Qt.AlignCenter)
            self.table_lhp.setItem(r_idx, 2, ss)

            pct = QTableWidgetItem(f"{lop['PhanTramDaDangKy']:.0f}%")
            pct.setTextAlignment(Qt.AlignCenter)
            self.table_lhp.setItem(r_idx, 3, pct)

            # Tô đỏ nếu đầy
            if lop["SoChoConLai"] <= 0:
                for c in range(4):
                    item = self.table_lhp.item(r_idx, c)
                    if item:
                        item.setBackground(QColor("#ffe0e0"))
            
            r_idx += 1

        # Cập nhật timestamp (Dirty Read / Non-Repeatable Read awareness)

        self.lbl_b2_timestamp.setText(f"Cập nhật lúc: {datetime.now().strftime('%H:%M:%S')}")

    def _on_lhp_selected(self):
        """Khi SV click chọn 1 lớp HP → nạp Bảng 3 và cập nhật trạng thái nút ĐK."""
        self.table_lich.setRowCount(0)
        self._selected_lhp = None
        self._update_dang_ky_btn()

        items = self.table_lhp.selectedItems()
        if not items:
            return
        row = items[0].row()
        ma_lhp = self.table_lhp.item(row, 0).text()

        liches = SinhVien.get_lich_lop(ma_lhp)
        for r_idx, lich in enumerate(liches):
            self.table_lich.insertRow(r_idx)
            self.table_lich.setItem(r_idx, 0, QTableWidgetItem(lich["Thu"]))
            self.table_lich.setItem(r_idx, 1, QTableWidgetItem(lich["Cahoc"]))
            self.table_lich.setItem(r_idx, 2, QTableWidgetItem(lich["PhongHoc"]))
            self.table_lich.setItem(r_idx, 3, QTableWidgetItem(lich["NgayBatDau"][:10]))

        self._selected_lhp = ma_lhp
        self._update_dang_ky_btn()

    def _load_bang4(self):
        """Tải Bảng 4 – Danh sách đã đăng ký (chỉ hiện các dòng CHƯA bị hủy)."""
        self.table_da_dk.setRowCount(0)
        ma_hk = self._get_current_ma_hk()
        if not ma_hk:
            return

        ds = self.sv.get_danh_sach_da_dang_ky(ma_hk)
        tong_tc = 0
        display_row = 0   # ← Đếm riêng hàng thực tế trên bảng (không lẫn hàng bị skip)

        for dk in ds:
            status = dk.get("TrangThai") or ""
            if "Huy" in status:
                continue   # Bỏ qua hàng đã hủy, KHÔNG tăng display_row

            self.table_da_dk.insertRow(display_row)

            # Nút HỦY ĐK
            btn_huy = QPushButton("Hủy ĐK")
            btn_huy.setStyleSheet(
                "QPushButton { background-color: #dc3545; color: white; border-radius: 4px; padding: 2px 8px;}"
                "QPushButton:hover { background-color: #a71d2a; }"
            )
            ma_dk = dk["MaDK"]
            btn_huy.clicked.connect(lambda _, mid=ma_dk: self._do_huy_dang_ky(mid))
            self.table_da_dk.setCellWidget(display_row, 0, btn_huy)

            self.table_da_dk.setItem(display_row, 1, QTableWidgetItem(dk["MaLHP"]))
            self.table_da_dk.setItem(display_row, 2, QTableWidgetItem(dk["MaHP"]))
            self.table_da_dk.setItem(display_row, 3, QTableWidgetItem(dk["TenHP"]))

            tc_item = QTableWidgetItem(str(dk["SoTinChi"]))
            tc_item.setTextAlignment(Qt.AlignCenter)
            self.table_da_dk.setItem(display_row, 4, tc_item)

            self.table_da_dk.setItem(display_row, 5, QTableWidgetItem(status))
            self.table_da_dk.setItem(display_row, 6, QTableWidgetItem(dk["LoaiDangKy"]))

            tong_tc += dk["SoTinChi"]
            display_row += 1   # ← Chỉ tăng khi thực sự thêm hàng

        self.lbl_tong_tc.setText(f"Tổng tín chỉ đã đăng ký: {tong_tc} TC")

   
    def _get_loai_dk(self) -> str:
        tab_idx = self.main_tabs.currentIndex()
        if tab_idx == 1: return "Học cải thiện"
        if tab_idx == 2: return "Học lại"
        return "Mới"

    def _refresh_data(self):
        """Làm mới toàn bộ Bảng 1 và Bảng 2, giữ nguyên môn và lớp HP đang chọn nếu có."""
        selected_ma_hp = None
        selected_ma_lhp = None

        items_hp = self.table_hp.selectedItems()
        if items_hp:
            selected_ma_hp = self.table_hp.item(items_hp[0].row(), 0).text()

        items_lhp = self.table_lhp.selectedItems()
        if items_lhp:
            selected_ma_lhp = self.table_lhp.item(items_lhp[0].row(), 0).text()

        # Tải lại Bảng 1 (sẽ tự clear Bảng 2 và Bảng 3)
        self._load_bang1()

        # Chọn lại môn cũ và nếu có thì chọn lại lớp HP cũ để hiện lịch chi tiết
        if selected_ma_hp:
            for r in range(self.table_hp.rowCount()):
                if self.table_hp.item(r, 0).text() == selected_ma_hp:
                    self.table_hp.selectRow(r)
                    break

        if selected_ma_lhp:
            found = False
            for r in range(self.table_lhp.rowCount()):
                if self.table_lhp.item(r, 0).text() == selected_ma_lhp:
                    self.table_lhp.selectRow(r)
                    found = True
                    break
            if not found:
                # Nếu lớp cũ không còn trong danh sách, chỉ giữ nguyên môn học
                self.table_lich.setRowCount(0)

    def _refresh_selected_schedule(self):
        """Chỉ reload lại danh sách lớp HP và lịch chi tiết của lớp đang chọn."""
        if not self._selected_lhp:
            QMessageBox.information(self, "Thông báo", "Vui lòng chọn một lớp HP trước khi reload lịch chi tiết.")
            return

        # Nạp lại danh sách lớp của môn hiện tại
        items_hp = self.table_hp.selectedItems()
        if not items_hp:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn lại học phần (Môn học) để tải dữ liệu.")
            return

        ma_hp = self.table_hp.item(items_hp[0].row(), 0).text()
        ma_hk = self._get_current_ma_hk()
        if not ma_hk:
            return

        self.table_lhp.setRowCount(0)
        lops = SinhVien.get_lop_hoc_phan(ma_hp, ma_hk)

        selected_ma_lhp = self._selected_lhp
        for r_idx, lop in enumerate(lops):
            self.table_lhp.insertRow(r_idx)
            self.table_lhp.setItem(r_idx, 0, QTableWidgetItem(lop["MaLHP"]))

            sl = QTableWidgetItem(str(lop["SoLuongDangKy"]))
            sl.setTextAlignment(Qt.AlignCenter)
            self.table_lhp.setItem(r_idx, 1, sl)

            ss = QTableWidgetItem(str(lop["SiSoToiDa"]))
            ss.setTextAlignment(Qt.AlignCenter)
            self.table_lhp.setItem(r_idx, 2, ss)

            pct = QTableWidgetItem(f"{lop['PhanTramDaDangKy']:.0f}%")
            pct.setTextAlignment(Qt.AlignCenter)
            self.table_lhp.setItem(r_idx, 3, pct)

            if lop["SoChoConLai"] <= 0:
                for c in range(4):
                    item = self.table_lhp.item(r_idx, c)
                    if item:
                        item.setBackground(QColor("#ffe0e0"))

            if lop["MaLHP"] == selected_ma_lhp:
                self.table_lhp.selectRow(r_idx)

        self.lbl_b2_timestamp.setText(f"Cập nhật lúc: {datetime.now().strftime('%H:%M:%S')}")

    def _do_dang_ky(self):
        """Ấc lý click nút ĐĂNG KÝ – có retry Deadlock và phân loại thông báo lỗi."""
        if not self._selected_lhp:
            return

        # Kiểm tra lại đợt đăng ký (có thể vừa hết hạn)
        ma_hk = self._get_current_ma_hk()
        is_open, msg = _is_within_registration_period(ma_hk)
        self._set_status(is_open, msg)
        if not is_open:
            QMessageBox.warning(self, "Thất bại", "Ngoài đợt đăng ký!")
            return

        loai_dk = self._get_loai_dk()
        ma_lhp  = self._selected_lhp

        # on_retry callback → cập nhật status bar mỗi lần retry (Deadlock)
        def _on_retry(attempt, max_r):
            self.lbl_status.setText(f"⏳ Hệ thống đang bận. Đang thử lại lần {attempt}/{max_r}...")
            QApplication.processEvents()

        def _attempt():
            ok, msg_ = self.sv.dang_ky_lop(ma_lhp, loai_dk, max_retries=1)
            return ok, msg_, None

        ok, result_msg, _ = execute_with_retry(
            _attempt, max_retries=3, delay_sec=1.0, on_retry=_on_retry
        )

        if ok:
            QMessageBox.information(self, "Thành công", "Đăng ký thành công!")
            self._load_bang1()    # Ẩn HP khỏi Bảng 1
            self._load_bang4()    # Cập nhật Bảng 4
            self._on_hp_selected()  # Refresh Bảng 2 (cập nhật sĩ số mới)
        else:
            # Phân loại thông báo theo loại lỗi:
            if "hết chỗ" in result_msg.lower() or "sĩ số" in result_msg.lower():
                QMessageBox.warning(self, "Thất bại", "Lớp đã đầy!")
                self._on_hp_selected()   # Auto-refresh Bảng 2 (Non-Repeatable Read)
            elif "trùng lịch" in result_msg.lower():
                QMessageBox.warning(self, "Thất bại", "Trùng lịch học!")
            elif "tiên quyết" in result_msg.lower():
                QMessageBox.warning(self, "Thất bại", "Thiếu điều kiện!")
            elif "tín chỉ" in result_msg.lower():
                QMessageBox.warning(self, "Thất bại", "Vượt tín chỉ!")
            elif "quá tải" in result_msg.lower() or "deadlock" in result_msg.lower():
                QMessageBox.critical(self, "Thất bại", "Xung đột hệ thống!")
            else:
                QMessageBox.warning(self, "Thất bại", "Đăng ký thất bại!")

    def _do_demo_deadlock(self):
        if not self._selected_lhp:
            return

        ma_hk = self._get_current_ma_hk()
        ma_lhp = self._selected_lhp
        ok, msg = self.sv.demo_deadlock_sinhvien(ma_lhp, ma_hk)
        if ok:
            QMessageBox.information(self, "Thành công", "Đã gọi stored procedure Deadlock SV. Nếu Admin đang chạy demo, có thể xảy ra deadlock.")
            self._load_bang1()
            self._load_bang4()
            self._on_hp_selected()
        else:
            QMessageBox.critical(self, "Lỗi Deadlock", msg)

        is_open2, msg2 = _is_within_registration_period(ma_hk)
        self._set_status(is_open2, msg2)

    def _do_huy_dang_ky(self, ma_dk: str):
        """Xử lý click nút HỦY ĐK."""
        reply = QMessageBox.question(
            self, "Xác nhận hủy",
            f"Bạn có chắc muốn hủy đăng ký?\nMã ĐK: {ma_dk}",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        ok, msg = self.sv.huy_dang_ky(ma_dk)
        if ok:
            QMessageBox.information(self, "Thành công", "Hủy thành công!")
            self._load_bang1()
            self._load_bang4()
        else:
            QMessageBox.warning(self, "Thất bại", "Hủy thất bại!")



