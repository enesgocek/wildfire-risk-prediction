# Tarama kalitesi ve zaman boşlukları — 5 Ekim 2026

14 Ocak 2019 eğitim örneğinin mevcut ham dosyaları tekrar okunarak piksel
merkezleri doğal tarama satırlarına, UTC saatlerine ve sensör/yörünge
kimliklerine bağlandı. Yeni ham indirme yapılmadı. Bu çalışma günlük etiket
üretmez; tek bir kış gününün bulguları bütün döneme genellenemez.

Önceki pilot belgelerinde “sekiz geçiş” olarak anılan sekiz dosya parçası
(granule), **yedi farklı sensör/yörünge kaydına** ait. S-NPP 10:18 ve 10:24
parçalarının yörünge numarası aynı: 37385. Ardışık parçalar bağımsız yeniden
gözlem gibi sayılmıyor. Sensör de kimliğe katılıyor; farklı uyduların aynı
numarası birleştirilmiyor.

## Sonuç

| Ölçüm | Sonuç |
|---|---:|
| Korunan model hücresi | 2.899 |
| Hücre/tarama satırı | 29.637 |
| Piksel merkezi kaydı, tekrarlar dahil | 1.782.400 |
| Bulut sınıfındaki merkez kaydı | 1.316.217 |
| Uygun giriş kalitesine sahip kara merkezi | 224.353 |
| Böyle bir kara merkezi bulunmayan hücre | 480 |
| En az bir uygun kara merkezi bulunan hücre | 2.419 |
| Bu 2.419 hücrenin en uzun zaman boşluğunun medyanı | 22,746 saat |
| Aynı ölçümün %95 yüzdeliği | 23,273 saat |

Sayımlar alan oranı veya benzersiz kara pikseli sayısı değildir. Tek bir
uygun merkezin bulunması da hücrenin tamamının gözlendiğini göstermez.
480 hücre için seçilen merkez kayıtlarında boşluk 24 saattir; bu, fiziksel
ayak izlerinin hiç kesişmediğini kanıtlamaz.

Dosyaların tamamındaki 1.617 taramanın geolocation `scan_quality` değeri
sıfır. Tarama modları 1.010 gündüz ve 607 gece; bu sayılar AOI dışında kalan
taramaları da içerir. Tarama kalite bayrağının sıfır olması bulutsuz gözlem
anlamına gelmez. Yangın giriş QA'sı, artık bowtie ve on yangın maskesi sınıfı
ayrı sayıldı; hiçbir yangın sınıfı uygun kara tanısına katılmadı. Listelenen
günün pilot alanında termal yangın tespiti yok.

## Yöntem ve denetim

- Her 32 doğal satır bir taramaya bağlandı. Kaynak TAI93 saatleri dosyadaki
  artık saniye bilgisiyle UTC'ye çevrildi; eski zaman CSV'sinin bütün
  zaman/mod/kalite sütunlarıyla tam eşleşme arandı.
- Günlük pencere `(T,T+24h]`. Gün sınırını aşan taramalar
  `boundary_unknown` olarak tutulur, boşluk hesabına dahil edilmez. Bu
  örneğin 1.617 taraması pencerenin tamamen içinde.
- Kara tanısı: `fire_mask=5`, giriş QA bitleri 0–6 nominal ve artık bowtie
  biti 22 kapalı. Bu bir üretim uygunluk veya negatif etiket kuralı değildir.
- Tarama zaman zarfı, seçilen merkezlerin edinim saatlerini sınırlar;
  hücrenin o süre boyunca kesintisiz gözlendiğini göstermez. Zarflar
  birleştirilip gün başı/sonu dahil aralarındaki en uzun boşluk hesaplandı.
- Geolocation kalite alanının iki kodlu alt alanı ayrı okundu. SCE tarafını
  belirten bit 256 tek başına hata olarak yorumlanmadı. Kullanım/eleme
  eşiği seçilmedi; bu örnekte tüm kalite değerleri zaten sıfır.
- Sekiz parçanın bütün hücre/sınıf/QA sayımları önceki referanslarla tam
  eşleşti. Yeni CSV'ler bağımsız olay-süpürme hesabıyla geri okundu; 2.899
  hücrenin bütün zaman, yörünge, mod ve sayım alanları doğrulandı. CSV'deki
  `YYYYDDD.HHMM` kimlikleri sayı yerine metin olarak okunur.
- Kaynak, referans ve kod SHA-256 özetleri kaydedildi. Önceki alan geometrisi
  ve donmuş Colab paketleri değiştirilmedi. 17 ek testle tam küme 274 test.

Kaynak tanımları: [VIIRS C2 yangın ürünü kılavuzu, Bölüm 3 ve Ek 2](https://ladsweb.modaps.eosdis.nasa.gov/archive/Document%20Archive/Science%20Data%20Product%20Documentation/VIIRS_C2_AF-375m_User_Guide_1.2.pdf)
ve [NASA VIIRS L1B kılavuzu, Tablo 7 ve Ek D3](https://ladsweb.modaps.eosdis.nasa.gov/api/v2/content/archives/Document%20Archive/Science%20Data%20Product%20Documentation/NASA_VIIRS_L1B_UG_August_2021.pdf).

Yerel çıktılar `outputs/reports/observation_coverage/` altında:
`observation_timing_2019-01-14.json`, `_grid.csv`, `_scan_grid.csv`,
`_all_scans.csv` ve `_readback.json`. Üç CSV toplam yaklaşık 7,93 MB.
Günlük gözlem `unknown`, negatif etiket izni `false` olarak kaldı.

## Sonraki adım

Eğitim döneminde yaz, yangın tespiti bulunan ve farklı bulut/tarama koşullarını
temsil eden küçük kontrol örneklerinin envanteri hazırlanmalı. Tek kış günüyle
eşik seçilmeyecek. Daha geniş kontrol sonrasında gözlem/etiket seçenekleri
çalışma planında değerlendirilecek; üretim kuralı, tam dönem bulut işi ve NASA Type teyidi
henüz tamamlanmış sayılmıyor.
