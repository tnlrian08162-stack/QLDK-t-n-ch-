use QuanLyDangKyHocPhan;
go
/*Cửa sổ 2:
====================================================*/

INSERT INTO DangKyHocPhan
(
    MaDK,
    TrangThai,
    LoaiDangKy,
    NgayDK,
    MaSV,
    MaLHP
)
VALUES
(
    'DK999',
    N'Thành công',
    N'Học mới',
    GETDATE(),
    'SV001',
    'LHP001'
);
;
--tìm các sinh viên chưa đăng kí lhp001
SELECT MaSV
FROM SinhVien sv
WHERE NOT EXISTS
(
    SELECT 1
    FROM DangKyHocPhan dk
    WHERE dk.MaSV = sv.MaSV
      AND dk.MaLHP = 'LHP001'
);