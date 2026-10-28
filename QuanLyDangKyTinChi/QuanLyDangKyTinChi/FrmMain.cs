using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace QuanLyDangKyTinChi
{
    public partial class FrmMain : Form
    {
        public FrmMain()
        {
            InitializeComponent();
        }

        private void btnSinhVien_Click(object sender, EventArgs e)
        {
            FrmChonSinhVien frm = new FrmChonSinhVien();
            frm.Show();

            this.Hide();
        }

        private void button1_Click(object sender, EventArgs e)
        {
            FrmNhaTruong frm = new FrmNhaTruong();
            frm.Show();
            this.Hide();
        }
    }
}
