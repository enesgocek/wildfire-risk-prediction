# Habitat kapsamı ön incelemesi — 10 Ekim 2026

## Amaç ve yöntem

Bitki örtüsünün 2018–2023 hazırlığı sürerken, modelin tahmin üreteceği alan
kapsamını gerekçelendirmek için kabul edilmiş statik örtü tablosu incelendi.
Antalya, Muğla, İzmir ve Mersin'in 2.899 hücresi korunarak örtü bileşimi,
alan paydaları ve sayısal destek işaretleri raporlandı. Habitat uygunluğu
henüz karara bağlanmadı; hiçbir satır elenmedi veya yangın etiketi oluşturulmadı.

Girdi `data/interim/landscape/v1/grid_static.csv`; kaynak manifesti,
grid/AOI geometrileri, özgün örtü tablosu ve raster SHA-256 değerleri denetlendi.
Yeni komut `scripts/landcover/review_habitat.py`, ortak yöntem
`src/wildfire_risk_prediction/habitat_review.py` içindedir. İnceleme çevrimdışıdır;
Earth Engine isteği, VM değişikliği veya paket kurulumu yapmaz. Her çağrı yeni
kimlikli çıktı oluşturur; önceki kabul tablosunu ve raporları değiştirmez.

Örtü oranlarının paydası kaynak rasterin kapsadığı alandır. Sınıf alanı,
bu oran ile `covered_area_km2` çarpılarak hesaplandı. AOI alanı ayrıca tutuldu;
AOI ile raster desteği sessizce birbirinin yerine kullanılmadı. Eşik senaryolarının
alan sütunu, eşiği sağlayan hücrelerin **tam raster kapsamını** gösterir;
o hücrelerin içindeki yalnız orman alanı değildir.

## Bulgular

AOI alanı yaklaşık 60.727,114 km². Raster sınıf özetinde orman 33.834,595 km²,
çalılık 7.831,543 km², otsu örtü 8.910,385 km², tarım 7.528,813 km²,
yerleşim 1.820,707 km² ve su 443,217 km². Bunlar 2017 referans haritasının
sınıf alanlarıdır; güncel arazi durumu veya yüzde ağaç kapalılığı değildir.
Doğal bitki örtüsü orman, çalılık ve otsu sınıfların toplamıdır; bu toplam
ile alt sınıflar ayrıca toplanamaz. Listelenmeyen raster sınıfları da vardır.

Haritada 10 hücre tamamen su sınıfındadır (oran 1'e 10⁻⁹ mutlak toleransla
eşit). Bilinmeyen sınıf payı pozitif olan hücre yoktur; bu, haritanın hatasız
olduğu anlamına gelmez. Önceki arazi incelemesindeki 17 destek alanı işareti
yeniden görüldü; toplam AOI alanları yaklaşık 1,010 km². Arazi destek/AOI
oranı 0,99–1,01 dışında olduğunda inceleme işareti verildi, oran kırpılmadı.
Bu aralık model uygunluk veya veri eksikliği kararı değildir.

Üç örtü tanımı için %1, %10, %25, %50 ve %75 olmak üzere 15 keşif senaryosu
hesaplandı. Eşitlik sınırı dahil edildi. Aşağıda bazı hücre sayıları yer alıyor:

| Eşiği sağlayan örtü oranı | En az %10 | En az %25 | En az %50 |
|---|---:|---:|---:|
| Orman | 2.367 | 2.083 | 1.676 |
| Orman + çalılık | 2.574 | 2.353 | 2.044 |
| Orman + çalılık + otsu örtü | 2.791 | 2.694 | 2.491 |

Bu eşikler seçilmiş veya literatürden doğrulanmış habitat kuralları değildir.
Kapsamın tanıma ne kadar duyarlı olduğunu gösterir. Yangın sonuçlarına,
2024 doğrulamasına veya 2025 final testine bakılarak seçim yapılmadı.

## Kontrol ve kanıt

Gerçek çıktı dizini:
`outputs/reports/habitat/review_v1/20261009T235212Z_3c2c021b/`.
`cells.csv` bütün 2.899 hücreyi, `review.json` özet ve kaynak hash'lerini,
`independent_readback.json` ayrı sınıf-formülü karşılaştırmasını tutar.

- Statik tablo SHA-256: `bd9b2a27e6234d97e41df11dac59fb7bc82242ef282ff60ac75d83cbc3fb0f82`.
- İnceleme CSV SHA-256: `76ab3a1dc632be7764548699342aaa3d933166e4d0ccb0d51ad3ea2df92ba14a`.
- İnceleme JSON SHA-256: `326c1c0197f3cb46aafbf6f4ee62478d1953ad3975fc13f99f9a6c5de3d31d5b`.

Habitat ve mevcut arazi davranış kontrollerinde 28 test geçti. Gerçek CSV
yeniden okundu; bağımsız kontrol parçası özgün raster sınıf sütunlarından
üç bileşimi ve 15 eşik sonucunu tekrar hesapladı. Bu, saha/uzman habitat
doğrulaması değildir; ham arazi integrallerinin eski denetimini yeniden yürütmez.

10 Ekim 02:52 Türkiye saati süreç sorgusunda bitki örtüsü üst süreci canlı,
Mayıs 2018 hazırlığı `running`. Üretim kodu, grid, kilit dosyası ve paket
ayarlarıyla bağlı kaynak hash'leri ayrı kontrol edildi; değişiklik yok.

## Açık kararlar ve sonraki iş

2017 haritasının sonraki yıllardaki eskimesi ve tarihsel yayımlanma zamanı
belirsizdir. Her hücre `habitat_eligibility=undecided` olarak kaldı;
negatif etiket izni verilmedi ve final test okunmadı. Su/kıyı hücrelerinin
coğrafi incelenmesi, orman–çalılık kapsamının danışmanla gerekçelendirilmesi
ve kapsama ilişkin seçim yanlılığının raporlanması gerekir.

Uzun hazırlığı beklerken bağımsız ilerleyebilecek sonraki aşama, aday yangın
tespitlerinin olay gruplaması sözleşmesi ve meteoroloji/örtü/olay tablolarının
birleştirme denetimidir. Nihai etiket üretimi, gözlem ve kaynak belirsizlikleri
çözülmeden tamamlanmış kabul edilmez.
