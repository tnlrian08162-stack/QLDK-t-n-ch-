USE QuanLyDangKyHocPhan;
GO

/*========================================	
	DEMO DEADLOCK
	Bối cảnh:
	- T1: Nhà trường cập nhật học kỳ 
	- T2: Sinh viên sinh viên đang đăng ký học phần (gần như đồng thời)
========================================*/
-- T1: Nhà trường cập nhật học kỳ
DROP PROCEDURE IF EXISTS sp_Demo_Deadlock_Admin
GO

CREATE PROCEDURE sp_Demo_Deadlock_Admin
(
    @MaHK VARCHAR(20),
    @TenHK NVARCHAR(50),
    @NamHoc INT,
    @NgayMoDangKy DATETIME,
    @NgayDongDangKy DATETIME
)
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
        BEGIN TRANSACTION;

    -- Bước 1: T1 nắm X-Lock trên HOCKY
        UPDATE HOCKY
        SET
            TenHK = @TenHK,
            NamHoc = @NamHoc,
            NgayMoDangKy = @NgayMoDangKy,
            NgayDongDangKy = @NgayDongDangKy
        WHERE MaHK = @MaHK;

    -- Giả lập trễ 5 giây để đợi Sinh viên xen vào
        WAITFOR DELAY '00:00:10';

    -- Bước 2: T1 xin S-LOCK trên LOPHP
        DECLARE @TongSV INT;

        SELECT @TongSV = SUM(SoLuongDangKy)
        FROM LopHocPhan
        WHERE MaHK = @MaHK;

        COMMIT TRANSACTION;
        PRINT N'Cập nhật học kỳ thành công';

    END TRY
    BEGIN CATCH

        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        PRINT ERROR_MESSAGE();
    END CATCH

END
GO

-- T2 Sinh viên đang đăng ký học phần
DROP PROCEDURE IF EXISTS sp_Demo_Deadlock_SinhVien
GO

CREATE PROCEDURE sp_Demo_Deadlock_SinhVien
    @MaLHP NVARCHAR(30),
    @MaHK  NVARCHAR(10)
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
        BEGIN TRANSACTION;
             /* Khắc phục : Xử lý HOCKY trước LopHocPhan sau
            --DECLARE @NgayDong DATETIME;
            --SELECT @NgayDong = NgayDongDangKy 
            --FROM HOCKY 
            --WHERE MaHK = @MaHK;
            */

            -- Bước 1: T2 nắm X-Lock trên bảng LOPHP
            UPDATE LopHocPhan 
            SET SoLuongDangKy = SoLuongDangKy + 1 
            WHERE MaLHP = @MaLHP;

            -- Giả lập trễ 5 giây để đợi Admin xen vào
            WAITFOR DELAY '00:00:10';

            -- Bước 2: T2 xin S-Lock trên bảng HOCKY
            DECLARE @NgayDong DATETIME;
            SELECT @NgayDong = NgayDongDangKy 
            FROM HOCKY 
            WHERE MaHK = @MaHK;

        COMMIT TRANSACTION;
        PRINT N'Đăng ký thành công!';
            
    END TRY

    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        PRINT ERROR_MESSAGE();
    END CATCH;

END
GO