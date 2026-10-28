using System;
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
    public partial class FrmChonSinhVien : Form
    {
        private DBConnection db = new DBConnection();
        public FrmChonSinhVien()
        {
            InitializeComponent();
        }

        private void btnDongY_Click(object sender, EventArgs e)
        {
            string maSV = cboSinhVien.Text.Split('-')[0].Trim();

            FrmDangKyHocPhan frm = new FrmDangKyHocPhan(maSV);
            frm.Show();

            this.Hide();
        }

        private void cboSinhVien_SelectedIndexChanged(object sender, EventArgs e)
        {
            btnDongY.Enabled = true;
        }

        private void FrmChonSinhVien_Load(object sender, EventArgs e)
        {
            btnDongY.Enabled = false;

            using (SqlConnection conn = db.GetConnection())
            {
                conn.Open();

                string sql = "SELECT MaSV, HoTen FROM SinhVien";

                SqlCommand cmd = new SqlCommand(sql, conn);
                SqlDataReader rd = cmd.ExecuteReader();

                while (rd.Read())
                {
                    cboSinhVien.Items.Add(
                        $"{rd["MaSV"]} - {rd["HoTen"]}"
                    );


                }
            }
        }
    }
}
