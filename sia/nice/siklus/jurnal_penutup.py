

import streamlit as st
from sqlalchemy import delete, insert

from core.buku import Buku
from core.db import sesi, t_detail, t_jurnal
from core.konstanta import IKHTISAR, LR, MODAL, PRIVE
from core.util import B, I, Z, kol
from ui.komponen import jalankan, pesan, tampil

KOL_PNT = kol(("Tanggal", 105, "w"), ("Keterangan / Akun", 520, "w"), ("Ref", 80, "w"), ("Debit", 150, "e"), ("Kredit", 150, "e"))


def penutup(b):
    """Daftar entri penutup: [(keterangan, [(kode, nama, debit, kredit)])]."""
    net = b.net(("JU", "AJP"))
    nm = lambda k: b.a[k]["nama"]
    sem = [a for a in b.akun if a["kelompok"] in LR and net[a["kode"]]]
    kr, db_ = [a for a in sem if net[a["kode"]] < 0], [a for a in sem if net[a["kode"]] > 0]
    ent = []
    if kr:
        ent.append(("Menutup akun pendapatan ke Ikhtisar Laba Rugi", [(a["kode"], a["nama"], -net[a["kode"]], Z) for a in kr]
                    + [(IKHTISAR, nm(IKHTISAR), Z, -sum(net[a["kode"]] for a in kr))]))
    if db_:
        ent.append(("Menutup akun HPP dan beban ke Ikhtisar Laba Rugi", [(IKHTISAR, nm(IKHTISAR), sum(net[a["kode"]] for a in db_), Z)]
                    + [(a["kode"], a["nama"], Z, net[a["kode"]]) for a in db_]))
    laba = -sum(net[a["kode"]] for a in sem)
    if laba > 0:
        ent.append(("Menutup Ikhtisar Laba Rugi (laba) ke Modal Pemilik", [(IKHTISAR, nm(IKHTISAR), laba, Z), (MODAL, nm(MODAL), Z, laba)]))
    elif laba < 0:
        ent.append(("Menutup Ikhtisar Laba Rugi (rugi) ke Modal Pemilik", [(MODAL, nm(MODAL), -laba, Z), (IKHTISAR, nm(IKHTISAR), Z, -laba)]))
    if net[PRIVE] > 0:
        ent.append(("Menutup Prive ke Modal Pemilik", [(MODAL, nm(MODAL), net[PRIVE], Z), (PRIVE, nm(PRIVE), Z, net[PRIVE])]))
    return ent


def tabel(b):
    rows, td, tk = [], Z, Z
    for i, (ket, baris) in enumerate(penutup(b), 1):
        rows.append(B(b.pg["tgl_akhir"], f"{i}. {ket}", tag="b"))
        for kode, nama, d, k in baris:
            rows.append(B("", (I if k else "") + nama, kode, d, k))
            td, tk = td + d, tk + k
    return KOL_PNT, (rows or [B("", "Belum ada akun sementara yang bersaldo.", tag="kosong")]) + [B("", "TOTAL JURNAL PENUTUP", "", td, tk, tag="b")]


def simpan():
    """Simpan jurnal penutup ke database (menggantikan penutup yang sudah ada)."""
    b = Buku()
    ent = penutup(b)
    with sesi(True) as c:
        c.execute(delete(t_jurnal).where(t_jurnal.c.jenis == "PNT"))
        for i, (ket, baris) in enumerate(ent, 1):
            jid = c.execute(insert(t_jurnal).values(tanggal=b.pg["tgl_akhir"], bukti=f"JP-{i:02d}", keterangan=ket,
                                                    jenis="PNT", sumber="SISTEM")).inserted_primary_key[0]
            for kode, _, d, k in baris:
                c.execute(insert(t_detail).values(jurnal_id=jid, kode=kode, debit=d, kredit=k))
    return len(ent)


def halaman():
    if st.button("Simpan jurnal penutup ke database", type="primary") and jalankan(simpan):
        pesan("ok", "Jurnal penutup tersimpan di database.")
        st.rerun()
    tampil(*tabel(Buku()))
