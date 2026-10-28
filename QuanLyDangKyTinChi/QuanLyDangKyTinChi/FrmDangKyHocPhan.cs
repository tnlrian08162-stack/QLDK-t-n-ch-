using System;
using System.Collections;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Data.SqlClient;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace QuanLyDangKyTinChi
{
    public partial class FrmDangKyHocPhan : Form
    {
        private string maSV;
        DBConnection db = new DBConnection();
        private string maLHPChon = "";
        public FrmDangKyHocPhan(string maSV)
        {
            InitializeComponent();
            this.maSV = maSV;
        }

        private void FrmDangKyHocPhan_Load(object sender, EventArgs e)
        {
            lblMaSV.Text = maSV;
            LoadLopHocPhan();
        }

        private void LoadLopHocPhan()
        {
            string query = @"
        SELECT
            l.MaLHP,
            h.TenHP,
            h.SoTinChi,
            c.ThuHoc,
            c.CaHoc,
            c.PhongHoc,
            l.SoLuongDangKy,
            l.SiSoToiDa
        FROM LopHocPhan l
        INNER JOIN HocPhan h
            ON l.MaHP = h.MaHP
        INNER JOIN ChiTietLopHocPhan c
            ON l.MaLHP = c.MaLHP";

            dgvHocPhan.DataSource = db.ExecuteQuery(query);
        }

        private void dgvHocPhan_CellClick(object sender, DataGridViewCellEventArgs e)
        {
            if (e.RowIndex >= 0)
            {
                maLHPChon = dgvHocPhan.Rows[e.RowIndex]
                       .Cells[0].Value.ToString();
            }
        }

        private void btnDangKy_Click(object sender, EventArgs e)
        {

            if (string.IsNullOrEmpty(maLHPChon))
            {
                MessageBox.Show("Vui lòng chọn học phần!");
                return;
            }

            using (SqlConnection conn = db.GetConnection())
            {
                conn.Open();

                // Kiểm tra đã đăng ký chưa
                string checkQuery = @"
                SELECT COUNT(*)
                FROM DangKyHocPhan
                WHERE MaSV = @MaSV
                AND MaLHP = @MaLHP";

                SqlCommand checkCmd = new SqlCommand(checkQuery, conn);
                checkCmd.Parameters.AddWithValue("@MaSV", maSV);
                checkCmd.Parameters.AddWithValue("@MaLHP", maLHPChon);

                int count = (int)checkCmd.ExecuteScalar();

                if (count > 0)
                {
                    MessageBox.Show("Bạn đã đăng ký học phần này rồi!");
                    return;
                }

                // Tạo mã đăng ký
                string maDK = Guid.NewGuid().ToString();
                // Thêm đăng ký
                string insertQuery = @"
                INSERT INTO DangKyHocPhan
                (MaDK, TrangThai, LoaiDangKy, NgayDK, MaSV, MaLHP)
                VALUES
                (@MaDK, N'Đã đăng ký', N'Đăng ký mới', GETDATE(), @MaSV, @MaLHP)";

                SqlCommand insertCmd = new SqlCommand(insertQuery, conn);
                insertCmd.Parameters.AddWithValue("@MaDK", maDK);
                insertCmd.Parameters.AddWithValue("@MaSV", maSV);
                insertCmd.Parameters.AddWithValue("@MaLHP", maLHPChon);


                // Tăng số lượng đăng ký
                string updateQuery = @"
                UPDATE LopHocPhan
                SET SoLuongDangKy = SoLuongDangKy + 1
                WHERE MaLHP = @MaLHP";

                SqlCommand updateCmd = new SqlCommand(updateQuery, conn);
                updateCmd.Parameters.AddWithValue("@MaLHP", maLHPChon);
  
                // Reload DataGridView
                insertCmd.ExecuteNonQuery();

                // cập nhật số lượng đăng ký
                updateCmd.ExecuteNonQuery();

                // reload dữ liệu
                LoadLopHocPhan();
                MessageBox.Show("Đăng ký thành công!");
            }
        }

        private void btnQuayLai_Click(object sender, EventArgs e)
        {
            this.Close();
        }
    }
}
