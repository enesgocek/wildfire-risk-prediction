# Piksel geometrisi ve veri hacmi — 4 Ekim 2026

Yaklaşık alan yöntemi tanı amaçlı kalıyor. Boyut düzeltmesi, gözlem eşiği veya
negatif etiket seçilmedi. 2024 üzerinden kural seçilmedi, 2025 açılmadı;
NASA Type teyidi ayrıca açık.

## Geometri incelemesi

Dokuz yerel eğitim dönemi dosyasındaki **1.176 seyrek termal tespit** incelendi:
928 S-NPP, 248 NOAA-20. Pilot dışındaki tespitler de geometri tanısına dahil.
Bu, dokuz dosyanın bütün tespitleri olup yılları/illerimizi temsil eden örneklem
değildir. Arşiv boyut referansı hâlâ önceki üç pilot kaydı; diğer tespitler
fiziksel doğruluk referansı sayılmadı.

- 1.145 tespitte tarama içi komşulardan yaklaşık poligon ölçülebildi.
- Tarama veya görüntü kenarındaki 31 kayıt korundu; ekstrapolasyon yapılmadı,
  ölçüleri boş bırakıldı. Bu sayı gözlenmeyen yer alanı değildir.
- Ölçümler yaklaşık 0,54–70 derece yerel sensör zenit açısını ve üç örnek
  birleştirme bölgesini kapsıyor. Zenit açısı uydu tarama açısıyla aynı değil.
- Konum ürününün ölçek/ofseti, eksik değerleri ve doğal sırası korundu. Örneğin
  6207 ham zenit değeri yaklaşık 62,07 derece. Her tespitin doğal konumu,
  yangın sınıfı ve seyrek ürün/konum ürünü zenit eşleşmesi kontrol edildi.
- Kaynak özetleri okumadan önce/sonra denetlendi; ham dosyalar değiştirilmedi.

[NASA geolocation ATBD](https://ladsweb.modaps.eosdis.nasa.gov/api/v2/content/archives/Document%20Archive/Science%20Data%20Product%20Documentation/Product%20Generation%20Algorithms/NASARevisedVIIRSGeolocationATBD2014.pdf)
örnek birleştirme bölgelerini ve arazi düzeltmesini açıklıyor. I-band bölge
geçişleri kodda 0 tabanlı 1280/2016/4384/5120 sınırlarına dönüştürüldü ve
sınır testleri eklendi. Merkezlerden çıkarılan köşeler kalibre edilmiş fiziksel
görüş alanı köşelerine eşit kabul edilmiyor.

Üç kontrolün önceki kenar ölçümleri yeni hatla tekrar eşleşti. Scan yönündeki
%1,08–9,19 ve track yönündeki %4,35–4,48 farklar, arşivdeki iki ondalıklı
boyutların ±0,005 km yuvarlama aralığının dışında. **Yuvarlama tek başına
farkı açıklamıyor.** Üçü de örnek birleştirme bölgesi geçişine komşu değil.

En büyük scan farkı olan kontrolün komşu merkez mesafeleri 506,68 ve 563,17 m;
3×3 komşuluğundaki yükseklik açıklığı 79 m. Bu, merkez aralıklarının tekdüze
olmadığına dair ölçümdür. Tüm ölçülen örneklerde scan aralığı asimetrisiyle
komşu yükseklik açıklığı arasındaki Pearson korelasyonu yaklaşık 0,516.
Bu ilişki nedensel açıklama, hata üst sınırı veya düzeltme katsayısı değildir.
Fiziksel görüş alanı, arazi düzeltmesi ve merkez hücresi tanımları henüz tam
çözümlenmedi. **Sabit bir yüzde düzeltmesi uygulamak için kanıt yok.**

[FIRMS alan öğreticisi](https://firms.modaps.eosdis.nasa.gov/content/tutorials/fire-footprint/)
nominal boyutlu gösterim dikdörtgeni tarif ediyor; scan/track değerini ya da
doğal piksel yönünü kullanmıyor. Fiziksel ayak izi için bağımsız doğruluk
referansı olarak kullanılmadı. [FIRMS alan açıklamaları](https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html)
scan/track bilgisini piksel boyutu olarak tanımlıyor. Nominal gösterim ve
doğal gözlem geometrisi birbirine karıştırılmayacak.

## Eğitim dönemi katalog kapasitesi

Ham uydu dosyası indirilmeden dört resmî CMR sorgusu yapıldı. S-NPP başlangıcı
2018-01-01, NOAA-20 başlangıcı mevcut FIRMS talebimizle aynı 2018-04-01;
bitiş 2023-12-31. İl poligonlarını çevreleyen dikdörtgen kullanıldı. Sayım
bu zaman/konum zarflarıyla kesişen katalog kayıtlarıdır; eşleşmiş indirme
listesi veya gerçek pilot piksel gözlemi değildir.

| Sensör | Yangın maskesi | Konum ürünü |
|---|---:|---:|
| S-NPP | 9.691 | 9.692 |
| NOAA-20 | 9.022 | 9.300 |
| Toplam dosya kaydı | 18.713 | 18.992 |

Toplam **37.705 katalog kaydı**. Sayılar tek başına yangın/konum eşleşmesini
kanıtlamıyor. Gerçek konum girdisi kimliği, eksik ürünler ve aynı zamandaki
farklı üretimler ayrıca incelenmeli. Sayı farkından doğrudan uydu arızası
veya pilotta gözlem yokluğu sonucu çıkarılamaz.

Katalog sayıları her ürün için mevcut 6 S-NPP / 3 NOAA-20 örneğinin ortalama
dosya boyutuyla çarpıldığında toplam **3,161 TiB** senaryosu çıkıyor.
Örneklerdeki en küçük/en büyük boyutlarla 3,069–3,280 TiB senaryoları oluşuyor.
Bunlar garanti alt/üst sınır veya tüm katalog boyutlarının toplamı değil;
örneklem yalnızca iki günü kapsıyor. Önceki tek günlük 2,91 TiB senaryosu
tarihsel tanı kaydı olarak korunuyor.

[CMR belgesi](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html)
CMR-Hits başlığının toplam sonuç sayısını verdiğini açıklıyor. Sorgu adresleri,
tek kayıtlık yanıtlar, istek kimlikleri ve dosya/kod SHA256 özetleri kaydedildi.
Toplu ham indirme başlatılmadı.

## Denetim ve sonraki iş

25 yeni testle toplam **148 test** geçti; kod/biçim kontrolleri başarılı.
Bağımsız geri okuma kayıt muhasebesini, ölçümsüz kenarların korunmasını,
kaynak/çıktı özetlerini, önceki üç kontrolün kenar ölçümlerini, jeodezik/eş
alan tutarlılığını ve hacim aritmetiğini sınadı. Fiziksel ayak izi doğruluğu
bu kontrollerle sertifikalandırılmıyor.

Sıradaki iş katalog metadata'sından aday yangın/konum dosya eşlerini ve
eksikleri belirlemek, ardından bölgesel erişim/yerinde işleme/partili işleme
planı hazırlamak. Nominal zaman eşleşmesi tek başına yeterli değil: gerçek
konum girdisi kimliği dosyanın InputPointer/ürün başlığından doğrulanmalı.
İncelenen CMR metadata'sında bu girdi kimliği yok; uzaktan başlık erişimi
veya dosya okuması ayrıca gerekecek. Manuel ham indirme tercihi korunuyor.
Yaklaşık alan yöntemi
nihai etikete taşınmadan önce sabit analiz ızgarasına yeniden örnekleme ve
sınır hassasiyeti araştırılacak. Gözlem eksikleri, bitki örtüsü paydası ve
dönemsel kapsam etkisi açık kalıyor.

Yerel çıktılar `outputs/reports/observation_coverage/` altında:

- `l2_geometry_diagnosis.json/.csv`: 1.176 kayıt, alt gruplar ve üç arşiv referansı.
- `l2_training_capacity_snapshot.json`: dört katalog sayımı ve hacim senaryoları.
- `capacity_*_cmr_response.json`: sorguların tek kayıtlık yanıtları.

Kaynak kodları `audit_l2_geometry.py` ve `snapshot_l2_capacity.py` altında.
Ham/ara veriler ve yerel raporlar Git kapsamı dışında.
