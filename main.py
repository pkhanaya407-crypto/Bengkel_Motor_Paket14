import json
from tkinter import Canvas, filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from datetime import date
import os
from koneksi import get_koneksi
from laporan import ModulLaporan

class AplikasiBengkel:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistem Manajemen Bengkel Motor - Paket 14")
        self.root.geometry("1150x680")

        # Keranjang sementara untuk sparepart saat transaksi servis
        self.keranjang_part = []

        # Header Aplikasi
        header = ttk.Frame(self.root, bootstyle="primary", padding=15)
        header.pack(fill="x")
        ttk.Label(header, text="SISTEM INFORMASI & TRANSAKSI BENGKEL MOTOR", 
                  font=("Helvetica", 16, "bold"), bootstyle="inverse-primary").pack(side=LEFT)

        # Tab Navigasi (Notebook)
        self.notebook = ttk.Notebook(self.root, bootstyle="primary")
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Inisialisasi Tab
        self.tab_dashboard = ttk.Frame(self.notebook, padding=10)
        self.tab_servis = ttk.Frame(self.notebook, padding=10)
        self.tab_pelanggan = ttk.Frame(self.notebook, padding=10)
        self.tab_mekanik = ttk.Frame(self.notebook, padding=10)
        self.tab_sparepart = ttk.Frame(self.notebook, padding=10)
        self.tab_laporan = ttk.Frame(self.notebook, padding=10)

        # Masukkan ke Notebook (Urutan Tab)
        self.notebook.add(self.tab_dashboard, text="Dashboard")
        self.notebook.add(self.tab_servis, text=" 1. Transaksi Servis & Nota ")
        self.notebook.add(self.tab_pelanggan, text=" 2. Data Pelanggan & Kendaraan ")
        self.notebook.add(self.tab_mekanik, text=" 3. Data Mekanik ")
        self.notebook.add(self.tab_sparepart, text=" 4. Data Suku Cadang ")
        self.notebook.add(self.tab_laporan, text=" 📊 5. Laporan ")

        self.setup_tab_dashboard()

        # Bangun isi masing-masing tab
        self.setup_tab_pelanggan()
        self.setup_tab_mekanik()
        self.setup_tab_sparepart()
        self.setup_tab_servis()

        # --- ISI TAMPILAN TAB LAPORAN ---
        frame_lap = ttk.Labelframe(self.tab_laporan, text="Cetak & Ekspor Laporan Bengkel", padding=20)
        frame_lap.pack(pady=30, padx=30, fill="x")
        
        ttk.Label(frame_lap, text="Pilih format laporan transaksi servis yang ingin diunduh:", font=("Helvetica", 11)).pack(anchor="w", pady=(0, 15))
        
        btn_excel = ttk.Button(
            frame_lap,
            text="📥 Ekspor Data Servis ke Excel (.xlsx)",
            bootstyle="success",
            command=lambda: ModulLaporan().ekspor_excel("servis")
        )
        btn_excel.pack(side="left", padx=(0, 15), ipadx=10, ipady=5)
        
        btn_pdf = ttk.Button(
            frame_lap,
            text="📄 Cetak Laporan Servis ke PDF (.pdf)",
            bootstyle="danger",
            command=lambda: ModulLaporan().ekspor_pdf("Laporan Data Servis Bengkel")
        )
        btn_pdf.pack(side="left", ipadx=10, ipady=5)
        # Muat semua data awal
        self.load_all_data()

    def setup_tab_dashboard(self):
        controls = ttk.Frame(self.tab_dashboard)
        controls.pack(fill="x", pady=(0, 10))
        ttk.Button(
            controls, text="Perbarui Statistik", bootstyle="primary",
            command=self.refresh_dashboard
        ).pack(side="left", padx=(0, 5))
        ttk.Button(
            controls, text="Backup Database", bootstyle="success",
            command=self.backup_database
        ).pack(side="left", padx=5)
        ttk.Button(
            controls, text="Restore Database", bootstyle="warning",
            command=self.restore_database
        ).pack(side="left", padx=5)

        self.dashboard_values = {}
        cards = ttk.Frame(self.tab_dashboard)
        cards.pack(fill="x", pady=(0, 10))
        stats = (
            ("Pelanggan", "pelanggan"),
            ("Kendaraan", "kendaraan"),
            ("Mekanik", "mekanik"),
            ("Suku Cadang", "sparepart"),
            ("Transaksi Servis", "servis"),
            ("Total Pendapatan", "pendapatan"),
        )
        for index, (title, key) in enumerate(stats):
            card = ttk.Labelframe(cards, text=title, padding=10)
            card.grid(row=index // 3, column=index % 3, sticky="nsew", padx=5, pady=5)
            value = ttk.Label(card, text="--", font=("Helvetica", 16, "bold"))
            value.pack()
            self.dashboard_values[key] = value
        for column in range(3):
            cards.columnconfigure(column, weight=1)

        self.dashboard_canvas = Canvas(
            self.tab_dashboard, height=300, background="white", highlightthickness=1,
            highlightbackground="#cccccc"
        )
        self.dashboard_canvas.pack(fill="both", expand=True, padx=5, pady=5)
        self.dashboard_canvas.bind("<Configure>", self.draw_dashboard_chart)

    def refresh_dashboard(self):
        conn = get_koneksi()
        if conn is None:
            return
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT "
                "(SELECT COUNT(*) FROM pelanggan), "
                "(SELECT COUNT(*) FROM kendaraan), "
                "(SELECT COUNT(*) FROM mekanik), "
                "(SELECT COUNT(*) FROM sparepart), "
                "(SELECT COUNT(*) FROM servis), "
                "(SELECT COALESCE(SUM(total_biaya), 0) FROM servis)"
            )
            row = cursor.fetchone()
            values = {
                "pelanggan": row[0],
                "kendaraan": row[1],
                "mekanik": row[2],
                "sparepart": row[3],
                "servis": row[4],
                "pendapatan": row[5],
            }
            for key, value in values.items():
                display = f"Rp {value:,}" if key == "pendapatan" else str(value)
                self.dashboard_values[key].configure(text=display)
            self.draw_dashboard_chart()
        except Exception as e:
            messagebox.showerror("Error Database", f"Gagal memuat statistik dashboard: {e}")
        finally:
            conn.close()

    def draw_dashboard_chart(self, _event=None):
        canvas = self.dashboard_canvas
        canvas.delete("all")
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width < 100 or height < 100:
            return

        chart_values = [
            ("Pelanggan", self.dashboard_values["pelanggan"].cget("text"), "#4e79a7"),
            ("Kendaraan", self.dashboard_values["kendaraan"].cget("text"), "#59a14f"),
            ("Mekanik", self.dashboard_values["mekanik"].cget("text"), "#f28e2b"),
            ("Suku Cadang", self.dashboard_values["sparepart"].cget("text"), "#e15759"),
            ("Servis", self.dashboard_values["servis"].cget("text"), "#b07aa1"),
        ]
        numeric_values = [
            int(value) if value.isdigit() else 0 for _, value, _ in chart_values
        ]
        max_value = max(numeric_values, default=0) or 1
        left, right, top, bottom = 55, width - 25, 35, height - 45
        canvas.create_text(
            left, 15, anchor="w", text="Jumlah Data", font=("Helvetica", 11, "bold")
        )
        canvas.create_line(left, top, left, bottom, fill="#666666")
        canvas.create_line(left, bottom, right, bottom, fill="#666666")

        slot_width = (right - left) / len(chart_values)
        chart_height = bottom - top
        for index, (label, _, color) in enumerate(chart_values):
            value = numeric_values[index]
            bar_height = chart_height * value / max_value
            x1 = left + index * slot_width + slot_width * 0.2
            x2 = left + (index + 1) * slot_width - slot_width * 0.2
            y1 = bottom - bar_height
            canvas.create_rectangle(x1, y1, x2, bottom, fill=color, outline="")
            canvas.create_text((x1 + x2) / 2, max(top - 10, y1 - 12), text=str(value))
            canvas.create_text(
                (x1 + x2) / 2, bottom + 18, text=label, font=("Helvetica", 9)
            )

    def setup_tab_pelanggan(self):
        notebook = ttk.Notebook(self.tab_pelanggan)
        notebook.pack(fill="both", expand=True)

        tab_data_pelanggan = ttk.Frame(notebook, padding=10)
        tab_data_kendaraan = ttk.Frame(notebook, padding=10)
        notebook.add(tab_data_pelanggan, text="Data Pelanggan")
        notebook.add(tab_data_kendaraan, text="Data Kendaraan")

        form_pelanggan = ttk.Labelframe(tab_data_pelanggan, text="Tambah Pelanggan", padding=10)
        form_pelanggan.pack(fill="x", pady=(0, 10))
        ttk.Label(form_pelanggan, text="Nama").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.ent_nama_pelanggan = ttk.Entry(form_pelanggan, width=35)
        self.ent_nama_pelanggan.grid(row=0, column=1, sticky="ew", padx=5, pady=4)
        ttk.Label(form_pelanggan, text="No. HP").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.ent_hp_pelanggan = ttk.Entry(form_pelanggan, width=35)
        self.ent_hp_pelanggan.grid(row=1, column=1, sticky="ew", padx=5, pady=4)
        ttk.Label(form_pelanggan, text="Alamat").grid(row=2, column=0, sticky="nw", padx=5, pady=4)
        self.txt_alamat_pelanggan = ttk.Text(form_pelanggan, width=35, height=3)
        self.txt_alamat_pelanggan.grid(row=2, column=1, sticky="ew", padx=5, pady=4)
        form_pelanggan.columnconfigure(1, weight=1)
        ttk.Button(
            form_pelanggan, text="Tambah Pelanggan", bootstyle="success",
            command=self.simpan_pelanggan
        ).grid(row=3, column=1, sticky="e", padx=5, pady=5)

        columns = ("id", "nama", "hp", "alamat")
        self.tree_pelanggan = ttk.Treeview(tab_data_pelanggan, columns=columns, show="headings")
        for column, title, width in (
            ("id", "ID", 60), ("nama", "Nama Pelanggan", 180),
            ("hp", "No. HP", 130), ("alamat", "Alamat", 300)
        ):
            self.tree_pelanggan.heading(column, text=title)
            self.tree_pelanggan.column(column, width=width)
        self.tree_pelanggan.pack(fill="both", expand=True)
        ttk.Button(
            tab_data_pelanggan, text="Hapus Pelanggan Terpilih", bootstyle="danger",
            command=self.hapus_pelanggan
        ).pack(anchor="e", pady=(8, 0))

        form_kendaraan = ttk.Labelframe(tab_data_kendaraan, text="Tambah Kendaraan", padding=10)
        form_kendaraan.pack(fill="x", pady=(0, 10))
        ttk.Label(form_kendaraan, text="Pemilik").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.combo_pemilik = ttk.Combobox(form_kendaraan, state="readonly", width=35)
        self.combo_pemilik.grid(row=0, column=1, sticky="ew", padx=5, pady=4)
        ttk.Label(form_kendaraan, text="No. Polisi").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.ent_no_polisi = ttk.Entry(form_kendaraan, width=35)
        self.ent_no_polisi.grid(row=1, column=1, sticky="ew", padx=5, pady=4)
        ttk.Label(form_kendaraan, text="Merk Motor").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        self.ent_merk_motor = ttk.Entry(form_kendaraan, width=35)
        self.ent_merk_motor.grid(row=2, column=1, sticky="ew", padx=5, pady=4)
        ttk.Label(form_kendaraan, text="Tipe Motor").grid(row=3, column=0, sticky="w", padx=5, pady=4)
        self.ent_tipe_motor = ttk.Entry(form_kendaraan, width=35)
        self.ent_tipe_motor.grid(row=3, column=1, sticky="ew", padx=5, pady=4)
        form_kendaraan.columnconfigure(1, weight=1)
        ttk.Button(
            form_kendaraan, text="Tambah Kendaraan", bootstyle="success",
            command=self.simpan_kendaraan
        ).grid(row=4, column=1, sticky="e", padx=5, pady=5)

        columns = ("nopol", "pemilik", "merk", "tipe")
        self.tree_kendaraan = ttk.Treeview(tab_data_kendaraan, columns=columns, show="headings")
        for column, title, width in (
            ("nopol", "No. Polisi", 120), ("pemilik", "Pemilik", 200),
            ("merk", "Merk Motor", 150), ("tipe", "Tipe Motor", 150)
        ):
            self.tree_kendaraan.heading(column, text=title)
            self.tree_kendaraan.column(column, width=width)
        self.tree_kendaraan.pack(fill="both", expand=True)
        ttk.Button(
            tab_data_kendaraan, text="Hapus Kendaraan Terpilih", bootstyle="danger",
            command=self.hapus_kendaraan
        ).pack(anchor="e", pady=(8, 0))

        self.load_pelanggan()
        self.load_combo_pelanggan()
        self.load_kendaraan()

    def load_pelanggan(self):
        for item in self.tree_pelanggan.get_children():
            self.tree_pelanggan.delete(item)
        conn = get_koneksi()
        if conn is None:
            return
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id_pelanggan, nama_pelanggan, no_hp, alamat "
                "FROM pelanggan ORDER BY id_pelanggan"
            )
            for row in cursor.fetchall():
                self.tree_pelanggan.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Error Database", f"Gagal memuat data pelanggan: {e}")
        finally:
            conn.close()

    def simpan_pelanggan(self):
        nama = self.ent_nama_pelanggan.get().strip()
        no_hp = self.ent_hp_pelanggan.get().strip()
        alamat = self.txt_alamat_pelanggan.get("1.0", "end-1c").strip()
        if not nama or not no_hp:
            messagebox.showerror("Data Belum Lengkap", "Nama dan no. HP wajib diisi.")
            return

        conn = get_koneksi()
        if conn is None:
            return
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO pelanggan (nama_pelanggan, no_hp, alamat) VALUES (%s, %s, %s)",
                (nama, no_hp, alamat)
            )
            conn.commit()
            self.ent_nama_pelanggan.delete(0, "end")
            self.ent_hp_pelanggan.delete(0, "end")
            self.txt_alamat_pelanggan.delete("1.0", "end")
            self.load_pelanggan()
            self.load_combo_pelanggan()
            self.refresh_dashboard()
            messagebox.showinfo("Sukses", "Data pelanggan berhasil ditambahkan.")
        except Exception as e:
            messagebox.showerror("Error Database", f"Gagal menyimpan pelanggan: {e}")
        finally:
            conn.close()

    def hapus_pelanggan(self):
        selected = self.tree_pelanggan.selection()
        if not selected:
            messagebox.showwarning("Peringatan", "Pilih pelanggan yang akan dihapus.")
            return
        if not messagebox.askyesno(
            "Konfirmasi", "Hapus pelanggan terpilih beserta kendaraannya?"
        ):
            return

        pelanggan_id = self.tree_pelanggan.item(selected[0], "values")[0]
        conn = get_koneksi()
        if conn is None:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pelanggan WHERE id_pelanggan = %s", (pelanggan_id,))
            conn.commit()
            self.load_pelanggan()
            self.load_combo_pelanggan()
            self.load_kendaraan()
            self.load_combo_kendaraan()
            self.refresh_dashboard()
            messagebox.showinfo("Sukses", "Data pelanggan berhasil dihapus.")
        except Exception as e:
            messagebox.showerror("Error Database", f"Gagal menghapus pelanggan: {e}")
        finally:
            conn.close()

    def load_combo_pelanggan(self):
        conn = get_koneksi()
        if conn is None:
            return
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id_pelanggan, nama_pelanggan FROM pelanggan ORDER BY nama_pelanggan"
            )
            rows = cursor.fetchall()
            self._pelanggan_ids = {f"{row[0]} - {row[1]}": row[0] for row in rows}
            self.combo_pemilik["values"] = list(self._pelanggan_ids)
        except Exception as e:
            messagebox.showerror("Error Database", f"Gagal memuat daftar pemilik: {e}")
        finally:
            conn.close()

    def load_kendaraan(self):
        for item in self.tree_kendaraan.get_children():
            self.tree_kendaraan.delete(item)
        conn = get_koneksi()
        if conn is None:
            return
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT k.no_polisi, p.nama_pelanggan, k.merk_motor, k.tipe_motor "
                "FROM kendaraan k JOIN pelanggan p ON p.id_pelanggan = k.id_pelanggan "
                "ORDER BY k.no_polisi"
            )
            for row in cursor.fetchall():
                self.tree_kendaraan.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Error Database", f"Gagal memuat data kendaraan: {e}")
        finally:
            conn.close()

    def simpan_kendaraan(self):
        pemilik = self.combo_pemilik.get()
        no_polisi = self.ent_no_polisi.get().strip().upper()
        merk = self.ent_merk_motor.get().strip()
        tipe = self.ent_tipe_motor.get().strip()
        if not pemilik or not no_polisi or not merk or not tipe:
            messagebox.showerror("Data Belum Lengkap", "Semua data kendaraan wajib diisi.")
            return

        conn = get_koneksi()
        if conn is None:
            return
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO kendaraan (no_polisi, id_pelanggan, merk_motor, tipe_motor) "
                "VALUES (%s, %s, %s, %s)",
                (no_polisi, self._pelanggan_ids[pemilik], merk, tipe)
            )
            conn.commit()
            self.ent_no_polisi.delete(0, "end")
            self.ent_merk_motor.delete(0, "end")
            self.ent_tipe_motor.delete(0, "end")
            self.load_kendaraan()
            self.load_combo_kendaraan()
            self.refresh_dashboard()
            messagebox.showinfo("Sukses", "Data kendaraan berhasil ditambahkan.")
        except Exception as e:
            messagebox.showerror("Error Database", f"Gagal menyimpan kendaraan: {e}")
        finally:
            conn.close()

    def hapus_kendaraan(self):
        selected = self.tree_kendaraan.selection()
        if not selected:
            messagebox.showwarning("Peringatan", "Pilih kendaraan yang akan dihapus.")
            return
        if not messagebox.askyesno("Konfirmasi", "Hapus kendaraan terpilih?"):
            return

        no_polisi = self.tree_kendaraan.item(selected[0], "values")[0]
        conn = get_koneksi()
        if conn is None:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM kendaraan WHERE no_polisi = %s", (no_polisi,))
            conn.commit()
            self.load_kendaraan()
            self.load_combo_kendaraan()
            self.refresh_dashboard()
            messagebox.showinfo("Sukses", "Data kendaraan berhasil dihapus.")
        except Exception as e:
            messagebox.showerror("Error Database", f"Gagal menghapus kendaraan: {e}")
        finally:
            conn.close()

    def setup_tab_mekanik(self):
        form = ttk.Labelframe(self.tab_mekanik, text="Tambah Mekanik", padding=10)
        form.pack(fill="x", pady=(0, 10))
        ttk.Label(form, text="Nama Mekanik").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.ent_nama_mekanik = ttk.Entry(form, width=35)
        self.ent_nama_mekanik.grid(row=0, column=1, sticky="ew", padx=5, pady=4)
        ttk.Label(form, text="Spesialisasi").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.ent_spesialisasi = ttk.Entry(form, width=35)
        self.ent_spesialisasi.grid(row=1, column=1, sticky="ew", padx=5, pady=4)
        form.columnconfigure(1, weight=1)
        ttk.Button(
            form, text="Tambah Mekanik", bootstyle="success",
            command=self.simpan_mekanik
        ).grid(row=2, column=1, sticky="e", padx=5, pady=5)

        columns = ("id", "nama", "spesialisasi")
        self.tree_mekanik = ttk.Treeview(self.tab_mekanik, columns=columns, show="headings")
        for column, title, width in (
            ("id", "ID", 60), ("nama", "Nama Mekanik", 220),
            ("spesialisasi", "Spesialisasi", 260)
        ):
            self.tree_mekanik.heading(column, text=title)
            self.tree_mekanik.column(column, width=width)
        self.tree_mekanik.pack(fill="both", expand=True)
        ttk.Button(
            self.tab_mekanik, text="Hapus Mekanik Terpilih", bootstyle="danger",
            command=self.hapus_mekanik
        ).pack(anchor="e", pady=(8, 0))
        self.load_mekanik()

    def load_mekanik(self):
        for item in self.tree_mekanik.get_children():
            self.tree_mekanik.delete(item)
        conn = get_koneksi()
        if conn is None:
            return
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id_mekanik, nama_mekanik, spesialisasi "
                "FROM mekanik ORDER BY id_mekanik"
            )
            for row in cursor.fetchall():
                self.tree_mekanik.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Error Database", f"Gagal memuat data mekanik: {e}")
        finally:
            conn.close()

    def simpan_mekanik(self):
        nama = self.ent_nama_mekanik.get().strip()
        spesialisasi = self.ent_spesialisasi.get().strip()
        if not nama:
            messagebox.showerror("Data Belum Lengkap", "Nama mekanik wajib diisi.")
            return

        conn = get_koneksi()
        if conn is None:
            return
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO mekanik (nama_mekanik, spesialisasi) VALUES (%s, %s)",
                (nama, spesialisasi)
            )
            conn.commit()
            self.ent_nama_mekanik.delete(0, "end")
            self.ent_spesialisasi.delete(0, "end")
            self.load_mekanik()
            self.load_combo_mekanik()
            self.refresh_dashboard()
            messagebox.showinfo("Sukses", "Data mekanik berhasil ditambahkan.")
        except Exception as e:
            messagebox.showerror("Error Database", f"Gagal menyimpan mekanik: {e}")
        finally:
            conn.close()

    def hapus_mekanik(self):
        selected = self.tree_mekanik.selection()
        if not selected:
            messagebox.showwarning("Peringatan", "Pilih mekanik yang akan dihapus.")
            return
        if not messagebox.askyesno("Konfirmasi", "Hapus mekanik terpilih?"):
            return

        mekanik_id = self.tree_mekanik.item(selected[0], "values")[0]
        conn = get_koneksi()
        if conn is None:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM mekanik WHERE id_mekanik = %s", (mekanik_id,))
            conn.commit()
            self.load_mekanik()
            self.load_combo_mekanik()
            self.refresh_dashboard()
            messagebox.showinfo("Sukses", "Data mekanik berhasil dihapus.")
        except Exception as e:
            messagebox.showerror("Error Database", f"Gagal menghapus mekanik: {e}")
        finally:
            conn.close()

    def setup_tab_sparepart(self):
        form = ttk.Labelframe(self.tab_sparepart, text="Tambah Suku Cadang", padding=10)
        form.pack(fill="x", pady=(0, 10))
        ttk.Label(form, text="Kode Part").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.ent_kode_part = ttk.Entry(form, width=35)
        self.ent_kode_part.grid(row=0, column=1, sticky="ew", padx=5, pady=4)
        ttk.Label(form, text="Nama Part").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.ent_nama_part = ttk.Entry(form, width=35)
        self.ent_nama_part.grid(row=1, column=1, sticky="ew", padx=5, pady=4)
        ttk.Label(form, text="Stok").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        self.ent_stok_part = ttk.Entry(form, width=35)
        self.ent_stok_part.grid(row=2, column=1, sticky="ew", padx=5, pady=4)
        ttk.Label(form, text="Harga (Rp)").grid(row=3, column=0, sticky="w", padx=5, pady=4)
        self.ent_harga_part = ttk.Entry(form, width=35)
        self.ent_harga_part.grid(row=3, column=1, sticky="ew", padx=5, pady=4)
        form.columnconfigure(1, weight=1)
        ttk.Button(
            form, text="Tambah Suku Cadang", bootstyle="success",
            command=self.simpan_sparepart
        ).grid(row=4, column=1, sticky="e", padx=5, pady=5)

        columns = ("kode", "nama", "stok", "harga")
        self.tree_sparepart = ttk.Treeview(self.tab_sparepart, columns=columns, show="headings")
        for column, title, width in (
            ("kode", "Kode Part", 100), ("nama", "Nama Part", 250),
            ("stok", "Stok", 80), ("harga", "Harga (Rp)", 120)
        ):
            self.tree_sparepart.heading(column, text=title)
            self.tree_sparepart.column(column, width=width)
        self.tree_sparepart.pack(fill="both", expand=True)
        ttk.Button(
            self.tab_sparepart, text="Hapus Suku Cadang Terpilih", bootstyle="danger",
            command=self.hapus_sparepart
        ).pack(anchor="e", pady=(8, 0))
        self.load_sparepart()

    def load_sparepart(self):
        for item in self.tree_sparepart.get_children():
            self.tree_sparepart.delete(item)
        conn = get_koneksi()
        if conn is None:
            return
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT kode_part, nama_part, stok, harga FROM sparepart ORDER BY kode_part"
            )
            for row in cursor.fetchall():
                self.tree_sparepart.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Error Database", f"Gagal memuat data suku cadang: {e}")
        finally:
            conn.close()

    def simpan_sparepart(self):
        kode = self.ent_kode_part.get().strip().upper()
        nama = self.ent_nama_part.get().strip()
        try:
            stok = int(self.ent_stok_part.get().strip())
            harga = int(self.ent_harga_part.get().strip())
            if stok < 0 or harga < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Data Tidak Valid", "Stok dan harga harus bilangan bulat >= 0.")
            return
        if not kode or not nama:
            messagebox.showerror("Data Belum Lengkap", "Kode dan nama suku cadang wajib diisi.")
            return

        conn = get_koneksi()
        if conn is None:
            return
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sparepart (kode_part, nama_part, stok, harga) "
                "VALUES (%s, %s, %s, %s)",
                (kode, nama, stok, harga)
            )
            conn.commit()
            self.ent_kode_part.delete(0, "end")
            self.ent_nama_part.delete(0, "end")
            self.ent_stok_part.delete(0, "end")
            self.ent_harga_part.delete(0, "end")
            self.load_sparepart()
            self.refresh_dashboard()
            messagebox.showinfo("Sukses", "Data suku cadang berhasil ditambahkan.")
        except Exception as e:
            messagebox.showerror("Error Database", f"Gagal menyimpan suku cadang: {e}")
        finally:
            conn.close()

    def hapus_sparepart(self):
        selected = self.tree_sparepart.selection()
        if not selected:
            messagebox.showwarning("Peringatan", "Pilih suku cadang yang akan dihapus.")
            return
        if not messagebox.askyesno("Konfirmasi", "Hapus suku cadang terpilih?"):
            return

        kode = self.tree_sparepart.item(selected[0], "values")[0]
        conn = get_koneksi()
        if conn is None:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sparepart WHERE kode_part = %s", (kode,))
            conn.commit()
            self.load_sparepart()
            self.refresh_dashboard()
            messagebox.showinfo("Sukses", "Data suku cadang berhasil dihapus.")
        except Exception as e:
            messagebox.showerror("Error Database", f"Gagal menghapus suku cadang: {e}")
        finally:
            conn.close()

    def setup_tab_servis(self):
        # Frame Utama Tab Servis (Dibagi menjadi 2 Kolom: Form Input & Riwayat)
        frame_kiri = ttk.Labelframe(self.tab_servis, text="Input Pencatatan Servis", padding=15)
        frame_kiri.pack(side="left", fill="both", expand=False, padx=5, pady=5)

        frame_kanan = ttk.Labelframe(self.tab_servis, text="Riwayat Transaksi Servis", padding=15)
        frame_kanan.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        # --- KOLOM KIRI: FORM INPUT ---
        ttk.Label(frame_kiri, text="Pilih Kendaraan (No. Polisi):").pack(anchor="w", pady=(0, 2))
        self.combo_kendaraan = ttk.Combobox(frame_kiri, width=30, state="readonly")
        self.combo_kendaraan.pack(anchor="w", pady=(0, 10))
        self.load_combo_kendaraan()

        ttk.Label(frame_kiri, text="Pilih Mekanik:").pack(anchor="w", pady=(0, 2))
        self.combo_mekanik = ttk.Combobox(frame_kiri, width=30, state="readonly")
        self.combo_mekanik.pack(anchor="w", pady=(0, 10))
        self.load_combo_mekanik()

        ttk.Label(frame_kiri, text="Keluhan / Pekerjaan Servis:").pack(anchor="w", pady=(0, 2))
        self.txt_keluhan = ttk.Text(frame_kiri, width=32, height=3)
        self.txt_keluhan.pack(anchor="w", pady=(0, 10))

        ttk.Label(frame_kiri, text="Biaya Jasa Mekanik (Rp):").pack(anchor="w", pady=(0, 2))
        self.ent_biaya_jasa = ttk.Entry(frame_kiri, width=32)
        self.ent_biaya_jasa.insert(0, "0")
        self.ent_biaya_jasa.pack(anchor="w", pady=(0, 15))

        # Tombol Simpan Transaksi & Cetak Nota
        btn_simpan_servis = ttk.Button(
            frame_kiri, 
            text="💾 SIMPAN TRANSAKSI & CETAK NOTA", 
            bootstyle="success",
            command=self.simpan_transaksi_servis
        )
        btn_simpan_servis.pack(fill="x", ipady=5)

        # --- KOLOM KANAN: TABEL RIWAYAT TRANSAKSI ---
        columns = ("id", "tanggal", "nopol", "pelanggan", "mekanik", "keluhan", "total")
        self.tree_servis = ttk.Treeview(frame_kanan, columns=columns, show="headings", height=18)
        
        self.tree_servis.heading("id", text="ID")
        self.tree_servis.heading("tanggal", text="Tanggal")
        self.tree_servis.heading("nopol", text="No. Polisi")
        self.tree_servis.heading("pelanggan", text="Pelanggan")
        self.tree_servis.heading("mekanik", text="Mekanik")
        self.tree_servis.heading("keluhan", text="Keluhan")
        self.tree_servis.heading("total", text="Total Biaya")

        self.tree_servis.column("id", width=40, anchor="center")
        self.tree_servis.column("tanggal", width=90, anchor="center")
        self.tree_servis.column("nopol", width=80, anchor="center")
        self.tree_servis.column("pelanggan", width=110)
        self.tree_servis.column("mekanik", width=110)
        self.tree_servis.column("keluhan", width=130)
        self.tree_servis.column("total", width=90, anchor="e")

        scrollbar = ttk.Scrollbar(frame_kanan, orient="vertical", command=self.tree_servis.yview)
        self.tree_servis.configure(yscrollcommand=scrollbar.set)
        
        self.tree_servis.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Tombol Cetak Ulang Nota Terpilih
        btn_cetak_ulang = ttk.Button(
            frame_kanan,
            text="📄 Cetak Ulang Nota Terpilih (.txt)",
            bootstyle="info",
            command=self.cetak_ulang_nota
        )
        btn_cetak_ulang.pack(fill="x", pady=(10, 0))

    def load_combo_kendaraan(self):
        try:
            conn = get_koneksi()
            cursor = conn.cursor()
            cursor.execute("SELECT kendaraan.no_polisi, pelanggan.nama_pelanggan, kendaraan.merk_motor FROM kendaraan JOIN pelanggan ON kendaraan.id_pelanggan = pelanggan.id_pelanggan")
            data = cursor.fetchall()
            conn.close()
            
            list_item = [f"{row[0]} - {row[1]} ({row[2]})" for row in data]
            self.combo_kendaraan['values'] = list_item
        except Exception as e:
            pass

    def load_combo_mekanik(self):
        try:
            conn = get_koneksi()
            cursor = conn.cursor()
            cursor.execute("SELECT id_mekanik, nama_mekanik FROM mekanik")
            data = cursor.fetchall()
            conn.close()
            
            list_item = [f"{row[0]} - {row[1]}" for row in data]
            self.combo_mekanik['values'] = list_item
        except Exception as e:
            pass

    def load_all_data(self):
        # Memuat data riwayat servis ke tabel
        try:
            for item in self.tree_servis.get_children():
                self.tree_servis.delete(item)
                
            conn = get_koneksi()
            cursor = conn.cursor()
            query = """
                SELECT servis.id_servis, servis.tanggal, servis.no_polisi, pelanggan.nama_pelanggan, 
                       mekanik.nama_mekanik, servis.keluhan, servis.total_biaya 
                FROM servis 
                JOIN kendaraan ON servis.no_polisi = kendaraan.no_polisi
                JOIN pelanggan ON kendaraan.id_pelanggan = pelanggan.id_pelanggan
                JOIN mekanik ON servis.id_mekanik = mekanik.id_mekanik
            """
            cursor.execute(query)
            for row in cursor.fetchall():
                self.tree_servis.insert("", "end", values=(row[0], row[1], row[2], row[3], row[4], row[5], f"Rp {row[6]:,}"))
            conn.close()
        except Exception as e:
            pass

    def simpan_transaksi_servis(self):
        try:
            selected_kendaraan = self.combo_kendaraan.get()
            selected_mekanik = self.combo_mekanik.get()
            keluhan = self.txt_keluhan.get("1.0", "end-1c").strip()
            biaya_jasa_str = self.ent_biaya_jasa.get().strip()

            if not selected_kendaraan or not selected_mekanik or not biaya_jasa_str:
                messagebox.showerror("Error", "Semua data wajib diisi!")
                return

            nopol = selected_kendaraan.split(" - ")[0]
            id_mekanik = selected_mekanik.split(" - ")[0]
            biaya_jasa = int(biaya_jasa_str)
            tgl_hari_ini = date.today().strftime("%Y-%m-%d")

            conn = get_koneksi()
            cursor = conn.cursor()
            
            # Simpan ke tabel servis
            query_servis = "INSERT INTO servis (tanggal, no_polisi, id_mekanik, keluhan, biaya_jasa, total_biaya) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(query_servis, (tgl_hari_ini, nopol, id_mekanik, keluhan, biaya_jasa, biaya_jasa))
            conn.commit()
            
            id_servis_baru = cursor.lastrowid
            conn.close()

            messagebox.StatusOK if hasattr(messagebox, 'StatusOK') else messagebox.showinfo("Sukses", "Transaksi servis berhasil disimpan!")
            self.load_all_data()
            
            # Buat file nota otomatis
            self.generate_nota_file(id_servis_baru)

        except Exception as e:
            messagebox.showerror("Error Database", f"Terjadi kesalahan: {e}")

    def generate_nota_file(self, id_servis):
        try:
            conn = get_koneksi()
            cursor = conn.cursor()
            query = """
                SELECT s.id_servis, s.tanggal, p.nama_pelanggan, k.merk_motor, k.tipe_motor, s.no_polisi, 
                       m.nama_mekanik, s.keluhan, s.biaya_jasa, s.total_biaya
                FROM servis s
                JOIN kendaraan k ON s.no_polisi = k.no_polisi
                JOIN pelanggan p ON k.id_pelanggan = p.id_pelanggan
                JOIN mekanik m ON s.id_mekanik = m.id_mekanik
                WHERE s.id_servis = %s
            """
            cursor.execute(query, (id_servis,))
            data = cursor.fetchone()
            conn.close()

            if data:
                nama_file = f"Nota_Servis_{id_servis}.txt"
                with open(nama_file, "w") as f:
                    f.write("========================================\n")
                    f.write("          NOTA SERVIS BENGKEL MOTOR     \n")
                    f.write("========================================\n")
                    f.write(f"No. Nota  : SRV-{data[0]:04d}\n")
                    f.write(f"Tanggal   : {data[1]}\n")
                    f.write(f"Pelanggan : {data[2]}\n")
                    f.write(f"Kendaraan : {data[5]} ({data[3]} {data[4]})\n")
                    f.write(f"Mekanik   : {data[6]}\n")
                    f.write(f"Keluhan   : {data[7]}\n")
                    f.write("----------------------------------------\n")
                    f.write("RINCIAN BIAYA:\n")
                    f.write(f"Jasa Servis Mekanik       : Rp {data[8]:,}\n")
                    f.write("----------------------------------------\n")
                    f.write(f"TOTAL BAYAR               : Rp {data[9]:,}\n")
                    f.write("========================================\n")
                    f.write("     Terima Kasih Atas Kunjungan Anda!  \n")
                
                if os.name == 'nt':
                    os.startfile(nama_file)
        except Exception as e:
            pass

    def cetak_ulang_nota(self):
        selected = self.tree_servis.selection()
        if not selected:
            messagebox.showwarning("Peringatan", "Pilih data transaksi servis terlebih dahulu dari tabel!")
            return
        item_data = self.tree_servis.item(selected[0])['values']
        id_servis = item_data[0]
        self.generate_nota_file(id_servis)

    def backup_database(self):
        backup_path = filedialog.asksaveasfilename(
            title="Simpan Backup Database",
            defaultextension=".json",
            filetypes=[("Backup Bengkel (*.json)", "*.json")]
        )
        if not backup_path:
            return

        table_columns = {
            "pelanggan": ("id_pelanggan", "nama_pelanggan", "no_hp", "alamat"),
            "kendaraan": ("no_polisi", "id_pelanggan", "merk_motor", "tipe_motor"),
            "mekanik": ("id_mekanik", "nama_mekanik", "spesialisasi"),
            "sparepart": ("kode_part", "nama_part", "stok", "harga"),
            "servis": (
                "id_servis", "tanggal", "no_polisi", "id_mekanik",
                "keluhan", "biaya_jasa", "total_biaya"
            ),
            "detail_servis": (
                "id_detail", "id_servis", "kode_part", "jumlah", "subtotal"
            ),
        }
        conn = get_koneksi()
        if conn is None:
            return

        try:
            cursor = conn.cursor()
            tables = {}
            for table, columns in table_columns.items():
                cursor.execute(f"SELECT {', '.join(columns)} FROM {table}")
                tables[table] = [
                    dict(zip(columns, row)) for row in cursor.fetchall()
                ]
        except Exception as e:
            messagebox.showerror("Backup Gagal", f"Gagal membaca data database: {e}")
            return
        finally:
            conn.close()

        backup = {
            "format": "bengkel-motor-backup",
            "version": 1,
            "tables": tables,
        }
        try:
            with open(backup_path, "w", encoding="utf-8") as file:
                json.dump(backup, file, ensure_ascii=False, indent=2, default=str)
            messagebox.showinfo("Backup Berhasil", f"Backup tersimpan di:\n{backup_path}")
        except OSError as e:
            messagebox.showerror("Backup Gagal", f"Gagal menyimpan file backup: {e}")

    def restore_database(self):
        backup_path = filedialog.askopenfilename(
            title="Pilih File Backup",
            filetypes=[("Backup Bengkel (*.json)", "*.json")]
        )
        if not backup_path:
            return

        table_columns = {
            "pelanggan": ("id_pelanggan", "nama_pelanggan", "no_hp", "alamat"),
            "kendaraan": ("no_polisi", "id_pelanggan", "merk_motor", "tipe_motor"),
            "mekanik": ("id_mekanik", "nama_mekanik", "spesialisasi"),
            "sparepart": ("kode_part", "nama_part", "stok", "harga"),
            "servis": (
                "id_servis", "tanggal", "no_polisi", "id_mekanik",
                "keluhan", "biaya_jasa", "total_biaya"
            ),
            "detail_servis": (
                "id_detail", "id_servis", "kode_part", "jumlah", "subtotal"
            ),
        }
        try:
            with open(backup_path, "r", encoding="utf-8") as file:
                backup = json.load(file)
            if (
                backup.get("format") != "bengkel-motor-backup"
                or backup.get("version") != 1
                or not isinstance(backup.get("tables"), dict)
            ):
                raise ValueError("Format file bukan backup aplikasi Bengkel Motor.")

            tables = backup["tables"]
            for table, columns in table_columns.items():
                rows = tables.get(table)
                if not isinstance(rows, list):
                    raise ValueError(f"Data tabel {table} tidak ditemukan atau tidak valid.")
                for row in rows:
                    if not isinstance(row, dict) or set(row) != set(columns):
                        raise ValueError(f"Struktur data tabel {table} tidak valid.")
        except (OSError, json.JSONDecodeError, ValueError, AttributeError) as e:
            messagebox.showerror("Restore Gagal", f"File backup tidak valid:\n{e}")
            return

        row_count = sum(len(tables[table]) for table in table_columns)
        if not messagebox.askyesno(
            "Konfirmasi Restore",
            f"Gabungkan {row_count} baris dari backup ke database saat ini?\n\n"
            "Data yang sudah memiliki primary key sama akan dilewati, "
            "bukan ditimpa."
        ):
            return

        conn = get_koneksi()
        if conn is None:
            return
        added = 0
        skipped = 0
        try:
            cursor = conn.cursor()
            for table, columns in table_columns.items():
                column_sql = ", ".join(columns)
                placeholders = ", ".join(["%s"] * len(columns))
                query = f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders})"
                for row in tables[table]:
                    try:
                        cursor.execute(query, tuple(row[column] for column in columns))
                        added += 1
                    except Exception as e:
                        if getattr(e, "errno", None) == 1062:
                            skipped += 1
                        else:
                            raise
            conn.commit()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Restore Gagal", f"Data backup tidak dapat digabungkan: {e}")
            return
        finally:
            conn.close()

        self.load_pelanggan()
        self.load_combo_pelanggan()
        self.load_kendaraan()
        self.load_combo_kendaraan()
        self.load_mekanik()
        self.load_combo_mekanik()
        self.load_sparepart()
        self.load_all_data()
        self.refresh_dashboard()
        messagebox.showinfo(
            "Restore Selesai",
            f"Data baru ditambahkan: {added}\nData duplikat dilewati: {skipped}"
        )

if __name__ == "__main__":
    root = ttk.Window(themename="cosmo")
    app = AplikasiBengkel(root)
    root.mainloop()