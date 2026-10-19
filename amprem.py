#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ikyy AM Premium Tools - versi Termux (CLI)

Pemakaian:
  python amprem.py                      -> menu interaktif
  python amprem.py sendlink EMAIL       -> kirim magic link
  python amprem.py verify LINK          -> verifikasi + aktivasi premium
  python amprem.py status               -> lihat status akun
  python amprem.py info                 -> info tools
  python amprem.py reset                -> hapus data tersimpan
"""

import os
import sys
import json
import time
from datetime import datetime

try:
    import requests
except ImportError:
    print("Module 'requests' belum terinstall.")
    print("Jalankan: pip install requests")
    sys.exit(1)

# ==================================================
# KONFIGURASI
# ==================================================

TOOL_NAME = "Ikyy AM Premium"
VERSION = "1.0"
API_URL = "https://anita-studio.netlify.app/.netlify/functions/amprem"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "data.json")

# ==================================================
# WARNA (ANSI - didukung Termux)
# ==================================================

R = "\033[0m"
B = "\033[1m"
RED = "\033[91m"
GRN = "\033[92m"
YLW = "\033[93m"
BLU = "\033[94m"
MAG = "\033[95m"
CYN = "\033[96m"
DIM = "\033[2m"


def clear():
    os.system("clear")


def banner():
    clear()
    print(f"""{MAG}{B}
  ╭──────────────────────────────────╮
  │   ___ _        __   __           │
  │  |_ _| | ___   \\ \\ / /_   _      │
  │   | || |/ / | | \\ V /| | | |     │
  │   | ||   <| |_| || | | |_| |     │
  │  |___|_|\\_\\\\__, ||_|  \\__, |     │
  │            |___/      |___/      │
  ╰──────────────────────────────────╯{R}
  {CYN}{B}{TOOL_NAME}{R} {DIM}• Termux Tools v{VERSION}{R}
  {DIM}by Ikyy{R}
""")


def line():
    print(f"{DIM}  ──────────────────────────────────{R}")


def ok(msg):
    print(f"  {GRN}✔{R} {msg}")


def err(msg):
    print(f"  {RED}✘{R} {msg}")


def warn(msg):
    print(f"  {YLW}!{R} {msg}")


def wait():
    input(f"\n  {DIM}Tekan Enter untuk lanjut...{R}")


# ==================================================
# DATABASE (lokal, 1 file JSON)
# ==================================================

def load_db():
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        err(f"Gagal baca data: {e}")
    return {
        "email": None,
        "id_token": None,
        "premium": False,
        "created": datetime.now().isoformat(),
    }


def save_db(db):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
    except Exception as e:
        err(f"Gagal simpan data: {e}")


# ==================================================
# API
# ==================================================

def call_api(action, data):
    try:
        r = requests.post(
            API_URL,
            json={"action": action, **data},
            timeout=30,
        )
        return r.json()
    except Exception as e:
        return {"success": False, "message": str(e)}


# ==================================================
# FITUR
# ==================================================

def valid_email(email):
    return "@" in email and "." in email.split("@")[-1] and " " not in email


def do_sendlink(email=None):
    db = load_db()

    if not email:
        default = db.get("email")
        hint = f" [{default}]" if default else ""
        email = input(f"  {CYN}Email{hint}:{R} ").strip() or (default or "")

    if not valid_email(email):
        err("Format email tidak valid.")
        return False

    db["email"] = email
    save_db(db)

    print(f"\n  {YLW}⏳ Mengirim magic link ke{R} {B}{email}{R} ...")
    result = call_api("send-magiclink", {"email": email})

    if result.get("success"):
        ok("Magic link terkirim!")
        print(f"  {DIM}Cek inbox/spam email kamu, lalu pilih menu Verify.{R}")
        return True

    err(f"Gagal mengirim link: {result.get('message', 'Unknown error')}")
    return False


def do_verify(raw_link=None):
    db = load_db()
    email = db.get("email")

    if not email:
        err("Email belum disimpan. Jalankan Send Link dulu.")
        return False

    if not raw_link:
        print(f"  {DIM}Tempel (paste) magic link dari email.{R}")
        raw_link = input(f"  {CYN}Magic link:{R} ").strip()

    if not raw_link:
        err("Link kosong.")
        return False

    print(f"\n  {YLW}⏳ Memverifikasi akun{R} {B}{email}{R} ...")
    result = call_api("verify-account", {"email": email, "rawLink": raw_link})

    if not result.get("success"):
        err(f"Verifikasi gagal: {result.get('message', 'Unknown error')}")
        return False

    id_token = result.get("idToken") or result.get("profile", {}).get("idToken")

    if not id_token:
        err("ID token tidak ditemukan.")
        return False

    db["id_token"] = id_token
    save_db(db)
    ok("Akun berhasil diverifikasi.")

    print(f"  {YLW}⏳ Memproses aktivasi premium...{R}")
    prem = call_api("apply-premium", {"email": email, "idToken": id_token})

    if prem.get("success"):
        db["premium"] = True
        save_db(db)
        print()
        print(f"  {GRN}{B}⭐ PREMIUM AKTIF{R}")
        print(f"  📧 {email}")
        print(f"  📅 {datetime.now().strftime('%d-%m-%Y')}")
        return True

    err(f"Aktivasi premium gagal: {prem.get('message', 'Unknown error')}")
    return False


def do_status():
    db = load_db()
    email = db.get("email") or "Belum diatur"
    premium = db.get("premium", False)
    created = (db.get("created") or "-")[:10]
    status = f"{GRN}ACTIVE ✔{R}" if premium else f"{RED}NOT ACTIVE ✘{R}"

    line()
    print(f"  📧 Email    : {B}{email}{R}")
    print(f"  ⭐ Premium  : {status}")
    print(f"  📅 Dibuat   : {created}")
    line()


def do_info():
    line()
    print(f"  {B}{TOOL_NAME}{R}  v{VERSION}")
    print(f"  Tools untuk membantu proses akun premium.\n")
    print(f"  {CYN}1.{R} Send Link  - kirim magic link ke email")
    print(f"  {CYN}2.{R} Verify     - verifikasi link & aktivasi")
    print(f"  {CYN}3.{R} Status     - lihat status akun")
    line()


def do_reset():
    confirm = input(f"  {YLW}Hapus semua data tersimpan? (y/N):{R} ").strip().lower()
    if confirm == "y":
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        ok("Data dihapus.")
    else:
        warn("Dibatalkan.")


# ==================================================
# MENU INTERAKTIF
# ==================================================

def menu():
    while True:
        banner()
        db = load_db()
        st = f"{GRN}ACTIVE{R}" if db.get("premium") else f"{RED}NOT ACTIVE{R}"
        print(f"  Status : {st}   Email : {db.get('email') or '-'}\n")
        line()
        print(f"  {CYN}[1]{R} 📨 Send Link")
        print(f"  {CYN}[2]{R} 🔐 Verify")
        print(f"  {CYN}[3]{R} 📊 Status")
        print(f"  {CYN}[4]{R} ℹ️  Info")
        print(f"  {CYN}[5]{R} 🗑  Reset Data")
        print(f"  {CYN}[0]{R} 🚪 Keluar")
        line()

        try:
            pilih = input(f"  {B}Pilih menu ›{R} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        print()
        if pilih == "1":
            do_sendlink()
        elif pilih == "2":
            do_verify()
        elif pilih == "3":
            do_status()
        elif pilih == "4":
            do_info()
        elif pilih == "5":
            do_reset()
        elif pilih == "0":
            print(f"  {MAG}Sampai jumpa! — Ikyy{R}\n")
            break
        else:
            warn("Pilihan tidak valid.")
            time.sleep(1)
            continue
        wait()


# ==================================================
# ENTRY POINT
# ==================================================

def main():
    args = sys.argv[1:]

    if not args:
        menu()
        return

    cmd = args[0].lower()
    rest = args[1:]

    if cmd in ("sendlink", "email"):
        do_sendlink(rest[0] if rest else None)
    elif cmd == "verify":
        do_verify(rest[0] if rest else None)
    elif cmd == "status":
        do_status()
    elif cmd == "info":
        do_info()
    elif cmd == "reset":
        do_reset()
    elif cmd in ("-h", "--help", "help"):
        print(__doc__)
    else:
        err(f"Command tidak dikenal: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n  {YLW}Dihentikan.{R}")
