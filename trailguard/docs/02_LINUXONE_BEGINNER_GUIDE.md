# 02 — Panduan Linux & LinuxONE untuk Pemula

Tujuan: cukup tahu untuk bekerja 24 jam tanpa panik. Dikelola Grup A; tambahkan temuan kalian.

## 1. Gambaran besar
- **LinuxONE** = server IBM Z yang menjalankan **Linux biasa**. Kalian masuk lewat **SSH** (terminal jarak jauh). **Tidak ada tampilan desktop.**
- Arsitektur CPU-nya **s390x** (bukan x86/ARM) dan **big-endian**. Dampak praktis: sebagian paket Python yang butuh kode C/Rust **tidak punya file siap-pakai (wheel)** dan harus dikompilasi — lama atau bisa gagal. Itu sebabnya `requirements.txt` kita sengaja ringan.
- Kredensial akses VM (alamat IP, username, password/kunci) ada di dashboard/email Community Cloud saat registrasi. Username umumnya `linux1` — **cek milik kalian**, jangan menebak.
- VM Community Cloud **terbatas** (CPU/RAM/disk). Cek dulu: `free -h`, `df -h`, `nproc`.

## 2. Masuk ke server
```bash
ssh <username>@<ip-vm>          # contoh: ssh linux1@203.0.113.10
# pertama kali: ketik 'yes' untuk fingerprint, lalu password
```
- Windows: PowerShell / Windows Terminal sudah punya `ssh`. (Alternatif: PuTTY.)
- **VS Code Remote-SSH** sangat membantu mengedit file di server, **tetapi belum tentu bisa di s390x**. Jika gagal: edit di laptop → `git push` → di VM `git pull`; atau edit dengan `nano`.
- Putus koneksi tidak boleh membunuh pekerjaan → **pakai tmux** (§4).

## 3. Contekan perintah dasar
| Tujuan | Perintah |
|---|---|
| Di mana saya? / isi folder | `pwd` / `ls -lah` |
| Pindah folder | `cd folder`, `cd ..`, `cd ~` |
| Lihat isi file | `cat f`, `head -20 f`, `tail -f log` (ikuti log live) |
| Edit file (sederhana) | `nano file` (Ctrl+O simpan, Ctrl+X keluar) |
| Salin / pindah / hapus | `cp a b` / `mv a b` / `rm file` |
| Cari teks | `grep -rn "kata" src/` |
| Ukuran file/folder | `du -sh data/*` |
| RAM / disk / CPU | `free -h` / `df -h .` / `nproc` |
| Proses berjalan | `top` atau `htop` (keluar: `q`) |
| Hentikan program | `Ctrl+C` |
| Riwayat perintah | panah atas, atau `history` |
| Jalankan sebagai admin | `sudo perintah` (hati-hati) |

## 4. tmux — wajib dipakai untuk proses panjang
```bash
tmux new -s kerja          # buat sesi bernama "kerja"
# ...jalankan pipeline/training di dalamnya...
# lepas (proses tetap jalan):  Ctrl+B lalu tekan D
tmux ls                    # daftar sesi
tmux attach -t kerja       # kembali ke sesi
```
Jika `tmux` belum terpasang: lihat tabel paket (§6). Alternatif darurat: `nohup perintah > log.txt 2>&1 &`.

## 5. Python & virtualenv
```bash
bash scripts/01_setup_env.sh        # membuat .venv dan memasang dependensi
source .venv/bin/activate           # WAJIB setiap login baru; prompt akan berawalan (.venv)
cp .env.example .env && nano .env   # isi TRAILGUARD_HMAC_KEY
set -a; source .env; set +a         # muat variabel dari .env ke sesi ini
make toy                            # uji cepat
```
Kunci acak: `python3 -c "import secrets; print(secrets.token_hex(32))"`.

## 6. Memasang program sistem (beda per distro)
Lihat distro: `cat /etc/os-release`.
| Distro | Perintah pasang |
|---|---|
| Ubuntu | `sudo apt update && sudo apt install -y tmux git gcc python3-dev` |
| RHEL / Rocky | `sudo dnf install -y tmux git gcc python3-devel` |
| SLES | `sudo zypper install -y tmux git gcc python3-devel` |

## 7. Melihat dashboard dari laptop (SSH tunnel)
Server tidak punya browser. Dari **laptop** (terminal baru, bukan di VM):
```bash
ssh -L 8000:localhost:8000 <username>@<ip-vm>
```
Biarkan terbuka, lalu buka `http://localhost:8000` di browser laptop. Di VM jalankan `make api`. Untuk Jupyter: `-L 8888:localhost:8888`.

## 8. Git di server
```bash
git clone <url-repo> && cd trailguard
git checkout -b grp-a/nama-tugas
git add -A && git commit -m "pesan singkat" && git push -u origin HEAD
```
Jangan commit `.env`, data mentah, atau model besar (sudah di `.gitignore` — tetap periksa `git status`).

## 9. Container (podman/docker)
```bash
make container           # build + run otomatis (memilih podman/docker)
podman ps                # container berjalan (atau: docker ps)
podman logs trailguard   # lihat log
podman rm -f trailguard  # hentikan & hapus
```
Image dasar **harus mendukung linux/s390x**. Jika `pull`/`build` gagal dengan pesan arsitektur → catat pesan lengkap, coba image `ubi9/python-311`, dan tanya SME IBM (`#ibm-z-sme-helpdek` di Discord — **hanya buka di hari-H**).

## 10. Troubleshooting cepat
| Gejala | Kemungkinan penyebab → solusi |
|---|---|
| `Permission denied (publickey/password)` | username/password salah; cek dashboard Community Cloud |
| `command not found: python3` / `tmux` | belum terpasang → §6 |
| `externally-managed-environment` saat `pip install` | lupa `source .venv/bin/activate` |
| `pip` lama lalu error `gcc`/`Rust`/`building wheel failed` | paket tak punya wheel s390x → **catat nama paket**, jangan buang waktu >20 menit; pakai fallback |
| `Killed` / proses mati sendiri | RAM habis (OOM) → pakai sampel data lebih kecil (`max_rows_per_file`) |
| `No space left on device` | `df -h`; hapus data/log yang tak perlu; kompres |
| `Address already in use` (port 8000) | ada proses lama → `podman rm -f trailguard` atau `pkill -f trailguard.api` |
| `ModuleNotFoundError: trailguard` | jalankan lewat `make ...` (mengatur `PYTHONPATH=src`) |
| `TRAILGUARD_HMAC_KEY belum diset` | §5: `set -a; source .env; set +a` |
| `pip install shap` gagal di `llvmlite`/`numba` (cari "llvm-config", "Failed building wheel") | s390x tak punya wheel → pasang paket LLVM dev (Ubuntu: `sudo apt install llvm-dev`; RHEL: `sudo dnf install llvm-devel`) lalu ulangi **sekali**. Gagal lagi / >45 menit → catat & berhenti; pakai Shapley sendiri |
| `pip install pyarrow` gagal / sangat lama | sama: batas 45 menit; tetap CSV.gz |
| Unduh LANL berhenti / disk penuh | `df -h`; jalankan di tmux; `wget -c` (lanjutkan unduhan); jangan simpan file mentah duplikat |
| SSH sering putus | pakai tmux; `ssh -o ServerAliveInterval=30 ...` |

## 11. Keselamatan
- Jangan `sudo rm -rf` dengan path yang tidak 100% kalian pahami.
- Jangan bagikan password/kunci SSH/`.env` di chat publik.
- VM dipakai bersama tim → jangan mengubah `~/.ssh` orang lain.
- Pegang prinsip tim: **catat setiap perintah penting yang berhasil** (jadi resep untuk teman).

## 12. Checklist "Linux survival" (semua anggota, H+0–1)
- [ ] Bisa `ssh` ke VM
- [ ] Bisa `cd`, `ls`, `cat`, `nano`
- [ ] Bisa membuat & melepas sesi `tmux`
- [ ] Bisa `source .venv/bin/activate`
- [ ] Bisa menjalankan `make toy` dan membaca hasilnya
