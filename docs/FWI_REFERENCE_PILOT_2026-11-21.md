# FWI referansı: küçük veri denemesi ve insan işlemi

21 Kasım 2026. Araştırma planındaki FWI/resmî meteorolojik tehlike
karşılaştırması için edinim hazırlığıdır; yeni model veya hedef
değişikliği değildir. **Henüz FWI dosyası indirilmedi, endeks
hesaplanmadı ve veri setine eklenmedi.**

## Neden bu adım

Dokuz günlük doğrusal pilotun farklı Mersin kaynağındaki ayrımı
zayıf kaldı. Sırf yüksek bir değer elde etmek için yeni modeller
kurmak yerine, planın mevcut fiziksel tehlike referansını doğru
veriyle incelemek gerekiyor. FWI yangın çıkma olasılığı değildir;
meteorolojik yangın tehlikesine ilişkin yerleşik bir karşılaştırma
aracıdır. Etiket/gözlem belirsizliğini gidermez. Günlük ortalama/
uç hava özetlerimiz yerel öğlen ve nem durumu devriyle aynı şey
olmadığından bunlara doğrudan "standart FWI" adı verilmeyecek.
[Önceki bağlayıcı FWI koşulu](research/ARTICLE_RESEARCH_PROTOCOL_2026-10-12.md#temel-modeller-ve-fwi-sınırı).

## Resmî kaynak kontrolü

ECMWF ürün kaydı, CEMS/EFFIS için ERA5 tabanlı tarihsel tehlike
ürününü ve DOI `10.24381/cds.0e89c522` kimliğini doğruluyor.
[ECMWF ürün kaydı](https://www.ecmwf.int/en/forecasts/datasets/fire-danger-indices-historical-data-copernicus-emergency-management-service).

EWDS sayfasında günlük, özgün yaklaşık 31 km ve 0,25° enterpole
ızgara seçenekleri görülüyor. 5 km hücreye bağlamak fiziksel
çözünürlüğü artırmaz. Portalda 16 Kasım 2026'dan itibaren
güncellemelerin durduğu uyarısı var; bu nottan tarihsel arşivin
silindiği sonucu çıkarılmadı. 2022 seçenekleri mevcut, gerçek
indirme başarısı henüz doğrulanmadı.
[EWDS ürün bilgisi](https://ewds.climate.copernicus.eu/datasets/cems-fire-historical-v1?tab=overview).

21 Kasım tarayıcı kontrolünde giriş yapılmış EWDS oturumu yoktu;
indirme/lisans düğmeleri giriş istiyordu. Yalnız public form
incelendi; hesap/anahtar oluşturulmadı, giriş/lisans onayı veya
istek gönderimi yapılmadı. Kimlik bilgisi okunmadı/paylaşılmadı.

## Kullanıcının yapacağı tek küçük edinim

[Ürünün Download sayfasını aç](https://ewds.climate.copernicus.eu/datasets/cems-fire-historical-v1?tab=download),
kendi hesabınla giriş yap ve lisansı kendin incele. Görülen form
için hazırlanmış seçimler aşağıdadır; bunlar API kodu değildir.

| Alan | Seçim |
|---|---|
| Product type | Reanalysis |
| Variable | Yalnız Fire weather index |
| Dataset type | Consolidated dataset |
| System version | 4.1 |
| Year / Month | 2022 / June |
| Day | 01–30; 31 seçilmesin |
| Geographical area | Area selection |
| North / South | 40 / 35 |
| West / East | 25 / 37 |
| Grid | 0.25x0.25 (interpolated) |
| Data format | NetCDF4 (Experimental) |

Bu yalnız küçük bölgesel bir aylık dosya denemesidir; dünya alanı,
bütün yıllar/değişkenler veya 2023–2025 seçilmeyecek. İndirme
boyutu henüz ölçülmedi; yerel okuyucu 32 MiB üstünü otomatik
kabul etmez. İnen özgün dosyayı şu klasöre olduğu gibi koy:

`C:/PROJELERIM/wildfire-risk-prediction/data/raw/external/cems_fwi_pilot_v1/`

Hesap parolası, erişim anahtarı veya oturum URL'si paylaşma.
Dosya ZIP gelirse özgün arşiv korunur; aşağıdaki okuyucu yalnız
`.nc` için, arşiv içeriği gerektiğinde ayrıca incelenecek.

## Hazır yerel kontrol ve kabul sınırı

`configs/fwi_reference_pilot_v1.json` görülen formu ve sınırları
kaydeder. `scripts/quality/inspect_fwi_reference_metadata.py` gerçek
NetCDF/HDF imzası, dosya hash/boyutu, yerel yol, değişken/ızgara ve
CF zaman metadata'sını inceler. Mevcut Rasterio ortamında netCDF
ve HDF5 sürücüsü bulundu; ek paket veya API anahtarı gerekmedi.
Örnek komut (dosya adı ancak indirdikten sonra gerçek adıyla yazılır):

```powershell
.\.venv\Scripts\python.exe scripts/quality/inspect_fwi_reference_metadata.py --file 'data/raw/external/cems_fwi_pilot_v1/GERCEK_DOSYA_ADI.nc'
```

Bu komutu kullanıcının çalıştırması şart değil; dosya yerelde
bulunduğunda asistan inceleyebilir. Okuyucu FWI değer dizisini
okumaz, model girdisi/yangın etiketi/risk rengi üretmez. Nominal CF
zamanı günlük girdilerin gerçek edinim veya yayımlanma zamanı
sayılmaz. Hedef gününün gerçekleşmiş hava/endeks değerini girdi
yaparak gelecek sızıntısı oluşturulmayacak; T'den önceki gün
eşleştirmesi de belge ve dosya zaman tanımı görülmeden kabul edilmez.
Operasyonel erişim veya gelecek hava tahmini arşivi doğrulanmış değil.

Dosya geldikten sonra zaman tanımı, değişken birimi, ölçek/no-data,
ızgara, tarih ve bölge ayrıca değerlendirilecek. Küçük deneme geçerse
gerekli tarih kapsamı ayrı somutlaştırılır. Şimdiki aşama veri
başlığını anlama ve referansın uygulanabilirliği; veri seti veya
ana yöntem kabulü değildir.

CF saat/gün birimlerinin eşitliği ve yanlış yıl/ay/birim reddi
için dört sentetik davranış testi geçti. Yeni kaynak/rol/geçmiş
pencere kontrolleriyle son ilgili birleşik koşu 57 testtir; gerçek
sağlayıcı dosyasının başarıyla açıldığı veya indirildiği anlamına
gelmez.
