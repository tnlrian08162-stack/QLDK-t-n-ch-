import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database.connection import execute_query, execute_procedure


class HocKyModel:

    @staticmethod
    def get_all() -> list[dict]:
        """Lấy toàn bộ danh sách học kỳ, sắp theo NamHoc mới nhất."""
        rows = execute_query(
            "SELECT MaHK, TenHK, NamHoc, NgayMoDangKy, NgayDongDangKy FROM HocKy ORDER BY NamHoc DESC, MaHK DESC"
        )
        return [
            {
                "MaHK": r.MaHK, 
                "TenHK": r.TenHK, 
                "NamHoc": r.NamHoc,
                "NgayMoDangKy": str(r.NgayMoDangKy) if r.NgayMoDangKy else "",
                "NgayDongDangKy": str(r.NgayDongDangKy) if r.NgayDongDangKy else ""
            }
            for r in rows
        ]

    @staticmethod
    def get_by_id(ma_hk: str) -> dict | None:
        """Lấy thông tin 1 học kỳ theo mã."""
        rows = execute_query(
            "SELECT MaHK, TenHK, NamHoc, NgayMoDangKy, NgayDongDangKy FROM HocKy WHERE MaHK = ?", (ma_hk,)
        )
        if rows:
            r = rows[0]
            return {
                "MaHK": r.MaHK, 
                "TenHK": r.TenHK, 
                "NamHoc": r.NamHoc,
                "NgayMoDangKy": str(r.NgayMoDangKy) if r.NgayMoDangKy else "",
                "NgayDongDangKy": str(r.NgayDongDangKy) if r.NgayDongDangKy else ""
            }
        return None

    @staticmethod
    def create(ma_hk: str, ten_hk: str, nam_hoc: str) -> tuple[bool, str]:
        """Thêm học kỳ mới. Trả về (success, message)."""
        if HocKyModel.get_by_id(ma_hk):
            return False, f"Mã học kỳ '{ma_hk}' đã tồn tại."
        execute_query(
            "INSERT INTO HocKy (MaHK, TenHK, NamHoc, NgayMoDangKy, NgayDongDangKy) VALUES (?, ?, ?, GETDATE(), DATEADD(DAY, 1, GETDATE()))",
            (ma_hk, ten_hk, nam_hoc),
            fetch=False,
        )
        return True, "Thêm học kỳ thành công."

    @staticmethod
    def update(ma_hk: str, ten_hk: str = None, nam_hoc: str = None) -> tuple[bool, str]:
        """Cập nhật thông tin học kỳ. Trả về (success, message)."""
        if not HocKyModel.get_by_id(ma_hk):
            return False, f"Không tìm thấy học kỳ '{ma_hk}'."
        sets, params = [], []
        if ten_hk is not None:
            sets.append("TenHK = ?"); params.append(ten_hk)
        if nam_hoc is not None:
            sets.append("NamHoc = ?"); params.append(nam_hoc)
        if not sets:
            return False, "Không có thông tin để cập nhật."
        params.append(ma_hk)
        execute_query(f"UPDATE HocKy SET {', '.join(sets)} WHERE MaHK = ?", tuple(params), fetch=False)
        return True, "Cập nhật học kỳ thành công."

    @staticmethod
    def delete(ma_hk: str) -> tuple[bool, str]:
        """Xóa học kỳ. Thất bại nếu HK đang có lớp HP liên kết."""
        if not HocKyModel.get_by_id(ma_hk):
            return False, f"Không tìm thấy học kỳ '{ma_hk}'."
        refs = execute_query("SELECT COUNT(*) AS cnt FROM LopHocPhan WHERE MaHK = ?", (ma_hk,))
        if refs and refs[0].cnt > 0:
            return False, f"Không thể xóa: học kỳ '{ma_hk}' đang có {refs[0].cnt} lớp HP."
        execute_query("DELETE FROM HocKy WHERE MaHK = ?", (ma_hk,), fetch=False)
        return True, "Xóa học kỳ thành công."



class HocPhanModel:

    @staticmethod
    def get_all() -> list[dict]:
        """Lấy toàn bộ danh sách học phần."""
        rows = execute_query(
            "SELECT MaHP, TenHP, SoTinChi, BatBuoc FROM HocPhan ORDER BY MaHP"
        )
        return [
            {
                "MaHP": r.MaHP,
                "TenHP": r.TenHP,
                "SoTinChi": r.SoTinChi,
                "BatBuoc": bool(r.BatBuoc),
            }
            for r in rows
        ]

    @staticmethod
    def get_cho_dang_ky(ma_sv: str, ma_hk: str) -> list[dict]:
        """
        Lấy danh sách Học Phần sinh viên có thể đăng ký trong HK.
        Tự kiểm tra điều kiện Tiên Quyết & Song Hành qua scalar function của DB.

        Returns: list[{
            "MaHP", "TenHP", "SoTinChi", "BatBuoc",
            "DieuKienDangKy", "TienQuyet", "SongHanh",
            "DatTienQuyet": bool, "DatSongHanh": bool
        }]
        """
        rows = execute_query(
            "SELECT HP.MaHP, HP.TenHP, HP.SoTinChi, HP.BatBuoc, "
            "'' AS DieuKienDangKy, '' AS TienQuyet, '' AS SongHanh "
            "FROM HocPhan HP "
            "JOIN LopHocPhan L WITH (NOLOCK) ON HP.MaHP = L.MaHP "
            "WHERE L.MaHK = ?",
            (ma_hk,),
        )
        result = []
        for r in rows:
            dat_tien_quyet = True
            dat_song_hanh  = True
            try:
                tq = execute_query(
                    "SELECT dbo.fn_KiemTraTienQuyet(?, ?) AS KQ", (ma_sv, r.MaHP)
                )
                if tq and tq[0].KQ == 0:
                    dat_tien_quyet = False
            except Exception:
                pass
            try:
                sh = execute_query(
                    "SELECT dbo.fn_KiemTraSongHanh(?, ?) AS KQ", (ma_sv, r.MaHP)
                )
                if sh and sh[0].KQ == 0:
                    dat_song_hanh = False
            except Exception:
                pass
            result.append({
                "MaHP"           : r.MaHP,
                "TenHP"          : r.TenHP,
                "SoTinChi"       : r.SoTinChi,
                "BatBuoc"        : bool(r.BatBuoc),
                "DieuKienDangKy" : r.DieuKienDangKy or "",
                "TienQuyet"      : r.TienQuyet or "",
                "SongHanh"       : r.SongHanh or "",
                "DatTienQuyet"   : dat_tien_quyet,
                "DatSongHanh"    : dat_song_hanh,
            })
        return result

    @staticmethod
    def get_dieu_kien(ma_hp: str) -> str:
        """Lấy chuỗi điều kiện đăng ký của 1 học phần dựa trên dữ liệu trong SQL."""
        rows = execute_query(
            "SELECT LoaiDieuKien, MaHP_TienQuyet FROM DieuKienHocPhan WHERE MaHP = ? ORDER BY LoaiDieuKien",
            (ma_hp,),
        )
        if rows:
            parts = [f"{r.LoaiDieuKien}: {r.MaHP_TienQuyet}" for r in rows]
            return "; ".join(parts)
        return ""

    @staticmethod
    def create(ma_hp: str, ten_hp: str, so_tin_chi: int, bat_buoc: bool) -> tuple[bool, str]:
        """Thêm học phần mới."""
        existing = execute_query("SELECT 1 FROM HocPhan WHERE MaHP = ?", (ma_hp,))
        if existing:
            return False, f"Mã học phần '{ma_hp}' đã tồn tại."
        execute_query(
            "INSERT INTO HocPhan (MaHP, TenHP, SoTinChi, BatBuoc) VALUES (?, ?, ?, ?)",
            (ma_hp, ten_hp, so_tin_chi, 1 if bat_buoc else 0),
            fetch=False,
        )
        return True, "Thêm học phần thành công."

    @staticmethod
    def update(ma_hp: str, ten_hp: str = None, so_tin_chi: int = None, bat_buoc: bool = None) -> tuple[bool, str]:
        """Cập nhật học phần."""
        existing = execute_query("SELECT 1 FROM HocPhan WHERE MaHP = ?", (ma_hp,))
        if not existing:
            return False, f"Không tìm thấy học phần '{ma_hp}'."
        sets, params = [], []
        if ten_hp    is not None: sets.append("TenHP = ?");    params.append(ten_hp)
        if so_tin_chi is not None: sets.append("SoTinChi = ?"); params.append(so_tin_chi)
        if bat_buoc  is not None: sets.append("BatBuoc = ?");  params.append(1 if bat_buoc else 0)
        if not sets:
            return False, "Không có thông tin để cập nhật."
        params.append(ma_hp)
        execute_query(f"UPDATE HocPhan SET {', '.join(sets)} WHERE MaHP = ?", tuple(params), fetch=False)
        return True, "Cập nhật học phần thành công."

    @staticmethod
    def delete(ma_hp: str) -> tuple[bool, str]:
        """Xóa học phần. Thất bại nếu còn Lớp HP đang tham chiếu."""
        refs = execute_query("SELECT COUNT(*) AS cnt FROM LopHocPhan WHERE MaHP = ?", (ma_hp,))
        if refs and refs[0].cnt > 0:
            return False, f"Không thể xóa: học phần '{ma_hp}' đang có {refs[0].cnt} lớp HP."
        execute_query("DELETE FROM DieuKienHocPhan WHERE MaHP = ? OR MaHP_TienQuyet = ?", (ma_hp, ma_hp), fetch=False)
        execute_query("DELETE FROM HocPhan WHERE MaHP = ?", (ma_hp,), fetch=False)
        return True, "Xóa học phần thành công."


class LopHocPhanModel:

    @staticmethod
    def get_by_hoc_phan(ma_hp: str, ma_hk: str) -> list[dict]:
        """
        Lấy danh sách Lớp HP của 1 môn trong 1 HK.

        Returns: list[{
            "MaLHP", "MaHP", "TenHP", "SoTinChi", "MaHK",
            "SoLuongDangKy", "SiSoToiDa", "SoChoConLai", "PhanTramDaDangKy"
        }]
        """
        rows = execute_query(
            "SELECT L.MaLHP, L.MaHP, HP.TenHP, HP.SoTinChi, L.MaHK, "
            "L.SoLuongDangKy, L.SiSoToiDa, "
            "(L.SiSoToiDa - L.SoLuongDangKy) AS SoChoConLai, "
            "CAST((L.SoLuongDangKy * 100.0 / NULLIF(L.SiSoToiDa, 0)) AS DECIMAL(5,2)) AS PhanTramDaDangKy "
            "FROM LopHocPhan L "
            "JOIN HocPhan HP ON L.MaHP = HP.MaHP "
            "WHERE L.MaHP = ? AND L.MaHK = ?",
            (ma_hp, ma_hk),
        )
        return [
            {
                "MaLHP"            : r.MaLHP,
                "MaHP"             : r.MaHP,
                "TenHP"            : r.TenHP,
                "SoTinChi"         : r.SoTinChi,
                "MaHK"             : r.MaHK,
                "SoLuongDangKy"    : r.SoLuongDangKy,
                "SiSoToiDa"        : r.SiSoToiDa,
                "SoChoConLai"      : r.SoChoConLai,
                "PhanTramDaDangKy" : float(r.PhanTramDaDangKy or 0),
            }
            for r in rows
        ]

    @staticmethod
    def get_lich(ma_lhp: str) -> list[dict]:
        """
        Lấy chi tiết lịch học (phòng, ca, thứ) của 1 lớp HP.
        Dùng để hiển thị thông tin trước khi SV nhấn Xác Nhận Đăng Ký.

        Returns: list[{
            "MaCTLHP", "MaLHP", "Thu", "Cahoc", "PhongHoc",
            "NgayBatDau", "NgayKetThuc"
        }]
        """
        rows = execute_query(
            "SELECT MaCTLHP, MaLHP, NgayBatDau, NgayKetThuc, ThuHoc, CaHoc, PhongHoc "
            "FROM ChiTietLopHocPhan WHERE MaLHP = ?",
            (ma_lhp,),
        )
        return [
            {
                "MaCTLHP"    : r.MaCTLHP,
                "MaLHP"      : r.MaLHP,
                "Thu"        : r.ThuHoc or "",
                "Cahoc"      : r.CaHoc or "",
                "PhongHoc"   : r.PhongHoc or "",
                "NgayBatDau" : str(r.NgayBatDau) if r.NgayBatDau else "",
                "NgayKetThuc": str(r.NgayKetThuc) if r.NgayKetThuc else "",
            }
            for r in rows
        ]

    @staticmethod
    def create(
        ma_lhp: str, ma_hp: str, ma_hk: str, si_so_toi_da: int,
        ngay_bd=None, ngay_kt=None, thu=None, ca_hoc=None, phong_hoc=None
    ) -> tuple[bool, str]:
        """Admin mở một lớp HP mới (gọi sp_ThemLopHP)."""
        ok, msg, rows = execute_procedure(
            "sp_ThemLopHocPhan",
            (ma_lhp, ma_hp, ma_hk, si_so_toi_da, ngay_bd, ngay_kt, thu, ca_hoc, phong_hoc),
        )
        if rows:
            r = rows[0]
            return bool(r.Success), r.Message
        return ok, msg

    @staticmethod
    def update(
        ma_lhp: str, si_so_toi_da: int = None,
        ngay_bd=None, ngay_kt=None, thu=None, ca_hoc=None, phong_hoc=None,
        ma_hp: str = None, ma_hk: str = None
    ) -> tuple[bool, str]:
        """Admin cập nhật thông tin lớp HP (gọi sp_CapNhatLopHocPhan)."""
        if ma_hp is None or ma_hk is None:
            existing = execute_query(
                "SELECT MaHP, MaHK FROM LopHocPhan WHERE MaLHP = ?",
                (ma_lhp,),
            )
            if existing:
                ma_hp = existing[0].MaHP
                ma_hk = existing[0].MaHK
            else:
                return False, "Không tìm thấy lớp học phần."
        ok, msg, rows = execute_procedure(
            "sp_CapNhatLopHocPhan",
            (ma_lhp, ma_hp, ma_hk, si_so_toi_da, ngay_bd, ngay_kt, thu, ca_hoc, phong_hoc),
        )
        if rows:
            r = rows[0]
            return bool(r.Success), r.Message
        return ok, msg


class DangKyModel:

    @staticmethod
    def dang_ky(
        ma_sv: str, ma_lhp: str, loai_dk: str = "Mới", max_retries: int = 3
    ) -> tuple[bool, str, str | None]:
        """
        Đăng ký một lớp học phần. Tự thử lại khi gặp Deadlock.
        Returns: (success, message, ma_dk)
        """
        for attempt in range(1, max_retries + 1):
            ma_dk = f"DK_{ma_sv}_{ma_lhp}_{int(time.time() * 1000)}"
            ok, msg, rows, err_code = execute_procedure(
                "sp_DangKyHocPhan", (ma_dk, ma_sv, ma_lhp, loai_dk)
            )
            ma_dk = None
            if rows:
                r     = rows[0]
                ok    = bool(r.Success)
                msg   = r.Message
                ma_dk = getattr(r, "MaDK", None)
            if ok:
                return True, msg, ma_dk
            if err_code == "DEADLOCK" or ("deadlock" in msg.lower() and attempt < max_retries):
                time.sleep(0.5 * attempt)
                continue
            return False, msg, None
        return False, "Không thể hoàn tất đăng ký, vui lòng thử lại.", None

    @staticmethod
    def huy_dang_ky(ma_dk: str, ma_sv: str) -> tuple[bool, str]:
        """
        Hủy đăng ký dựa trên MaDK.
        Nếu stored procedure lỗi, dùng fallback trực tiếp.
        Returns: (success, message)
        """
        ok, msg, rows, err_code = execute_procedure("sp_HuyDangKyHocPhan", (ma_dk,))
        if ok and rows:
            r = rows[0]
            return bool(r.Success), r.Message

        try:
            rows = execute_query(
                "SELECT MaDK, MaSV FROM DangKyHocPhan WHERE MaDK = ?",
                (ma_dk,),
            )
            if not rows:
                return False, "Không tìm thấy phiếu đăng ký."
            if rows[0].MaSV != ma_sv:
                return False, "Phiếu đăng ký không thuộc sinh viên này."

            execute_query("DELETE FROM DangKyHocPhan WHERE MaDK = ?", (ma_dk,), fetch=False)
            return True, "Hủy đăng ký thành công."
        except Exception as e:
            return False, f"Lỗi khi hủy đăng ký: {e}"

    @staticmethod
    def get_ds_da_dang_ky(ma_sv: str, ma_hk: str) -> list[dict]:
        """
        Lấy danh sách lớp HP sinh viên đã đăng ký trong HK.

        Returns: list[{
            "MaDK", "MaLHP", "MaHP", "TenHP", "SoTinChi",
            "TrangThai", "LoaiDangKy", "NgayDk", "HocPhi"
        }]
        """
        rows = execute_query(
            "SELECT DK.MaDK, DK.MaLHP, HP.MaHP, HP.TenHP, HP.SoTinChi, "
            "DK.TrangThai, DK.LoaiDangKy, DK.NgayDK AS NgayDk, 0 AS HocPhi "
            "FROM DangKyHocPhan DK "
            "JOIN LopHocPhan L ON DK.MaLHP = L.MaLHP "
            "JOIN HocPhan HP ON L.MaHP = HP.MaHP "
            "WHERE DK.MaSV = ? AND L.MaHK = ? "
            "ORDER BY DK.NgayDK DESC",
            (ma_sv, ma_hk),
        )
        return [
            {
                "MaDK"      : r.MaDK,
                "MaLHP"     : r.MaLHP,
                "MaHP"      : r.MaHP,
                "TenHP"     : r.TenHP,
                "SoTinChi"  : r.SoTinChi,
                "TrangThai" : r.TrangThai or "",
                "LoaiDangKy": r.LoaiDangKy or "",
                "NgayDk"    : str(r.NgayDk) if r.NgayDk else "",
                "HocPhi"    : int(r.HocPhi) if r.HocPhi else 0,
            }
            for r in rows
        ]

    @staticmethod
    def kiem_tra_trung_lich(ma_sv: str, ma_lhp: str) -> bool:
        """
        Kiểm tra lớp HP có bị trùng lịch với lớp SV đã ĐK không.
        Trả về True nếu BỊ TRÙNG.
        """
        try:
            rows = execute_query(
                "SELECT dbo.fn_KiemTraTrungLich(?, ?) AS KQ", (ma_sv, ma_lhp)
            )
            return bool(rows and rows[0].KQ == 1)
        except Exception:
            return False

    @staticmethod
    def get_thong_ke(ma_hk: str) -> list[dict]:
        """
        Lấy thống kê đăng ký theo lớp HP trong 1 HK (dành cho Admin).

        Returns: list[{
            "MaLHP", "MaHP", "TenHP", "SiSoToiDa",
            "SoLuongDangKy", "SoChoConLai", "PhanTramDaDangKy"
        }]
        """
        rows = execute_query(
            "SELECT L.MaLHP, HP.MaHP, HP.TenHP, L.SiSoToiDa, "
            "L.SoLuongDangKy, (L.SiSoToiDa - L.SoLuongDangKy) AS SoChoConLai, "
            "CAST((L.SoLuongDangKy * 100.0 / NULLIF(L.SiSoToiDa, 0)) AS DECIMAL(5,2)) AS PhanTramDaDangKy "
            "FROM LopHocPhan L "
            "JOIN HocPhan HP ON L.MaHP = HP.MaHP "
            "WHERE L.MaHK = ? "
            "ORDER BY HP.MaHP, L.MaLHP",
            (ma_hk,),
        )
        return [
            {
                "MaLHP"            : r.MaLHP,
                "MaHP"             : r.MaHP,
                "TenHP"            : r.TenHP,
                "SiSoToiDa"        : r.SiSoToiDa,
                "SoLuongDangKy"    : r.SoLuongDangKy,
                "SoChoConLai"      : r.SoChoConLai,
                "PhanTramDaDangKy" : float(r.PhanTramDaDangKy or 0),
            }
            for r in rows
        ]

    @staticmethod
    def get_ds_sv_theo_lop(ma_lhp: str) -> list[dict]:
        """
        Lấy danh sách sinh viên đã đăng ký vào 1 lớp HP (Admin xem).

        Returns: list[{
            "MaDK", "MaSV", "TenSinhVien", "TrangThai", "LoaiDangKy", "NgayDk"
        }]
        """
        rows = execute_query(
            "SELECT DK.MaDK, DK.MaSV, SV.HoTen AS TenSinhVien, DK.TrangThai, DK.LoaiDangKy, DK.NgayDK AS NgayDk "
            "FROM DangKyHocPhan DK "
            "JOIN SinhVien SV ON DK.MaSV = SV.MaSV "
            "WHERE DK.MaLHP = ? AND DK.TrangThai != N'DaHuy' "
            "ORDER BY DK.NgayDK",
            (ma_lhp,),
        )
        return [
            {
                "MaDK"       : r.MaDK,
                "MaSV"       : r.MaSV,
                "TenSinhVien": r.TenSinhVien or "",
                "TrangThai"  : r.TrangThai or "",
                "LoaiDangKy" : r.LoaiDangKy or "",
                "NgayDk"     : str(r.NgayDk) if r.NgayDk else "",
            }
            for r in rows
        ]
