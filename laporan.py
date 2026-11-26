import pandas as pd
from tkinter import messagebox
import tkinter.filedialog as fd
from koneksi import get_koneksi
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from xml.sax.saxutils import escape

class ModulLaporan:
    def __init__(self):
        pass

    def ekspor_excel(self, nama_tabel="servis"):
        print("Fungsi ekspor_excel dipanggil!")
        conn = get_koneksi()
        if conn:
            try:
                query = f"SELECT * FROM {nama_tabel}"
                df = pd.read_sql(query, conn)
                
                file_path = fd.asksaveasfilename(
                    defaultextension=".xlsx", 
                    filetypes=[("Excel files", "*.xlsx")],
                    title=f"Simpan Laporan {nama_tabel} ke Excel"
                )
                
                if file_path:
                    df.to_excel(file_path, index=False)
                    messagebox.showinfo("Sukses", f"Laporan berhasil diekspor ke:\n{file_path}")
            except Exception as e:
                print(f"Error Excel: {e}")
                messagebox.showerror("Error", f"Gagal mengekspor Excel: {e}")
            finally:
                conn.close()
        else:
            print("Koneksi database gagal!")

    def ekspor_pdf(self, judul_laporan="Laporan Servis Bengkel"):
        print("Fungsi ekspor_pdf dipanggil!")
        file_path = fd.asksaveasfilename(
            defaultextension=".pdf", 
            filetypes=[("PDF files", "*.pdf")],
            title="Simpan Laporan PDF"
        )
        if not file_path:
            return

        conn = get_koneksi()
        if conn is None:
            return

        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT s.id_servis, s.tanggal, s.no_polisi, p.nama_pelanggan, "
                "m.nama_mekanik, s.total_biaya "
                "FROM servis s "
                "JOIN kendaraan k ON k.no_polisi = s.no_polisi "
                "JOIN pelanggan p ON p.id_pelanggan = k.id_pelanggan "
                "JOIN mekanik m ON m.id_mekanik = s.id_mekanik "
                "ORDER BY s.tanggal DESC, s.id_servis DESC"
            )
            data_servis = cursor.fetchall()
        except Exception as e:
            print(f"Error PDF: {e}")
            messagebox.showerror("Error", f"Gagal mengambil data laporan: {e}")
            return
        finally:
            conn.close()

        try:
            styles = getSampleStyleSheet()
            cell_style = ParagraphStyle(
                "ReportCell", parent=styles["BodyText"], fontName="Helvetica",
                fontSize=8, leading=10
            )
            header_style = ParagraphStyle(
                "ReportHeader", parent=cell_style, fontName="Helvetica-Bold",
                textColor=colors.white
            )
            title = Paragraph("BENGKEL MOTOR - LAPORAN RESMI", styles["Title"])
            subtitle = Paragraph(escape(judul_laporan), styles["Heading2"])
            table_data = [[
                Paragraph(label, header_style)
                for label in ("ID Servis", "Tanggal", "No. Polisi", "Pelanggan", "Mekanik", "Total Biaya")
            ]]
            for row in data_servis:
                table_data.append([
                    Paragraph(escape(str(value if value is not None else "-")), cell_style)
                    for value in row[:5]
                ] + [
                    Paragraph(f"Rp {row[5]:,}", cell_style)
                ])

            report = SimpleDocTemplate(
                file_path, pagesize=letter, leftMargin=36, rightMargin=36,
                topMargin=36, bottomMargin=36, title=judul_laporan
            )
            table = Table(
                table_data, colWidths=(36, 68, 68, 120, 110, 138), repeatRows=1
            )
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#24527a")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b7c9d6")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), (colors.white, colors.HexColor("#edf3f7"))),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 1), (0, -1), "CENTER"),
                ("ALIGN", (-1, 1), (-1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            report.build([title, subtitle, Spacer(1, 12), table])
            messagebox.showinfo("Sukses", f"Laporan PDF berhasil disimpan di:\n{file_path}")
        except Exception as e:
            print(f"Error PDF: {e}")
            messagebox.showerror("Error", f"Gagal membuat PDF: {e}")