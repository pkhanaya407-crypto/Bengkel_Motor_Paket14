import mysql.connector
from tkinter import messagebox

def get_koneksi():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="", # Kosongkan jika menggunakan XAMPP default
            database="db_bengkel_motor"
        )
        return conn
    except mysql.connector.Error as err:
        messagebox.showerror("Error Database", f"Gagal terhubung ke MySQL:\n{err}\n\nPastikan XAMPP (MySQL) sudah dijalankan!")
        return Nonepython