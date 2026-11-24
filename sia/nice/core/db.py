

import datetime as dt
from contextlib import contextmanager

from sqlalchemy import (CHAR, Column, Date, ForeignKey, Integer, MetaData, Numeric, String, Table, create_engine, func,
                        insert, inspect, select)
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateSchema

from core.config import DB
from core.konstanta import DIKUNCI

# definisi tabel
_meta = MetaData()
_opsi = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}  


def _uang(skala=2):
    return Numeric(18, skala)


t_akun = Table("akun", _meta,
               Column("kode", String(10), primary_key=True), Column("nama", String(100)), Column("kelompok", String(20)),
               Column("saldo_normal", CHAR(1)), Column("sistem", TINYINT, server_default="0"), **_opsi)
t_pengaturan = Table("pengaturan", _meta,
                     Column("id", Integer, primary_key=True, autoincrement=False), Column("nama_usaha", String(100)),
                     Column("nama_periode", String(60)), Column("tgl_awal", Date), Column("tgl_akhir", Date), **_opsi)
t_saldo_awal = Table("saldo_awal", _meta,
                     Column("kode", String(10), primary_key=True), Column("debit", _uang(), server_default="0"),
                     Column("kredit", _uang(), server_default="0"), Column("qty", _uang(), server_default="0"), **_opsi)
t_jurnal = Table("jurnal", _meta,                      # jenis: JU, AJP, PNT
                 Column("id", Integer, primary_key=True), Column("tanggal", Date), Column("bukti", String(30)),
                 Column("keterangan", String(255)), Column("jenis", String(4)), Column("sumber", String(12), server_default="MANUAL"), **_opsi)
t_detail = Table("jurnal_detail", _meta,
                 Column("id", Integer, primary_key=True), Column("jurnal_id", Integer, ForeignKey("jurnal.id", ondelete="CASCADE")),
                 Column("kode", String(10)), Column("debit", _uang(), server_default="0"), Column("kredit", _uang(), server_default="0"), **_opsi)
t_mutasi = Table("persediaan_mutasi", _meta,
                 Column("id", Integer, primary_key=True), Column("tanggal", Date), Column("kode", String(10)), Column("jenis", String(6)),
                 Column("qty", _uang()), Column("harga", _uang(4)), Column("total", _uang()), Column("keterangan", String(255)),
                 Column("jurnal_id", Integer), **_opsi)
# semua input Penerimaan / Pengeluaran / Transaksi Lainnya dicatat di sini, lalu otomatis menjadi jurnal umum
t_transaksi = Table("transaksi", _meta,
                    Column("id", Integer, primary_key=True), Column("kelompok", String(8)), Column("item", String(80)),
                    Column("no_bukti", String(30)), Column("tanggal", Date), Column("pihak", String(100)), Column("jenis", String(40)),
                    Column("qty", _uang()), Column("harga", _uang()), Column("total", _uang()), Column("cara", String(30)),
                    Column("keterangan", String(255)), Column("jurnal_id", Integer), **_opsi)
t_migrasi = Table("migrasi", _meta, Column("nama", String(40), primary_key=True), **_opsi)


# koneksi
_mesin = {}


def mesin(pakai_db=True):
    """Satu engine per jenis koneksi (dengan atau tanpa memilih database), dipakai bersama."""
    if pakai_db not in _mesin:
        url = URL.create("mysql+mysqlconnector", username=DB["user"], password=DB["password"] or None, host=DB["host"],
                         port=DB["port"], database=DB["database"] if pakai_db else None, query={"charset": "utf8mb4"})
        _mesin[pakai_db] = create_engine(url, pool_pre_ping=True, pool_recycle=280)
    return _mesin[pakai_db]


@contextmanager
def sesi(commit=False):
    """with sesi(True) as c: c.execute(insert(...))  -> commit di akhir, rollback bila ada kesalahan."""
    s = Session(mesin())
    try:
        yield s
        if commit:
            s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def ambil(perintah):
    """Jalankan select(...) -> daftar baris berupa dict."""
    with sesi() as s:
        return [dict(r) for r in s.execute(perintah).mappings()]


# kode | nama | kelompok | saldo normal (D/K)
AKUN = """1-101|Kas|Aset|D
1-102|Bank BRI|Aset|D
1-103|Piutang Usaha|Aset|D
1-104|Persediaan Alpukat Segar|Aset|D
1-105|Persediaan Alpukat Frozen|Aset|D
1-106|Peralatan Usaha|Aset|D
1-107|Peralatan Pengolahan Frozen|Aset|D
1-108|Akumulasi Penyusutan Peralatan|Aset|K
2-101|Utang Usaha|Liabilitas|K
2-102|Utang Gaji|Liabilitas|K
3-101|Modal Pemilik|Ekuitas|K
3-102|Prive|Ekuitas|D
3-103|Ikhtisar Laba Rugi|Ekuitas|K
4-101|Penjualan Alpukat Segar|Pendapatan|K
4-102|Penjualan Alpukat Frozen|Pendapatan|K
4-103|Penjualan Alpukat untuk Jus|Pendapatan|K
4-104|Pendapatan Lain-lain|Pendapatan|K
4-105|Retur Penjualan|Pendapatan|D
4-106|Potongan Penjualan|Pendapatan|D
5-101|Pembelian Alpukat Segar|Pembelian|D
5-102|Retur Pembelian|Pembelian|K
5-103|Potongan Pembelian|Pembelian|K
6-101|HPP Alpukat Segar|HPP|D
6-102|HPP Alpukat Frozen|HPP|D
6-103|HPP Alpukat untuk Jus|HPP|D
7-101|Beban Gaji|Beban|D
7-102|Beban Perawatan Tanaman|Beban|D
7-103|Beban Produksi Frozen|Beban|D
7-104|Beban Pengiriman|Beban|D
7-105|Beban Penyusutan|Beban|D
7-106|Beban Perlengkapan|Beban|D
7-107|Beban Kompensasi Kerusakan Barang|Beban|D
7-108|Beban Operasional Lainnya|Beban|D
7-109|Beban Air|Beban|D
7-110|Beban Listrik|Beban|D"""


def _migrasi():
    """Penyesuaian satu kali untuk database dari versi lama. Dicatat di tabel `migrasi` supaya tidak diulang
    (jadi akun yang sudah dihapus pengguna tidak muncul lagi)."""
    sudah = {r["nama"] for r in ambil(select(t_migrasi.c.nama))}
    nota_lama = []
    if "nota_ke_transaksi" not in sudah:
        try:
            if inspect(mesin()).has_table("nota"):          # tabel nota tidak ada = instalasi baru
                nota = Table("nota", MetaData(), autoload_with=mesin())
                nota_lama = ambil(select(nota).order_by(nota.c.id))
        except Exception:
            nota_lama = []
    with sesi(True) as s:
        if "akun_air_listrik" not in sudah:
            for kode, nama in (("7-109", "Beban Air"), ("7-110", "Beban Listrik")):
                if not s.execute(select(t_akun.c.kode).where(t_akun.c.kode == kode)).first():
                    s.execute(insert(t_akun).values(kode=kode, nama=nama, kelompok="Beban", saldo_normal="D", sistem=0))
            s.execute(insert(t_migrasi).values(nama="akun_air_listrik"))
        if "nota_ke_transaksi" not in sudah:
            for n in nota_lama:
                jual = n["tipe"] == "JUAL"
                s.execute(insert(t_transaksi).values(
                    kelompok="TERIMA" if jual else "KELUAR", item=("Penjualan " if jual else "Pembelian ") + str(n["jenis"]),
                    no_bukti=n["no_nota"], tanggal=n["tanggal"], pihak=n["pihak"], jenis=n["jenis"], qty=n["qty"], harga=n["harga"],
                    total=n["total"], cara=n["cara"], keterangan="", jurnal_id=n["jurnal_id"]))
            s.execute(insert(t_migrasi).values(nama="nota_ke_transaksi"))


def siapkan_database():
    """Buat database + tabel bila belum ada, lalu isi daftar akun dan periode pertama kali."""
    try:                                    
        with mesin(False).begin() as k:
            k.execute(CreateSchema(DB["database"], if_not_exists=True))
    except Exception:
        pass
    _meta.create_all(mesin())
    with sesi(True) as s:
        if not s.execute(select(func.count()).select_from(t_akun)).scalar():
            baris = [b.split("|") for b in AKUN.splitlines()]
            s.execute(insert(t_akun), [dict(kode=kode, nama=nama, kelompok=kel, saldo_normal=normal, sistem=1 if kode in DIKUNCI else 0)
                                       for kode, nama, kel, normal in baris])
        if not s.execute(select(func.count()).select_from(t_pengaturan)).scalar():
            th = dt.date.today().year
            s.execute(insert(t_pengaturan).values(id=1, nama_usaha="Ambarawa Avocado", nama_periode=f"Periode {th}",
                                                  tgl_awal=dt.date(th, 1, 1), tgl_akhir=dt.date(th, 12, 31)))
    _migrasi()
