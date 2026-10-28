USE QuanLyDangKyHocPhan;
GO

/*========================================	
	DEMO TRUE LOST UPDATE
	Bối cảnh:
	- T1 (SV001) và T2 (SV002) cùng đọc SoLuongDangKy của LHP013.
	- T1 ghi xuống DB sĩ số mới.
	- T2 ghi đè xuống DB sĩ số mới (Làm mất kết quả của T1).
	- Hậu quả: DB có 2 bản ghi Đăng ký, nhưng sĩ số tổng chỉ tăng 1.
========================================*/

DROP PROCEDURE IF EXISTS sp_Demo_LostUpdate;
GO

CREATE PROCEDURE sp_Demo_LostUpdate
    @MaDK VARCHAR(50),
    @MaSV VARCHAR(20),
    @MaLHP VARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;

    SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
    BEGIN TRANSACTION;

    DECLARE @SoLuongHienTai INT;
    DECLARE @SoLuongMoi INT;

    -- [ĐOẠN LỖI] Đọc bằng Shared Lock thông thường
    SELECT @SoLuongHienTai = SoLuongDangKy
    FROM LopHocPhan
    WHERE MaLHP = @MaLHP;

     /* 
       KHẮC PHỤC LOST UPDATE
    -- Đọc với Update Lock
    SELECT @SoLuongHienTai = SoLuongDangKy
    FROM LopHocPhan WITH (UPDLOCK)
    WHERE MaLHP = @MaLHP;
     */

    -- Giả lập độ trễ 5 giây
    WAITFOR DELAY '00:00:10';

    -- Tính toán số lượng mới
    SET @SoLuongMoi = @SoLuongHienTai + 1;

    -- 1. Thực hiện INSERT bản ghi Đăng ký 
    INSERT INTO DangKyHocPhan (MaDK, TrangThai, LoaiDangKy, NgayDK, MaSV, MaLHP)
    VALUES (@MaDK, N'Thành công', N'Học mới', GETDATE(), @MaSV, @MaLHP);

    -- 2. GHI ĐÈ kết quả
    UPDATE LopHocPhan
    SET SoLuongDangKy = @SoLuongMoi
    WHERE MaLHP = @MaLHP;

    COMMIT TRANSACTION;

END;
GO

/* 
Mở 2 cửa sổ querry riêng biệt để kiểm tra, copy paste nội dung của 2 đoạn dưới sang cửa số mới riêng biệt
- Chạy code của querry 1 rồi chạy liền code của querry 2
*/

/*---------------- CỬA SỔ QUERY 1 ----------------
USE QuanLyDangKyHocPhan;
GO
EXEC sp_Demo_LostUpdate 
    @MaDK = 'DK_TEST_01', 
    @MaSV = 'SV001', 
    @MaLHP = 'LHP013';
--------------------------------------------------*/

/*---------------- CỬA SỔ QUERY 2 ----------------
USE QuanLyDangKyHocPhan;
GO
EXEC sp_Demo_LostUpdate 
    @MaDK = 'DK_TEST_02', 
    @MaSV = 'SV002', 
    @MaLHP = 'LHP013';
--------------------------------------------------*/

-- Kiểm tra số lượng đăng ký của lớp học phần
SELECT
    MaLHP,
    SoLuongDangKy,
    SiSoToiDa
FROM LopHocPhan
WHERE MaLHP = 'LHP013';

-- Xoá dữ liệu vừa đăng ký
DELETE FROM DangKyHocPhan
WHERE MaDK IN ('DK_TEST_01', 'DK_TEST_02');

