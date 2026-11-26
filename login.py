import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from koneksi import get_koneksi
import subprocess
import sys

class JendelaLogin:
    def __init__(self, root):
        self.root = root
        self.root.title("Login - Sistem Bengkel Motor")
        self.root.geometry("400x350")
        self.root.resizable(False, False)
        
        # Judul Form
        title_lbl = ttk.Label(root, text="LOGIN BENGKEL MOTOR", font=("Helvetica", 16, "bold"), bootstyle="primary")
        title_lbl.pack(pady=30)
        
        # Frame Input
        form_frame = ttk.Frame(root)
        form_frame.pack(pady=10, padx=30, fill="x")
        
        ttk.Label(form_frame, text="Username:", font=("Helvetica", 10)).pack(anchor="w")
        self.entry_user = ttk.Entry(form_frame, font=("Helvetica", 11))
        self.entry_user.pack(fill="x", pady=(5, 15))
        
        ttk.Label(form_frame, text="Password:", font=("Helvetica", 10)).pack(anchor="w")
        self.entry_pass = ttk.Entry(form_frame, font=("Helvetica", 11), show="*")
        self.entry_pass.pack(fill="x", pady=(5, 15))
        
        # Tombol Login
        btn_login = ttk.Button(root, text="Masuk", bootstyle="success", command=self.proses_login)
        btn_login.pack(pady=10, ipadx=20)

    def proses_login(self):
        user = self.entry_user.get()
        pwd = self.entry_pass.get()
        
        if user == "" or pwd == "":
            messagebox.showerror("Error", "Username dan Password tidak boleh kosong!")
            return
            
        conn = get_koneksi()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                query = "SELECT * FROM user WHERE username = %s AND password = %s"
                cursor.execute(query, (user, pwd))
                result = cursor.fetchone()
                
                if result:
                    messagebox.showinfo("Sukses", f"Login Berhasil! Selamat datang, {result['username']} ({result['level']})")
                    self.root.destroy()
                    subprocess.Popen([sys.executable, "main.py"])
                else:
                    messagebox.showerror("Gagal", "Username atau Password salah!")
            except Exception as e:
                messagebox.showerror("Error Database", str(e))
            finally:
                conn.close()

if __name__ == "__main__":
    app = ttk.Window(themename="cosmo")
    JendelaLogin(app)
    app.mainloop()