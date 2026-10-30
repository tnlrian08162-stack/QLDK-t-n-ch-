USE QuanLyDangKyHocPhan;
GO

/*===============================


--VIEW--


===============================*/


-- A. View thống kê tổng số tín chỉ mà mỗi sinh viên đã đăng ký thành công theo học kỳ.
DROP VIEW v_ThongKeTongTinChi;
GO

CREATE VIEW v_ThongKeTongTinChi AS
SELECT 
    sv.MaSV,
    sv.HoTen,
    hk.MaHK,
    hk.TenHK,
    SUM(hp.SoTinChi) AS TongTinChi
FROM SinhVien sv
JOIN DangKyHocPhan dk ON sv.MaSV = dk.MaSV
JOIN LopHocPhan lhp ON dk.MaLHP = lhp.MaLHP
JOIN HocPhan hp ON lhp.MaHP = hp.MaHP
JOIN HocKy hk ON lhp.MaHK = hk.MaHK
WHERE dk.TrangThai = N'Thành công'
GROUP BY 
    sv.MaSV,
    sv.HoTen,
    hk.MaHK,
    hk.TenHK;
GO

-- B. View tổng hợp tình trạng sức chứa của tất cả các Lớp học phần đang mở.
DROP VIEW v_TinhTrangLopHocPhan;
GO

CREATE VIEW v_TinhTrangLopHocPhan AS
SELECT 
    lhp.MaLHP,
    hp.MaHP,
    hp.TenHP,
    hk.TenHK,
    lhp.SoLuongDangKy,
    lhp.SiSoToiDa,
    (lhp.SiSoToiDa - lhp.SoLuongDangKy) AS SoChoConTrong,
    CAST(
        CASE 
            WHEN lhp.SiSoToiDa = 0 THEN 0 
            ELSE lhp.SoLuongDangKy * 100.0 / lhp.SiSoToiDa
        END
        AS DECIMAL(5,2)
    )AS PhanTramDangKy,

    CASE 
        WHEN lhp.SoLuongDangKy >= lhp.SiSoToiDa THEN N'Đã đầy'
        WHEN (lhp.SiSoToiDa - lhp.SoLuongDangKy) <= 5 THEN N'Sắp đầy'
        ELSE N'Còn trống'
    END AS TrangThaiLop
FROM LopHocPhan lhp
JOIN HocPhan hp ON lhp.MaHP = hp.MaHP
JOIN HocKy hk ON lhp.MaHK = hk.MaHK;
GO


--C. View học phần sinh viên có thể đăng ký trong học kỳ
CREATE VIEW v_HocPhanCoTheDangKy AS
SELECT
    hk.MaHK,
    hk.TenHK,
    hp.MaHP,
    hp.TenHP,
    hp.SoTinChi,
    hp.BatBuoc,
    lhp.MaLHP,
    lhp.SiSoToiDa,
    lhp.SoLuongDangKy,
    (lhp.SiSoToiDa - lhp.SoLuongDangKy) AS SoChoConTrong,
    '' AS DieuKienDangKy,
    '' AS TienQuyet,
    '' AS SongHanh
FROM LopHocPhan lhp
JOIN HocPhan hp ON lhp.MaHP = hp.MaHP
JOIN HocKy hk ON lhp.MaHK = hk.MaHK
WHERE lhp.SoLuongDangKy < lhp.SiSoToiDa;
GO


--D.View lịch học chi tiết của sinh viên
DROP VIEW v_LichHocChiTietSinhVien;
GO

CREATE VIEW v_LichHocChiTietSinhVien AS
SELECT
    sv.MaSV,
    sv.HoTen,
    hp.TenHP,
    lhp.MaLHP,
    ct.ThuHoc,
    ct.CaHoc,
    ct.NgayBatDau,
    ct.NgayKetThuc,
    ct.PhongHoc,
    dk.TrangThai
FROM SinhVien sv
JOIN DangKyHocPhan dk ON sv.MaSV = dk.MaSV
JOIN LopHocPhan lhp ON dk.MaLHP = lhp.MaLHP
JOIN HocPhan hp ON lhp.MaHP = hp.MaHP
JOIN ChiTietLopHocPhan ct ON lhp.MaLHP = ct.MaLHP
WHERE dk.TrangThai = N'Thành công';
GO

--E .View danh sách đăng ký của sinh viên
DROP VIEW v_DanhSachDangKySinhVien;
GO

CREATE VIEW v_DanhSachDangKySinhVien AS
SELECT
    dk.MaDK,
    sv.MaSV,
    sv.HoTen,
    hp.MaHP,
    hp.TenHP,
    hp.SoTinChi,
    hk.MaHK,
    hk.TenHK,
    lhp.MaLHP,
    dk.NgayDK,
    dk.TrangThai,
    dk.LoaiDangKy,
    0 AS HocPhi
FROM SinhVien sv
JOIN DangKyHocPhan dk ON sv.MaSV = dk.MaSV
JOIN LopHocPhan lhp ON dk.MaLHP = lhp.MaLHP
JOIN HocPhan hp ON lhp.MaHP = hp.MaHP
JOIN HocKy hk ON lhp.MaHK = hk.MaHK;
GO

--F .View Thống kê danh sách học phần (ADMIN)
CREATE VIEW v_ThongKeDangKyHocPhan
AS
SELECT
    lhp.MaLHP,
    hp.MaHP,
    hp.TenHP,
    hk.MaHK,
    hk.TenHK,
    lhp.SiSoToiDa,
    lhp.SoLuongDangKy,
    (lhp.SiSoToiDa - lhp.SoLuongDangKy) AS SoChoConTrong,
    CAST(
        CASE
            WHEN lhp.SiSoToiDa = 0 THEN 0
            ELSE lhp.SoLuongDangKy * 100.0 / lhp.SiSoToiDa
        END
        AS DECIMAL(5,2)
    ) AS PhanTramDangKy,
    COUNT(dk.MaDK) AS SoLuongDangKyThucTe
FROM LopHocPhan lhp
JOIN HocPhan hp ON lhp.MaHP = hp.MaHP
JOIN HocKy hk ON lhp.MaHK = hk.MaHK
LEFT JOIN DangKyHocPhan dk
    ON lhp.MaLHP = dk.MaLHP
    AND dk.TrangThai = N'Thành công'
GROUP BY
    lhp.MaLHP,
    hp.MaHP,
    hp.TenHP,
    hk.MaHK,
    hk.TenHK,
    lhp.SiSoToiDa,
    lhp.SoLuongDangKy;
GO




--KIỂM THỬ VIEW




-- Lệnh gọi View để kiểm tra kết quả:
SELECT * FROM v_ThongKeTongTinChi;
GO
-- Lệnh gọi View để kiểm tra kết quả:
SELECT * FROM v_TinhTrangLopHocPhan ORDER BY SoChoConTrong ASC;
GO
-- kiểm thử  học phần có thể đăng ký
SELECT * FROM v_HocPhanCoTheDangKy ;
--KIỂM THỬ LỊCH HỌC CHI TIẾT CỦA SINH VIÊN
SELECT * FROM v_LichHocChiTietSinhVien 
-- KIỂM THỬ DANH SÁCH ĐĂNG KÝ CỦA SINH VIÊN
SELECT * FROM v_DanhSachDangKySinhVien ;

