

from core.buku import Buku
from siklus.bukbes import buku_besar
from ui.komponen import tampil


def tabel(b):
    return buku_besar(b, ("JU", "AJP"))


def halaman():
    tampil(*tabel(Buku()))
