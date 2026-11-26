CREATE DATABASE IF NOT EXISTS db_bengkel_motor;
USE db_bengkel_motor;

-- 1. Tabel Pelanggan
CREATE TABLE pelanggan (
    id_pelanggan INT AUTO_INCREMENT PRIMARY KEY,
    nama_pelanggan VARCHAR(100) NOT NULL,
    no_hp VARCHAR(15) NOT NULL,
    alamat TEXT
);

-- 2. Tabel Kendaraan (Relasi ke Pelanggan)
CREATE TABLE kendaraan (
    no_polisi VARCHAR(15) PRIMARY KEY,
    id_pelanggan INT NOT NULL,
    merk_motor VARCHAR(50) NOT NULL,
    tipe_motor VARCHAR(50) NOT NULL,
    FOREIGN KEY (id_pelanggan) REFERENCES pelanggan(id_pelanggan) ON DELETE CASCADE
);

-- 3. Tabel Mekanik
CREATE TABLE mekanik (
    id_mekanik INT AUTO_INCREMENT PRIMARY KEY,
    nama_mekanik VARCHAR(100) NOT NULL,
    spesialisasi VARCHAR(50)
);

-- 4. Tabel Sparepart (Suku Cadang)
CREATE TABLE sparepart (
    kode_part VARCHAR(20) PRIMARY KEY,
    nama_part VARCHAR(100) NOT NULL,
    stok INT NOT NULL,
    harga INT NOT NULL
);

-- 5. Tabel Servis (Transaksi Utama)
CREATE TABLE servis (
    id_servis INT AUTO_INCREMENT PRIMARY KEY,
    tanggal DATE NOT NULL,
    no_polisi VARCHAR(15) NOT NULL,
    id_mekanik INT NOT NULL,
    keluhan TEXT,
    biaya_jasa INT NOT NULL,
    total_biaya INT NOT NULL,
    FOREIGN KEY (no_polisi) REFERENCES kendaraan(no_polisi),
    FOREIGN KEY (id_mekanik) REFERENCES mekanik(id_mekanik)
);

-- 6. Tabel Detail Penggunaan Sparepart pada Servis
CREATE TABLE detail_servis (
    id_detail INT AUTO_INCREMENT PRIMARY KEY,
    id_servis INT NOT NULL,
    kode_part VARCHAR(20) NOT NULL,
    jumlah INT NOT NULL,
    subtotal INT NOT NULL,
    FOREIGN KEY (id_servis) REFERENCES servis(id_servis) ON DELETE CASCADE,
    FOREIGN KEY (kode_part) REFERENCES sparepart(kode_part)
);

-- Data Awal (Dummy Data) agar aplikasi siap diuji
INSERT INTO mekanik (nama_mekanik, spesialisasi) VALUES 
('Budi Santoso', 'Mesin & Tune Up'), 
('Andi Wijaya', 'Kelistrikan & Injeksi');

INSERT INTO sparepart (kode_part, nama_part, stok, harga) VALUES 
('SP01', 'Oli Mesin MPX2 0.8L', 25, 55000),
('SP02', 'Kampas Rem Depan', 15, 45000),
('SP03', 'Busi Standar', 30, 20000),
('SP04', 'Vanbelt Set', 10, 125000);