# GCP üzerinde ilk kaynak doğrulama denemesi

> Dönemsel uygulama kaydı. Kurulum, maliyet ve bekleyen iş ifadeleri belgenin
> ilgili çalışma aşamasına aittir. Güncel durum [STATUS.md](STATUS.md), mevcut
> üretim yolu [devam rehberinde](GCP_SOURCE_AWARE_CONTINUATION_2026-10-09.md) izlenir.

Bu paket bütün yılları veya paralel iş kuyruğunu çalıştırmaz. Daha önce
Colab'da doğrulanmış **13 Ocak 2019 01:00 UTC S-NPP** geçişini, değişmeyen
referans koduyla VM üzerinde sınar. Sonraki paralel hız denemesinden önce
Python/HDF5, NASA erişimi ve kaynak/sayım eşitliği kontrolüdür.

## Hazırlanan paket

- `outputs/gcp_pilot/wildfire_gcp_pilot.zip`: 1.409.018 bayt.
- SHA256: `d9da7b49ee68afbc27c85cf6906d4583d47062423abaeed92cebf57e850aa7f2`.
- Ham kaynak: 194.702.968 bayt, yalnızca VM'ye indirilecek.
- Dört paket üyesi: GCP runner, manifest, sabit bağımlılıklar ve özgün pilot ZIP.
- Özgün pilot ZIP SHA: `bce362d01b5a5d204c5979910703e16f3be11b0568f12b5ac8e34790aee6bbac`.

Kimlik bilgisi, ham uydu veya büyük arşiv içermez. Linux x86_64 / Python
3.12 gerektirir. Ayrı venv kurar; sistem Python paketlerini değiştirmez.
Paket kurma ve doğal işleme alt süreçlerinde ayrı 900 saniye sınırı var;
VM'nin ayrıca **2 saat/Stop** sınırı uygulanmalı. Parola isteminde bekleme
VM'nin çalışma süresini durdurmaz.

## VM oluşturma ön koşulları

Onayladığım Free trial korunur; Upgrade veya kredi dışı ödeme
yok. Frankfurt kotası, mevcut form ve maliyet kontrolü tamamlanmadan paket
hazırlığı VM oluşturulduğu anlamına gelmez.

[Form ve kalan kontroller](GCP_CPU_PREFLIGHT.md).

## Oluşturmadan sonraki kullanım

VM'nin yanındaki SSH ile tarayıcı terminali açılır. Bu terminal VM'nin
terminalidir; Cloud Shell veya yerel PowerShell değildir. SSH penceresindeki
dosya yükleme menüsüyle yalnızca hazırlanan ZIP VM ana dizinine yüklenir.
[Google SSH rehberi](https://docs.cloud.google.com/compute/docs/connect/standard-ssh).

Standart Ubuntu 24.04 üzerinde venv desteğini hazırlamak:

```bash
sudo apt-get update
sudo apt-get install -y python3-venv
```

Yüklenen dosyayı doğrulayıp sadece bilinen üyeleri özel paket dizinine çıkartmak:

```bash
python3 - <<'PY'
import hashlib, zipfile
from pathlib import Path
p = Path.home() / 'wildfire_gcp_pilot.zip'
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'd9da7b49ee68afbc27c85cf6906d4583d47062423abaeed92cebf57e850aa7f2', 'Paket SHA farki'
dest = Path.home() / 'wildfire-gcp-package'
dest.mkdir(exist_ok=True)
assert not dest.is_symlink(), 'Paket dizini symlink'
with zipfile.ZipFile(p) as z:
    expected = {'pilot.zip', 'requirements.txt', 'run_gcp_portability.py', 'gcp_manifest.json'}
    assert len(z.namelist()) == 4 and set(z.namelist()) == expected
    assert z.testzip() is None
    assert all((dest / n).resolve().is_relative_to(dest.resolve()) for n in z.namelist())
    z.extractall(dest)
print('Paket dogrulandi')
PY
python3 ~/wildfire-gcp-package/run_gcp_portability.py
```

NASA kullanıcı adı/parola gizli isteme yazılır; komut satırına, sohbete,
metadata/startup scriptine veya ZIP'e yazılmaz. Orijinal işleyici
`earthaccess.login(..., persist=False)` kullanır. Alt süreç kimlik ortamı
hata veya iptal halinde de temizlenir.

Başarıda `gcp_portability_passed` ve sonuçların tam yolları yazılır.
SSH dosya indirme menüsünden **gcp_pilot_results.zip** ve
**gcp_run_summary.json** alınır; yerelde `outputs/gcp_pilot/received/` altında
saklanır. Hata varsa farklı tarih/ürün veya bağımlılık sürümü denenmez.
Makine boşta çalıştırılmaz; sonuçlar dışarı alındıktan sonra Stop uygulanır.
Disk Stop ile silinmez; yerel sonuç doğrulandıktan sonra ayrı kapanış/temizlik
adımı gerekir. Yeni bucket veya Drive bağlantısı bu ilk deneme için gerekmez.

Gelen üç üyeli sonuç ZIP'i özgün yerel doğrulayıcının `verify()` fonksiyonuyla
okunacak. Bu fonksiyonun döndürdüğü rapor yeni
`outputs/reports/observation_coverage/gcp_pilot_received_verification.json`
yoluna kaydedilecek. Eski CLI raporu Colab adı taşıdığı için CLI ile önceki
kanıtın üzerine yazılmayacak. ZIP'ten kod çalıştırılmaz.

## Yerel prova ve sınırlar

Kaynakların eski SHA'sı korunarak yalnızca özel prova dizinine hardlink
oluşturuldu. İlk prova, donmuş denetimin kaynakları paket kökü altında
beklediğini gösterdi; GCP sarmalayıcının yerel modu düzeltildi. Ardından
orijinal ürün adındaki nokta/alt çizgi ayrımı çıktı üye kontrolünde düzeltildi.
Bilimsel referans kodu ve donmuş eski ZIP değişmedi.

Son gerçek kaynak provası: tam QA/kaynak kimliği ve 2.899 hücre CSV'si eski
referansla eşleşti; üç üyeli 24.510 bayt sonuç ZIP'i CRC/byte geri okumasından
geçti. Mod **local_portability_rehearsal_passed**; NASA indirme/VM/Linux
kurulumu yapılmış sayılmaz. Ham kaynaklar yeniden yerel denetlendi, değişmedi.

11 yeni test paket/hash, çıktı kimliği/etiket yasağı, yerel kaynakların
korunması ve ayrı ortam kurallarını sınar. GCP'deki Python/paket kurulumu
ve gerçek NASA indirmesi henüz çalışmadı. Tek geçiş, paralel hız kazancını,
72 ay bütçesini, fiziksel ayak izini veya günlük negatif etiketi doğrulamaz.

Tam test kümesi 356 başarılı; Ruff kod/biçim kontrolünde 121 Python dosyası
geçti. Kaynakların eski SHA'ları ve tüm hücre referansları bağımsız geri
okumayla ayrıca doğrulandı. Bu kayıtlar yerel hazırlık kanıtıdır.

## Gerçek GCP sonucu — 6 Ekim

SSH kopmasından sonra bağlandım; apt update ve python3-venv başarılı.
Gizli kullanıcı adı girişinde Ctrl+C ile iptal edilen denemeler başarı
sayılmadı. Son deneme gcp_portability_passed verdi; iki çıktı received
dizinine alınıp ayrı rapor yolunda bağımsız doğrulayıcıyla okundu.
ZIP 24.471 bayt, SHA
bb7f9173d6bab9e89008881d4d70fd072ad7e7608d0b73ed82cc3c802c4238bb.
Paket manifest kimliği, kaynak SHA'ları, tam QA, pinli paketler ve 2.899
hücrenin bütün sütunları geçti; başarılı kaynak payload'ı 194.702.968 bayt.
Son çalıştırmanın ortam dahil süresi 134,84 saniye, doğal işleyici süresi
21,65 saniye. Bu süre önceki denemeler/VM boş zamanı veya toplam fatura değil.
Negatif izin false; yalnızca tek geçiş taşınabilirliği geçti. VM'nin
Running kaldığını bildirdim. Sıradaki [bir/iki işçi denemesi](GCP_PARALLEL_BENCHMARK.md)
hazır; henüz bulutta çalışmadı.
