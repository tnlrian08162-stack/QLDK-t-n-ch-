USE QuanLyDangKyHocPhan;
GO

/*========================================	
	DEMO DIRTY READ
	Bối cảnh:
	- T1: Nhà trường UPDATE lịch học của lớp học phần
	nhưng chưa COMMIT dữ liệu
	- T2: Sinh viên xem lịch học nhưng trong lúc T1 đang xử lý
========================================*/

-- T1: Nhà trường Cập nhật lịch học
DROP PROCEDURE IF EXISTS sp_Demo_DirtyRead_Admin
GO

CREATE PROCEDURE sp_Demo_DirtyRead_Admin
(
	@MaLHP VARCHAR(20),
	@ThuHoc NVARCHAR(20)
)
AS
BEGIN 
	SET NOCOUNT ON;
	-- Bắt đầu thực hiện giao tác T1
	BEGIN TRANSACTION;
		-- Nhà trường cập nhật lịch học
		UPDATE ChiTietLopHocPhan
		SET ThuHoc = @ThuHoc
		WHERE MaLHP = @MaLHP;
		/*
		- T1 đang giữ X-Lock trên ChiTietLopHocPhan
		- Dữ liệu mới chưa được lưu chính thức
		*/
		WAITFOR DELAY '00:00:10';
		ROLLBACK TRANSACTION;
		PRINT N'ROLLBACK dữ liệu';

END
GO

-- T2: Sinh viên xem lịch học
DROP PROCEDURE IF EXISTS sp_Demo_DirtyRead_SinhVien
GO

CREATE PROCEDURE sp_Demo_DirtyRead_SinhVien
(
	@MaSV VARCHAR(20)
)
AS
BEGIN
	SET NOCOUNT ON;
	/*
	Khắc phục:
	--SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
	- Không đọc dữ liệu chưa COMMIT
	- Nếu T1 đang UPDATE thì T2 phải chờ T1 COMMIT/ROLLBACK
	*/
	-- Cho phép đọc dữ liệu chưa COMMIT
	SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

	/*
	- Sinh viên xem lịch học
	- Nếu T1 đang UPDATE và chưa COMMIT
	thì SV vẫn đọc được dữ liệu mới 
	*/
	SELECT 
	MaSV,
	HoTen,
	TenHP,
	MaLHP,
	ThuHoc,
	CaHoc,
	PhongHoc
	FROM v_LichHocChiTietSinhVien
	WHERE MaSV = @MaSV;

END
GO
	

		