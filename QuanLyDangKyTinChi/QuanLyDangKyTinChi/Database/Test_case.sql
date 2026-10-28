USE QuanLyDangKyHocPhan;
GO
--- 1 Quan ly hoc ky
-- a. tao hoc ky thanh cong
EXEC sp_CapNhatHocKy
    @MaHK = 'HK1_2026',
    @TenHK = N'Học kỳ 1 năm 2026',
    @NamHoc = 2026,
    @NgayMoDangKy = '2026-06-01',
    @NgayDongDangKy = '2026-06-15';
--b. ngay dong nho hon ngay mo 
EXEC sp_CapNhatHocKy
    @MaHK = 'HK1_2026',
    @TenHK = N'Học kỳ lỗi',
    @NamHoc = 2026,
    @NgayMoDangKy = '2026-06-15',
    @NgayDongDangKy = '2026-06-01';
GO

--c.Ma hoc ky khong ton tai
DECLARE @NgayMo DATETIME = GETDATE();
DECLARE @NgayDong DATETIME = DATEADD(DAY,10,GETDATE());

EXEC dbo.sp_CapNhatHocKy
    @MaHK = 'HK999',
    @TenHK = N'Test',
    @NamHoc = 2026,
    @NgayMoDangKy = @NgayMo,
    @NgayDongDangKy = @NgayDong;
-- 2. Quan ly lop hoc phan 
--a. THem lop hoc phan thanh cong
EXEC sp_ThemLopHocPhan
    @MaLHP='LHP100',
    @MaHP='HP001',
    @MaHK='HK1_2026',
    @SiSoToiDa=50;
--b. Trung ma lop hoc phan  
EXEC sp_ThemLopHocPhan
    @MaLHP='LHP001',
    @MaHP='HP001',
    @MaHK='HK1_2026',
    @SiSoToiDa=50;
--c. Hoc phan kh ton tai 
EXEC sp_ThemLopHocPhan
    @MaLHP='LHP200',
    @MaHP='HP999',
    @MaHK='HK1_2026',
    @SiSoToiDa=50;
-- d. Si so < 0
EXEC sp_ThemLopHocPhan
    @MaLHP='LHP201',
    @MaHP='HP001',
    @MaHK='HK1_2026',
    @SiSoToiDa=0;
--3. Cap nhat lop hoc phan 
--a. CAp nhat thanh cong 
EXEC sp_CapNhatLopHocPhan
    @MaLHP='LHP001',
    @MaHP='HP001',
    @MaHK='HK1_2026',
    @SiSoToiDa=30;
--b. Lop hoc phan k ton tai 
EXEC sp_CapNhatLopHocPhan
    @MaLHP='LHP999',
    @MaHP='HP001',
    @MaHK='HK1_2026',
    @SiSoToiDa=60;
--c.Giam si so nho hon so SV da dang ky 
SELECT *
FROM LopHocPhan
WHERE MaLHP='LHP001';
EXEC sp_CapNhatLopHocPhan
    @MaLHP='LHP001',
    @MaHP='HP001',
    @MaHK='HK1_2026',
    @SiSoToiDa=40;
--4. Kiem tra triggẻr sỉ só
--a. Tăng sỉ số
SELECT *
FROM LopHocPhan
WHERE MaLHP='LHP001';

EXEC sp_DangKyHocPhan
    @MaDK='DK999',
    @MaSV='SV050',
    @MaLHP='LHP001',
    @LoaiDangKy=N'Học mới';
--c. Giam si so 
DELETE FROM DangKyHocPhan
WHERE MaDK='DK999';
SELECT *
FROM LopHocPhan
WHERE MaLHP='LHP001';
--5. Kiem tra audit log
--a. log đăng ký
EXEC sp_DangKyHocPhan
    @MaDK='DK888',
    @MaSV='SV049',
    @MaLHP='LHP001',
    @LoaiDangKy=N'Học mới';

SELECT *
FROM NhatKyDangKyHocPhan
ORDER BY MaNhatKy DESC;
--b. Log hủy đăng ký 
DELETE FROM DangKyHocPhan
WHERE MaDK='DK888';
SELECT *
FROM NhatKyDangKyHocPhan
ORDER BY MaNhatKy DESC;
--6. Kiểm tra báo cáo thống kê 
--a. Tổng tín chỉ 
SELECT *
FROM v_ThongKeTongTinChi
WHERE MaSV='SV001';
--b. Tính trạng lớp học phần  (XEM LẠI)
SELECT *
FROM v_TinhTrangLopHocPhan;
--7. Kiểm tra khóa đăng ký học phần 
UPDATE HocKy
SET NgayDongDangKy='2026-06-01'
WHERE MaHK='HK1_2026';

EXEC sp_DangKyHocPhan
    @MaDK='DK777',
    @MaSV='SV030',
    @MaLHP='LHP001',
    @LoaiDangKy=N'Học mới';
--8. Kiểm tra hủy đăng ký khi đóng cổng  (Xem lại )
UPDATE HocKy
SET NgayDongDangKy = DATEADD(DAY, -1, GETDATE())
WHERE MaHK = 'HK1_2026';

DELETE FROM DangKyHocPhan
WHERE MaDK = 'DK0022';



-- Them hoc phan moi 
EXEC sp_ThemLopHocPhan
    @MaLHP = 'LHP091',
    @MaHP = 'HP001',
    @MaHK = 'HK1_2026',
    @SiSoToiDa = 50,
    @NgayBatDau = '2026-09-01',
    @NgayKetThuc = '2026-12-31',
    @ThuHoc = N'Thứ 2',
    @CaHoc = N'Ca 1',
    @PhongHoc = N'A101';

SELECT * FROM ChiTietLopHocPhan

SELECT * FROM LopHocPhan


-- KIEM TRA DEADLOCK
EXEC sp_Deadlock_SinhVien
    @MaLHP = 'LHP001',
    @MaHK = 'HK1_2026';

UPDATE LopHocPhan
SET SoLuongDangKy =(
    SELECT COUNT(*) FROM DangKyHocPhan dk 
    WHERE dk.MaLHP = LHP.MaLHP
)
FROM LopHocPhan LHP;

