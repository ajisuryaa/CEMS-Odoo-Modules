# Cara Menjalankan CEMS (Odoo 19)

Panduan menjalankan proyek **CEMS** di mesin lokal: **tanpa Docker** dan **dengan Docker**.

| | |
|---|---|
| **Target** | Odoo 19 Community |
| **Addons** | `cems_odoo/custom-addons` (`construction_progress`, `construction_hrd`) |
| **URL default** | http://localhost:8069 |

---

## Struktur folder yang diasumsikan

Repo CEMS **tidak** berisi Odoo core. Layout yang dipakai di mesin development:

```text
pmg-odoo/                         ← working directory (parent)
├── odoo/                         ← clone Odoo 19 (bukan bagian repo CEMS)
├── venv/                         ← Python virtualenv (tanpa Docker)
└── cems_odoo/                    ← repo ini (Git)
    ├── custom-addons/
    │   ├── construction_progress/
    │   └── construction_hrd/
    ├── document_project/
    ├── docker-compose.yml
    ├── docker/
    │   └── odoo.conf
    ├── odoo.conf.example
    └── RUNNING.md                ← dokumen ini
```

Semua perintah di bawah dijalankan dari **`pmg-odoo/`** kecuali yang disebut khusus di dalam `cems_odoo/`.

---

## A. Tanpa Docker (local / venv)

### Prasyarat

| Komponen | Catatan |
|----------|---------|
| **Python** | 3.11 atau 3.12 (disarankan; ikuti `odoo/requirements.txt`) |
| **PostgreSQL** | 14+ (lokal), user/role untuk Odoo |
| **Git** | untuk clone Odoo + repo CEMS |
| **OS libs** | macOS: Xcode CLT; Linux: libpq, build tools sesuai Odoo docs |

### 1. Clone Odoo 19 & buat venv

```bash
cd /path/to/pmg-odoo

# Odoo core (sekali saja)
git clone -b 19.0 --depth 1 https://github.com/odoo/odoo.git

# Virtualenv
python3.11 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r odoo/requirements.txt
```

### 2. Pastikan PostgreSQL siap

Contoh cepat (macOS Homebrew):

```bash
brew services start postgresql@16
createuser -s odoo          # atau user lain
createdb odoo               # nama DB bebas, mis. odoo / cems_dev
```

Sesuaikan user/password di `odoo.conf` jika dipakai.

### 3. (Opsional) File konfigurasi

```bash
cp cems_odoo/odoo.conf.example cems_odoo/odoo.conf
# edit admin_passwd, db_user, db_password jika perlu
```

Path `addons_path` di contoh relatif terhadap lokasi file conf. Jika menjalankan dari `pmg-odoo/` dengan flag CLI, path di bawah sudah cukup tanpa conf.

### 4. Jalankan server (hari-hari)

```bash
cd /path/to/pmg-odoo
source venv/bin/activate

./odoo/odoo-bin -d odoo \
  --addons-path=odoo/addons,odoo/odoo/addons,cems_odoo/custom-addons
```

Atau dengan conf:

```bash
./odoo/odoo-bin -c cems_odoo/odoo.conf -d odoo
```

Buka: **http://localhost:8069**

> **Penting:** jangan ada spasi setelah `\` di multi-line shell. Salah: `\ --addons-path=...` → error `unrecognized parameters`.

### 5. Install modul CEMS (pertama kali)

**Cara A — UI**

1. Login sebagai admin  
2. Aktifkan Developer Mode  
3. Apps → Update Apps List  
4. Install **CEMS Construction Progress**  
5. Install **CEMS Construction HRD**

**Cara B — CLI**

```bash
./odoo/odoo-bin -d odoo \
  --addons-path=odoo/addons,odoo/odoo/addons,cems_odoo/custom-addons \
  -i construction_progress,construction_hrd --stop-after-init
```

Lalu start server lagi (langkah 4).

### 6. Upgrade setelah ubah kode

```bash
./odoo/odoo-bin -d odoo \
  --addons-path=odoo/addons,odoo/odoo/addons,cems_odoo/custom-addons \
  -u construction_progress,construction_hrd --stop-after-init
```

### 7. Checklist cepat (tanpa Docker)

| Cek | Perintah / aksi |
|-----|-----------------|
| Venv aktif | prompt `(venv)` |
| Postgres jalan | `psql -l` atau `pg_isready` |
| Addons terbaca | Apps list menampilkan `construction_*` |
| Port | 8069 tidak bentrok |

---

## B. Dengan Docker

File Compose ada di root repo: [`docker-compose.yml`](./docker-compose.yml).  
Image resmi **`odoo:19.0`** + **PostgreSQL 16**. Addons CEMS di-mount ke `/mnt/extra-addons`.

### Prasyarat

- Docker Desktop (macOS/Windows) atau Docker Engine + Compose plugin (Linux)
- Port **8069** (Odoo) dan **5432** (Postgres) tersedia di host — atau ubah di compose

### 1. Start stack

```bash
cd /path/to/pmg-odoo/cems_odoo

docker compose up -d
```

Cek status:

```bash
docker compose ps
docker compose logs -f web
```

Buka: **http://localhost:8069**

Database manager muncul di browser pertama kali — buat DB baru (mis. `odoo`), master password sesuai `docker/odoo.conf` (`admin_passwd`).

### 2. Install modul CEMS di Docker

Setelah DB dibuat dan Odoo siap:

```bash
cd /path/to/pmg-odoo/cems_odoo

docker compose exec web odoo \
  -d odoo \
  -i construction_progress,construction_hrd \
  --stop-after-init
```

> Ganti `-d odoo` dengan nama database yang Anda buat di UI.

Restart web agar server normal:

```bash
docker compose restart web
```

Atau lewat UI: Apps → Update Apps List → install modul CEMS.

### 3. Upgrade modul (setelah edit kode lokal)

Kode di `custom-addons/` langsung terlihat di container (volume mount). Setelah ubah Python/XML:

```bash
docker compose exec web odoo \
  -d odoo \
  -u construction_progress,construction_hrd \
  --stop-after-init

docker compose restart web
```

### 4. Perintah berguna

```bash
# Stop
docker compose down

# Stop + hapus volume DB (HATI-HATI: data hilang)
docker compose down -v

# Shell di container Odoo
docker compose exec web bash

# psql ke Postgres
docker compose exec db psql -U odoo -d odoo
```

### 5. Variabel / file Docker

| File / env | Fungsi |
|------------|--------|
| `docker-compose.yml` | Service `web` (Odoo 19) + `db` (Postgres 16) |
| `docker/odoo.conf` | `addons_path`, port, credentials master |
| Volume `odoo-web-data` | filestore Odoo |
| Volume `odoo-db-data` | data PostgreSQL |

Default Compose:

- Host port **8069** → container 8069  
- Postgres hanya di jaringan internal Compose (tidak expose 5432 ke host, kecuali Anda uncomment di compose)

### 6. Checklist cepat (Docker)

| Cek | Aksi |
|-----|------|
| Image pull sukses | `docker compose pull` |
| `web` healthy / logs tanpa traceback | `docker compose logs web` |
| Addons mount | di container: `ls /mnt/extra-addons` → ada `construction_*` |
| Install order | Progress dulu, lalu HRD |

---

## Urutan install modul

```text
construction_progress  →  construction_hrd  →  (fase berikutnya…)
```

Jangan install HRD sebelum Progress (dependensi manifest).

---

## Troubleshooting

| Gejala | Penyebab umum | Perbaikan |
|--------|---------------|-----------|
| `unrecognized parameters: --addons-path=...` | Spasi setelah `\` di shell | Hapus spasi; atau tulis satu baris |
| Modul CEMS tidak muncul di Apps | `addons_path` masih ke `custom-addons` lama | Pakai `cems_odoo/custom-addons` |
| `/my/cems/attendance` 404 | HRD belum di-install / belum di-upgrade | `-i` / `-u construction_hrd` |
| GPS / kamera portal gagal | Bukan HTTPS / localhost policy | Pakai `localhost` atau HTTPS; izinkan browser |
| Docker: permission / mount kosong | Path volume salah | Jalankan `compose` dari folder `cems_odoo/` |
| Port already in use | Ada Odoo/Postgres lain | Stop proses lama atau ganti port di compose/conf |

---

## Referensi terkait

| Dokumen | Isi |
|---------|-----|
| [README.md](./README.md) | Overview monorepo |
| [odoo.conf.example](./odoo.conf.example) | Template conf lokal (tanpa Docker) |
| [document_project/pt_dynatech_batam/README.md](./document_project/pt_dynatech_batam/README.md) | Indeks blueprint & phase guides |
| [custom-addons/construction_progress/README.md](./custom-addons/construction_progress/README.md) | Modul Phase 1 |
| [custom-addons/construction_hrd/README.md](./custom-addons/construction_hrd/README.md) | Modul Phase 2 |
