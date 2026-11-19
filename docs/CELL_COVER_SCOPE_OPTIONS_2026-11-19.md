# Risk hücresi kapsamı karşılaştırması ve karar — 19 Kasım 2026

Olay kaynağı araması sürerken, ondan bağımsız olan hücre kapsamı
kararının etkisi hesaplandı. 27 Ekim'de kabul edilen iki ayrı kontrol
korunuyor: risk hücresinin kapsamı ile olay adayının yerel örtüsü farklı
konular. Araştırmacı aşağıdaki karşılaştırmadan sonra A yönünü seçti:
asgari yüzdeyle ek eleme yapmadan inceleme havuzunu korumak. Ek bir
örtü oranı eşiği seçilmedi, hücre silinmedi veya yangın etiketi atanmadı.

## Yapılan işlem ve sonuç

Önceki CGLS 2017 hücre ölçüleri, CORINE 2018'in aynı çalışma alanı
kesişimlerinde yeni hesaplanan sınıf alanlarıyla karşılaştırıldı.
2.899 coğrafi hücrenin tamamı hesaplandı. Aşağıdaki karar paydası,
önceden onaylı su kuralını geçen **2.889 hücre**. Sınırdaki hücrelerin
yalnız dört illik çalışma alanına giren kısmı kullanıldı; hepsi tam
25 km² sayılmadı.

| Haritadaki pay için betimsel kesim | CGLS 2017 hücre sayısı | CORINE 2018 hücre sayısı | Kesimi sağlama konusunda haritaları farklı hücre |
|---|---:|---:|---:|
| Herhangi bir kesişim, >0 | 2.805 | 2.592 | 231 |
| En az %10 | 2.574 | 2.366 | 262 |
| En az %25 | 2.353 | 2.115 | 320 |
| En az %50 | 2.044 | 1.656 | 478 |
| En az %75 | 1.625 | 945 | 770 |

Kesimler bir başarı ölçütüne göre optimize edilmedi ve ekolojik kabul
eşiği sayılmadı. CGLS'de ağaç/çalı ayrık sınıfları; CORINE'de
311/312/313/322/323/324 kodlarının betimsel toplamı kullanıldı. Bunlar
eşdeğer doğal orman tanımları değil. CORINE 324 geçişli örtü içeriyor;
tarımsal/doğal mozaik 243'ün bilinmeyen doğal payı bu toplama katılmadı.
Önceki noktalar için sınıf ve harita sınırları
[CORINE incelemesinde](CORINE_SUPPORT_REVIEW_2026-11-04.md) açıklanıyor.

Bu farklar gerçek 2017→2018 örtü değişimi veya hangi haritanın doğru
olduğunu ölçmüyor. Tarih, sınıf tanımı, çözünürlük ve ölçüm paydası farklı:
CGLS paydası önceki haritalanmış destek, yeni CORINE paydası bütün AOI
kesişimi. Yeni CORINE ölçüsünde anlamlı eksik harita alanı görülmedi;
en büyük eksik pay 3,90×10⁻⁸ düzeyindeki sayısal kapanış farkıydı.
İki ürün de 2021–2023 olay tarihi örtüsünü tek başına doğrulamıyor.
Bu karşılaştırma yeni bir tahmin zamanı girdisi olarak bağlanmadı.

Somut örnek: CGLS 2017'de ağaç/çalı payı sıfır olan dokuz hücrede
CORINE seçili sınıf kesişimi var. Bunların bazıları çok küçük sınır
parçaları; biri yalnız 0,00321 km² AOI kesişimine sahip. Dokuz yeni
doğal orman veya harita hatası doğrulanmış sayılmadı. Sıfır sınıf
payıyla kalıcı dışlama kararı arasındaki belirsizlik görünür kılındı.

## Sunulan kapsam yönleri

**A — Önerilen:** Orman/çalılık parçalarının bulunduğu karma hücreleri
araştırma dışında bırakacak bir asgari yüzde koymadan, su kuralını geçen
2.889 hücreyi inceleme ve veri hazırlama havuzunda korumak. Oranlar
bağlam olarak taşınır; olayın yerel örtüsü ayrı kabul protokolünden geçer.
Bu, bütün hücrelerin güncel doğal orman olduğu veya hepsine gerçek risk
değeri yayımlanabileceği anlamına gelmez. Yeni güvenilir örtü kanıtı
gerekçeli bir kapsam güncellemesi gerektirebilir.

**B — Daha dar araştırma nüfusu:** Yalnız tarihsel CGLS 2017 haritasında
orman/çalı payı en az %50 olan hücrelere odaklanma yönünü seçmek.
Bu betimsel kesimde 2.044 hücre kalır, 845 karma/diğer hücre ana
inceleme nüfusunun dışında olur. Soru, orman parçalarının bulunabildiği
tüm hücrelerden orman/çalı baskın hücrelere daralır. Aynı %50 kesimi
CORINE'e uygulayınca 1.656 çıkması, harita seçiminin de sonuç üzerinde
etkili olduğunu gösterir. B seçimi tek başına kalıcı filtreyi uygulama
veya haritanın doğruluğunu kabul etme yetkisi sayılmayacak; sürümlü
kapsam sözleşmesi ayrıca somutlaştırılacak.

A önerisinin gerekçesi ana orman/çalılık yangını hedefini, hücredeki
diğer kullanımlar nedeniyle erken daraltmamak ve önceden kabul edilen
yerel olay örtüsü kontrolünü korumak. Bu bir model başarısı iddiası değil.
Her iki yön de etiket, eğitim veya nihai birleştirme onayı değil.
Birinci aşamadaki olay/PU/değerlendirme açıkları bu kapsam tercihiyle
kapanmayacak.

## Araştırmacı kararı ve doğrulanan kapsam

19 Kasım'da araştırmacı **A — karma hücreleri koru, asgari yüzdeyle
eleme yapma** yönünü açıkça seçti. Yeni sürümlü kayıt
[`cell_scope_direction_v1.json`](../configs/cell_scope_direction_v1.json).
Önceki hash ile bağlı su ve iki aşamalı örtü tasarımı ayarları
değiştirilmedi. Ek yüzde filtresi uygulanmadığı için inceleme havuzu
aynı 2.889 hücreden oluşuyor. Yalnız sayılar değil, bütün hücre
anahtarlarının da önceki su kapsamıyla aynı olduğu doğrulandı.

Bu karar inceleme/veri hazırlama nüfusuna aittir. Bütün habitat
protokolünün kabulü, bütün hücrelerin güncel doğal örtüsü veya geçerli
risk tahmini yayımlama izni değildir. Her olay adayının yerel ve
zamana uygun örtü kanıtı ayrı kalacak. Nihai etiketli birleştirme için
önceden kararlaştırılan son kontrol/onay gerekliliği sürüyor.

Karar doğrulama komutu `python scripts/quality/verify_cell_scope_direction.py`.
Makbuz:
`outputs/reports/dataset/cell_scope_direction_v1/20261119T002729Z_43151c8b/readback.json`.
SHA-256 `0daacc4452907b20a0e86f1e0ac3a61c8c80b6f0f89975e580800c3d1c3f65b7`.

## Kontrol ve izlenebilirlik

Komut `python scripts/quality/audit_cell_cover_scope.py`.
Hesap tamamen yerel ve ağ engelli. Sınırlar EPSG:6933'te 100 m ve
50 m adımlarla yoğunlaştırılıp doğrulanmış raster CRS'sine dönüştürüldü.
Kategorik raster interpolate edilmedi. Sınıf alanları exactextract
kapsama hesabıyla ölçüldü. Bütün 2.899 hücrede iki adımın odunsu payları
karşılaştırıldı; en büyük fark **3,87×10⁻⁷**. Mekânsal sıraya yayılmış
beş hücre ayrıca raster kareleriyle doğrudan Shapely kesişiminden
hesaplandı; en büyük pay farkı **3,02×10⁻¹¹** altında. Bu iki sayısal
hesap aynı haritaya dayanıyor; bağımsız arazi doğrulaması değil.

Kaydedilmiş CSV, standart Python CSV okuyucusuyla ayrıca okunup altı
kesimin sayımları uzlaştırıldı. Girdi/çıktı hash'leri, şema/anahtarlar,
alan paydası ve kapalı hedef durumu kontrol edildi. Ruff/biçim geçti.
Su kapsamı, hedef kabul korumaları ve arazi hesaplarına ait mevcut
40 davranış testi de bu oturumda geçti; bütün depo testi veya bağımsız
arazi doğrulaması olarak sunulmadı.
Eski üretim dosyaları değişmedi; yerel 2024/2025 kayıtları okunmadı.

Hesap:
`outputs/reports/dataset/cell_cover_scope_v1/20261119T002103Z_099cd518/readback.json`.
SHA-256 `1831e4d0f67789883d9d98f636c6df23194609dbf53a3f74b127ab8c68993f59`.

Görsel komutu `python scripts/quality/plot_cell_cover_scope.py`.
[Karşılaştırma görseli](../outputs/reports/dataset/cell_cover_scope_visual_v1/20261119T002356Z_ae047e23/scope_options.png).
Görsel makbuzu SHA-256
`4aa8bec05e3e14d3eac9262a72da45bddfca9e78e17f36c8b574eb548463a9a4`.
Görsel asistan tarafından kontrol edildi; insan incelemesi veya seçimi
olarak kaydedilmedi. Çıktı CSV/PNG/ham raster Git'e eklenmez.
