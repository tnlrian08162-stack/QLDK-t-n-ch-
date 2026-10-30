USE QuanLyDangKyHocPhan;
GO

/* =========================================================================
   1. INDEX - CHỈ MỤC TỐI ƯU HÓA TRUY VẤN
   ========================================================================= */

-- Chỉ mục trên các khóa ngoại của bảng LopHocPhan
IF EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_LopHocPhan_MaHP' AND object_id = OBJECT_ID('LopHocPhan'))
    DROP INDEX IX_LopHocPhan_MaHP ON LopHocPhan;
GO
CREATE NONCLUSTERED INDEX IX_LopHocPhan_MaHP ON LopHocPhan(MaHP);
GO

IF EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_LopHocPhan_MaHK' AND object_id = OBJECT_ID('LopHocPhan'))
    DROP INDEX IX_LopHocPhan_MaHK ON LopHocPhan;
GO
CREATE NONCLUSTERED INDEX IX_LopHocPhan_MaHK ON LopHocPhan(MaHK);
GO

-- Chỉ mục trên khóa ngoại của bảng ChiTietLopHocPhan
IF EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_ChiTietLopHocPhan_MaLHP' AND object_id = OBJECT_ID('ChiTietLopHocPhan'))
    DROP INDEX IX_ChiTietLopHocPhan_MaLHP ON ChiTietLopHocPhan;
GO
CREATE NONCLUSTERED INDEX IX_ChiTietLopHocPhan_MaLHP ON ChiTietLopHocPhan(MaLHP);
GO

-- Chỉ mục bao phủ kèm điều kiện lọc cho trạng thái 'Thành công'
IF EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_DangKyHocPhan_TrangThai_ThanhCong' AND object_id = OBJECT_ID('DangKyHocPhan'))
    DROP INDEX IX_DangKyHocPhan_TrangThai_ThanhCong ON DangKyHocPhan;
GO
CREATE NONCLUSTERED INDEX IX_DangKyHocPhan_TrangThai_ThanhCong
ON DangKyHocPhan(MaSV, MaLHP)
INCLUDE (TrangThai, LoaiDangKy)
WHERE TrangThai = N'Thành công';
GO
 -- lệnh kiểm tra các chỉ mục đã tạo
 SELECT name
FROM sys.indexes
WHERE object_id = OBJECT_ID('DangKyHocPhan');
EXEC sp_helpindex 'DangKyHocPhan';

/* =========================================================================
   2. SECURITY - BẢO MẬT & PHÂN QUYỀN NGƯỜI DÙNG (Cập nhật Schema dbo)
   ========================================================================= */

-- Khởi tạo các nhóm quyền (Database Roles)
IF DATABASE_PRINCIPAL_ID('GiaoVuRole') IS NOT NULL DROP ROLE GiaoVuRole;
IF DATABASE_PRINCIPAL_ID('SinhVienRole') IS NOT NULL DROP ROLE SinhVienRole;
GO

CREATE ROLE GiaoVuRole;
GO
CREATE ROLE SinhVienRole;
GO

----------------------------------------------------------------------------
-- PHÂN QUYỀN CHO NHÓM GIÁO VỤ (ACADEMIC STAFF)
----------------------------------------------------------------------------
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.SinhVien TO GiaoVuRole;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.HocPhan TO GiaoVuRole;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.DieuKienHocPhan TO GiaoVuRole;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.HocKy TO GiaoVuRole;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.LopHocPhan TO GiaoVuRole;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.ChiTietLopHocPhan TO GiaoVuRole;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.DangKyHocPhan TO GiaoVuRole;

GRANT EXECUTE TO GiaoVuRole;
GO

----------------------------------------------------------------------------
-- PHÂN QUYỀN CHO NHÓM SINH VIÊN (STUDENTS)
----------------------------------------------------------------------------
GRANT SELECT ON dbo.SinhVien TO SinhVienRole;
GRANT SELECT ON dbo.HocPhan TO SinhVienRole;
GRANT SELECT ON dbo.DieuKienHocPhan TO SinhVienRole;
GRANT SELECT ON dbo.HocKy TO SinhVienRole;
GRANT SELECT ON dbo.LopHocPhan TO SinhVienRole;
GRANT SELECT ON dbo.ChiTietLopHocPhan TO SinhVienRole;

-- Cấp quyền trên các VIEW (Đã thêm prefix dbo. để sửa lỗi 15151)
GRANT SELECT ON dbo.v_ThongKeTongTinChi TO SinhVienRole;
GRANT SELECT ON dbo.v_TinhTrangLopHocPhan TO SinhVienRole;
GRANT SELECT ON dbo.v_HocPhanCoTheDangKy TO SinhVienRole;
GRANT SELECT ON dbo.v_LichHocChiTietSinhVien TO SinhVienRole;
GRANT SELECT ON dbo.v_DanhSachDangKySinhVien TO SinhVienRole;

-- Khóa quyền thao tác bảng trực tiếp
DENY INSERT, UPDATE, DELETE ON dbo.DangKyHocPhan TO SinhVienRole;

-- Cho phép gọi các Stored Procedure đăng ký/hủy (Đã thêm prefix dbo. để sửa lỗi 15151)
GRANT EXECUTE ON dbo.sp_DangKyHocPhan TO SinhVienRole;
GO
GRANT EXECUTE ON dbo.sp_HuyDangKyHocPhan TO SinhVienRole;
GO


/* =========================================================================
   3. BACKUP DATABASE - ĐƯỜNG DẪN D:\HQTCSDL\BTL
   ========================================================================= */

USE master;
GO

ALTER DATABASE QuanLyDangKyHocPhan SET RECOVERY FULL;
GO

-- 3.1. SAO LƯU TOÀN BỘ (FULL BACKUP)
BACKUP DATABASE QuanLyDangKyHocPhan
TO DISK = 'D:\HQTCSDL\BTL\QuanLyDangKyHocPhan_Full.bak'
WITH FORMAT,
     INIT,
     NAME = 'Full Backup - He Thong Quan Ly Dang Ky Hoc Phan',
     STATS = 10;
GO

-- 3.2. SAO LƯU THAY ĐỔI (DIFFERENTIAL BACKUP)
BACKUP DATABASE QuanLyDangKyHocPhan
TO DISK = 'D:\HQTCSDL\BTL\QuanLyDangKyHocPhan_Diff.bak'
WITH DIFFERENTIAL,
     INIT,
     NAME = 'Differential Backup - Cac thay doi moi',
     STATS = 10;
GO

-- 3.3. SAO LƯU NHẬT KÝ GIAO DỊCH (TRANSACTION LOG BACKUP)
BACKUP LOG QuanLyDangKyHocPhan
TO DISK = 'D:\HQTCSDL\BTL\QuanLyDangKyHocPhan_Log.trn'
WITH INIT,
     NAME = 'Transaction Log Backup - Nhat ky dang ky hoc phan',
     STATS = 10;
GO

-- 3.4. KIỂM TRA FILE SAO LƯU
RESTORE VERIFYONLY FROM DISK = 'D:\HQTCSDL\BTL\QuanLyDangKyHocPhan_Full.bak';
GO

