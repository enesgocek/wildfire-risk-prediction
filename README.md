# Orman Yangını Riski — Pilot Proje

Antalya, Muğla, İzmir ve Mersin'de 5×5 km gridler için sonraki 24 saatin yangın
riski üzerinde çalışıyoruz. Şu an ilk hafta altyapısı hazır; gerçek veri ve model henüz yok.

## Nereden başlamalıyım?

- [Proje rehberi](docs/PROJECT.md): kapsam, veri kuralları, mevcut durum ve sıradaki işler.
- [Orijinal yol haritası](docs/ROADMAP.md): bütün projenin haftalık planı.
- `configs/project.yaml`: iller, tahmin ufku ve eğitim/validation/test yılları.

Orijinal yol haritasındaki Hatay önerisi yerine **Mersin** seçilmiştir.
Güncel kararlar proje rehberi ve yapılandırmada bulunur.

## Klasörlerin amacı

```text
configs/  → Proje ayarları
docs/     → Proje kararları ve yol haritası
src/      → Şu an kullanılan Python kodu
scripts/  → Kurulum ve kontrol komutları
tests/    → Mevcut kodun kontrolleri
outputs/  → Deneyler, raporlar ve önbellek (Git'e girmez)
```

Veri toplarken `data/`, model ve arayüz geliştirilirken ilgili klasörler eklenecek.
Boş gelecek klasörleri tutulmaz. `.venv` Python ortamıdır; günlük çalışmada düzenlenmez.
Kökteki `pyproject.toml`, `uv.lock`, `.python-version` ve `.gitignore` teknik altyapıdır.

## Antigravity ve kurulum

Klasörü Antigravity'de açın. Python interpreter: `.venv\Scripts\python.exe`.
Windows PowerShell'de proje kökünden:

```powershell
.\scripts\setup.ps1
```

uv kurulu değilse Python 3.12 yolu verilebilir:

```powershell
.\scripts\setup.ps1 -PythonExe 'C:\Python312\python.exe'
```

[uv kurulum yönergesi](https://docs.astral.sh/uv/getting-started/installation/).
Python sürüm hedefi `.python-version`, paket sürümleri `uv.lock` içinde tutulur.
uv kurulu başka bir işletim sisteminde `uv sync --locked` kullanılabilir;
mevcut kurulum Windows üzerinde doğrulanmıştır.

## Kontroller ve ilk deney

Mevcut bilgisayarda uv PATH'te olmadığından doğrudan proje içindeki uv kullanılır:

```powershell
.\.venv\Scripts\uv.exe run --locked pytest
.\.venv\Scripts\uv.exe run --locked ruff check .
.\.venv\Scripts\uv.exe run --locked python scripts/smoke_experiment.py
```

Bu deney yalnızca altyapıyı kontrol eder; gerçek veri kullanmaz veya model eğitmez.
Sonuçlar `outputs/reports/` altında tutulur. uv PATH'teyse tam yol yerine `uv` yazılabilir.

## MLflow deney ekranı

```powershell
.\.venv\Scripts\uv.exe run --locked mlflow server --backend-store-uri sqlite:///outputs/mlflow/mlflow.db --host 127.0.0.1 --port 5000
```

Proje kökünden başlatıp <http://127.0.0.1:5000> adresini açın. Ctrl+C ile durdurun.
Veritabanı ve deney dosyaları `outputs/mlflow/` altındadır. Önceki deney kaydı korunmuştur.
Bu klasör için ayrı yedekleme gerekir; Git'e yüklenmez.

## Earth Engine erişimi

Google Cloud/Earth Engine projenizi kaydedip API ve non-commercial doğrulamasını tamamlayın.
Setup'ın oluşturduğu `.env` içinde `GEE_PROJECT_ID` değerini doldurun:

```powershell
.\.venv\Scripts\uv.exe run --locked earthengine authenticate
.\.venv\Scripts\uv.exe run --locked python scripts/check_gee_access.py
```

Kontrol sonucu `outputs/reports/gee_access.json` içine yazılır.
Çıkış kodu 0 başarılı API isteği, 1 erişim hatası, 2 ayarlanmamış proje kimliğidir.
API başarısı non-commercial statüsünü doğrulamaz; o adım Google hesabında tamamlanır.
[Google erişim yönergesi](https://developers.google.com/earth-engine/guides/access).

## GitHub'a yükleme

Yerel Git deposu hazır; commit ve uzak depo bağlantısı size bırakıldı.
GitHub'da boş depo oluşturduktan sonra:

```powershell
git status --short
git add .
git commit -m "Initialize research infrastructure"
git remote add origin https://github.com/KULLANICI_ADIN/wildfire-risk-prediction.git
git push -u origin main
```

`.env`, `.venv`, `outputs` ve büyük veri/model dosyaları Git'e girmez.
