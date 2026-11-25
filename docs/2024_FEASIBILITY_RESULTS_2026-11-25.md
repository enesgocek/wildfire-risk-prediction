# 2024 kaynak ve girdi uygulanabilirliği — 25 Kasım 2026

## Sonuç

Araştırmacının somut A önerisi ardından projeye devam talimatı, sınırlı
2024 incelemesine devam olarak kaydedildi; açıkça A harfi yazdığı iddia
edilmedi. Ayrı yürütme kaydı `configs/2024_source_replication_feasibility_execution_v1.json`.
Önceki önerinin `execute_authorized=false` tarihsel hali değiştirilmedi.

**2024 meteoroloji girdileri yerelde mevcut ve kalite geri okuması geçti.
Ana modelin dört NDVI/NDMI girdisi için 2024 kapsamı kontrol edilen bitki
örtüsü depolarında bulunmadı.** Dolayısıyla 15 alanlı ana XGBoost ile
2024 değerlendirmesi başlatılmadı. Gerçek yangın etiketi veya negatif
gün üretilmedi; önceki deneysel S/U ve modeller değiştirilmedi.

## Kaynak tablosu: 2.960 tespit

Donmuş birleşik kaynakta 33.255 satırın önce yalnız yıl metadata'sı
incelendi. Diğer yılların 30.295 satırındaki bilimsel alanlar opak
bırakıldı; **2.960 adet 2024 satırı** çözümlendi. Hepsi mevcut type=0,
nominal/yüksek güven kuralını, dört il nokta AOI'sini ve su kapsamını
geçti. Koordinatlardan hesaplanan 5 km grid anahtarları dosyayla eşleşti.
Kimlikler tekil; 1.531 N20, 1.429 SNPP tespiti var.

Tespitler 320 farklı kaynak günü ve 505 farklı hücreye yayılıyor.
Yılın kalan 46 gününde bu katalogda kayıt bulunmaması iyi gözlem veya
yangın yokluğu değildir. Dosya `version=2` alanı NASA'nın açıkladığı
Collection 2 bağlamıdır; aylık ürünün işleme sürümünün doğrulandığı
anlamına gelmez. Sayılar bağımsız yangın/ilk olay veya S üyeliği değildir.
İlk olay gruplaması bu işte yapılmadı.

## Meteoroloji: 366 gün geri okundu

2024'ün 366 günlük ham hücre tablosu ve 366 mevcut türetilmiş tablo,
değişmemiş `weather_model_v1` kuralıyla yeniden karşılaştırıldı. Girdiler
ve mevcut çıktı dosyaları düzenlenmedi. Her dosyada 2.899 hücre, doğru
2024 günlük zaman anahtarı ve aynı şema doğrulandı.

| 2024 meteoroloji incelemesi | Hücre–gün |
|---|---:|
| Kontrol edilen bütün kayıtlar | 1.061.034 |
| 11 meteoroloji alanı sonlu | 991.860 |
| Mevcut tam alan ana kalite kuralını geçen | 878.400 |

Dolu değer ile tam alan kapsamı aynı şey değil. Mevcut kalite eşiği
değiştirilmedi, eksikler doldurulmadı. Bu sayımlar bütün meteoroloji
hücreleri içindir; 2.889 hücrelik su kapsamı veya 505 kaynak hücresi
ile aynı payda değildir.

Sağ uç dahil `(T,T+24h]` takvim bağlantısında 2.960 tespitin tamamı
mevcut 2024 meteoroloji gününe bağlanabiliyor. **1.797 tespit**, bağlı
hücre/günde tam alan meteoroloji kuralını geçiyor. Kalan 1.163 tespit
silinmedi; puanlanabilir kabul edilmedi. Bu 1.797, bağımsız yangın veya
henüz hazırlanmamış ilk olay/hücre–gün eğitim sayısı değildir.

Sayısal karşılaştırma, eski `scripts/meteorology/prepare_model_weather.py`
üreticisinde zaten kullanılan CSV toleransıyla yapıldı: rtol=atol=1e-12.
En büyük gözlenen mutlak fark **5,68434×10⁻¹⁴**. NaN maskeleri, kalite
bayrakları ve anahtar/metadata metinleri tam eşleşti. İlk bit eşitliği
denemesinde görülen fark bu yazma/okuma hassasiyetiydi; sonuç geçirmek
için yeni bilimsel tolerans seçilmedi. Bu kalite kontrolü, yeniden analiz
verisinin gerçek zamanda erişilebilir olduğunu kanıtlamaz.

**Tarih açıklığı:** 3 Ekim tarihli meteoroloji kuralı, 2024'ün eski
bütünlük incelemelerine dahil edildiğini zaten belirtir. Dolayısıyla
2024 meteorolojisi küresel olarak ilk kez açılmış veya kör veri diye
sunulmaz. Yeni çalışma mevcut araştırma hattında 2024 kaynak/özellik
hazırlığıdır; 2025 final kapalıdır. Kaynak/meteo değerleri incelenmiş
2024'te ilerideki sonuçlar için körlük iddiası kurulmayacak.

## Eksik girdi: 2024 NDVI/NDMI

`data/raw/vegetation/` ve `data/interim/vegetation/` altında adında
2024 bulunan veri yolu yok. Tam kapsamlı `full_grid_v1` ve aylık
`month_v1` dizinleri bu yıla uzanmıyor. Tarih içermeyen dört küçük
pilot CSV'nin yalnız tarih/hücre metadata'sı da incelendi; 2024 satırı
yok. Bu inceleme tüm diskin veya sağlayıcıların yokluk kanıtı değildir.
Pilotların NDVI/NDMI değerleri ve 2023/2025 bilimsel dosyaları açılmadı.

Ana modelin dört alanı, 30 ve 60 günlük geçmiş pencerelerden gelen
NDVI/NDMI özetleridir. 2017 sabit örtü haritası bunların yerine geçmez.
Dört alanı sıfırlamak, eski 2023 değerlerini sınırsız taşımak veya bu
alanlar yokken 15 alanlı modeli çalıştırmak mevcut yöntemi korumaz.

## Tamamlanan denetimler ve kayıt

- Altı yeni kaynak/yıl/CSV biçimi davranışı, mevcut meteoroloji ve
  nihai birleştirme korumalarıyla bu devamda **32 ilgili test** geçti.
- Ayrı denetleyici kaynak tablosunda yalnız 2024 alanlarını çözüp
  2.960 kimlik/değer ve gün/sensör sayımını doğrudan karşılaştırdı.
  Standart CSV okuyucusuyla 366 mevcut meteoroloji dosyasından doluluk,
  kalite ve tespit/gün desteğini yeniden saydı; yıl toplamları eşleşti.
- Kaynak ve 732 günlük meteoroloji girdi hash'leri korundu. Yeni
  üreticide akış logu kapanmadan hash'lenmedi; kapanmış log kimliği
  ebeveyn makbuzunda ayrı doğrulandı.
- İki eski tarih metni biçimi ve ilk katı bit eşitliği kontrolünde
  duran ara denemeler korundu, başarı sayılmadı. Kaynak/meteoroloji
  dosyaları değiştirilmedi. Ayrı denetleyicinin ilk BOM başlık okuması
  düzeltilip yeniden çalıştırıldı; hatalı deneme kabul edilmedi.
- Başarılı son iş 49,484 saniye; ebeveyn süre sınırı 900 saniye.
  Yeni veri indirmesi, bulut işi, model yükleme/fit/tahmin veya nihai
  etiketli birleştirme yok. Ayrı sayım denetimi bu işten sonradır.

`outputs/reports/dataset/` altında:

| Çalışma | readback.json SHA-256 |
|---|---|
| `2024_replication_feasibility_v1/20261125T001419Z_2e1802f8` | `bf53e0a9146779534cc71143db73578a201d13c5966193107d338433e07cf1e6` |
| `2024_replication_feasibility_audit_v1/20261125T001641Z_f8eab957` | `6095a5c776729ef979ab668bec8b05bdccbd7d8538347803cd1cd4cad4fc6245` |

## Somut sonraki yol: ana bitki örtüsü yöntemini koruyan yerel prova

Google Cloud kullanılmadan aynı Landsat girdisine erişim yolu incelendi.
Microsoft'un resmi örneği `landsat-c2-l2` arşivini ve API anahtarı olmadan
erişim yolunu tarif ediyor. Koleksiyon metadata uç noktası okunabildi;
alan/tarih araması web aracı erişim hatası verdi. Bu sağlayıcıda veri
yokluğu kanıtı değildir. Raster bantlarına erişim henüz sınanmadı.
[Resmi örnek](https://github.com/microsoft/PlanetaryComputerExamples/blob/main/datasets/landsat-c2/landsat-c2-example.ipynb),
[koleksiyon metadata'sı](https://planetarycomputer.microsoft.com/api/stac/v1/collections/landsat-c2-l2).

Mevcut yöntemle aynı Collection 2 Level-2 yüzey yansıması ölçeği ve
kalite bantları kullanılabilir görünüyor; sayısal eşdeğerlik henüz
doğrulanmadı. Ölçek/offset ve QA bantları USGS'nin birincil belgelerinde
açıklanıyor. [USGS ölçek](https://www.usgs.gov/faqs/how-do-i-use-a-scale-factor-landsat-level-2-science-products),
[USGS kalite](https://www.usgs.gov/landsat-missions/landsat-collection-2-quality-assessment-bands).
Ücretli Azure Pro/hesap/işlem hizmeti açılmayacak; herkese açık veri erişimi
ve yerel hesap olasılığı araştırılıyor.

**Önerilen A:** ana 15 alanlı modeli koruyarak tek hücre için sınırlı
yerel Landsat erişim/uyumluluk provası. Somut öneri
`configs/local_landsat_compatibility_pilot_proposal_v1.json` içinde:

- En fazla 15 dakika, toplam 128 MiB (134.217.728 bayt), en fazla 20
  sahne ve 512 HTTP isteği; bulut hesabı veya ücretli işlem yok.
- Hücre C517/R913, 1 Temmuz 2024 ve eski yerel karşılık için 1 Temmuz
  2022; 30/60 günlük yalnız geçmiş pencereler. Hücre seçimi sonuca göre
  değil, Temmuz 2024 meteoroloji desteği olan katalogda ilk grid/kimliktir.
  Temsilî yangın veya örtü örneği değildir.
- Yalnız Landsat 8 / Tier 1, red/NIR/SWIR1 ve QA bantları. QA maskesi
  191, QA_RADSAT=0, mevcut ölçek ve yansıma aralığı korunur. Bulut
  yüzdesine göre yeni sahne kesimi eklenmez. Eksik sahneler sessizce
  atılarak tamamlanmış 30/60 günlük özellik üretilmez.
- Pikselde indeks medyanı ve sonra AOI alan ağırlıklı özet sırası
  korunacak. CRS/30 m demek aynı grid başlangıcı demek değildir;
  eski Earth Engine grid/kenar ağırlığı ve sahne işleme sürümleri
  uzlaştırılmadan sayısal eşdeğerlik kabul edilmez. Sahne listesi,
  maske, grid, süre/bayt ve eski 2022 karşılığı birlikte raporlanır.
- Erişim engeli, ücret/giriş gereksinimi, eksik sahne listesi veya
  sınır aşımında durulur; tokenlar yazdırılmaz/kaydedilmez.

Bu yalnız küçük uyumluluk provasıdır; tüm 2024 bitki örtüsü üretimi,
özellik kabulü, yeni tahmin/etiket/eğitim ve nihai merge yetkisi değildir.
Eski bilimsel kod ve veriler korunur, yeni yol ayrı sürümde hazırlanır.

**Alternatif B:** 2024'ü yalnız meteoroloji kullanan ayrı yardımcı
sınama yönünde ele almak. Mevcut meteoroloji modelleri incelenebilir;
bu, 15 alanlı ana XGBoost'un aynı yöntemle ayrı yıl doğrulaması değildir.
Yeni indirme gereksinimini azaltabilir fakat model karşılaştırmasının
kapsamını değiştirir; kullanıcı yöntem tercihi olmadan seçilmeyecek.

Her iki yol da gözlem/olay/PU aktarımı açığını tek başına kapatmaz.
Bu iş, 2024 ana model sınamasının hangi somut girdide durduğunu ve
o girdiyi yöntemi değiştirmeden hazırlamak için neyin sınanması
gerektiğini ortaya çıkardı. Yeni prova henüz yürütülmedi.
