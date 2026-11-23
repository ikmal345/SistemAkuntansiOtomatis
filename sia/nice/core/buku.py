"""Memuat data buku sekali (akun, saldo awal, jurnal), lalu dipakai bersama oleh semua tahap siklus."""
from collections import defaultdict

from sqlalchemy import select

from core.db import ambil, t_akun, t_detail, t_jurnal, t_pengaturan, t_saldo_awal
from core.util import Z, dec


class Buku:
    """Sumber data hanya tiga: saldo awal, jurnal umum (JU), dan jurnal penyesuaian (AJP).
    Transaksi penerimaan / pengeluaran / lainnya otomatis menjadi JU, jadi semuanya ikut terhitung di sini."""

    def __init__(self):
        self.akun = ambil(select(t_akun).order_by(t_akun.c.kode))
        self.a = {x["kode"]: x for x in self.akun}
        self.sa = {x["kode"]: (dec(x["debit"]), dec(x["kredit"]), dec(x["qty"])) for x in ambil(select(t_saldo_awal))}
        self.pg = ambil(select(t_pengaturan).where(t_pengaturan.c.id == 1))[0]
        self.baris = [dict(x, debit=dec(x["debit"]), kredit=dec(x["kredit"])) for x in ambil(
            select(t_jurnal.c.tanggal, t_jurnal.c.bukti, t_jurnal.c.keterangan, t_jurnal.c.jenis, t_detail.c.kode, t_detail.c.debit, t_detail.c.kredit)
            .select_from(t_jurnal.join(t_detail, t_detail.c.jurnal_id == t_jurnal.c.id))
            .where(t_jurnal.c.jenis.in_(["JU", "AJP"]))
            .order_by(t_jurnal.c.tanggal, t_jurnal.c.id, t_detail.c.id))]
        self._lap = None

    def mut(self, jenis):
        """Total mutasi debit dan kredit tiap akun untuk jenis jurnal tertentu."""
        m = defaultdict(lambda: [Z, Z])
        for l in self.baris:
            if l["jenis"] in jenis:
                m[l["kode"]][0] += l["debit"]
                m[l["kode"]][1] += l["kredit"]
        return m

    def net(self, jenis):
        """Saldo bersih (debit - kredit) tiap akun = saldo awal + mutasi jurnal."""
        m = self.mut(jenis)
        return {k: self.sa.get(k, (Z, Z, Z))[0] - self.sa.get(k, (Z, Z, Z))[1] + m[k][0] - m[k][1] for k in self.a}
