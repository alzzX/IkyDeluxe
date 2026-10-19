#!/data/data/com.termux/files/usr/bin/bash
# Installer Ikyy AM Premium Tools untuk Termux
echo "[*] Update paket..."
pkg update -y && pkg upgrade -y
echo "[*] Install python..."
pkg install -y python
echo "[*] Install requirements..."
pip install -r requirements.txt
chmod +x amprem.py
echo ""
echo "[✔] Selesai! Jalankan dengan:  python amprem.py"
