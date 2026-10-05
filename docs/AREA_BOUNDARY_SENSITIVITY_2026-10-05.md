# Yaklaşık gözlem alanının sınır hassasiyeti — 5 Ekim 2026

Drive saklama denemesi geçtikten sonra 14 Ocak 2019'un mevcut sekiz geçişli
alan çıktısıyla ilerledik. Yeni uydu indirilmedi; 2024/2025 okunmadı. Bu çalışma
fiziksel ayak izi doğrulaması veya nihai gözlem yöntemi seçimi değildir.

## Karşılaştırma

Mevcut nominal yangınsız kara poligonlarına -100/-50/-25/0/+25/+50/+100
EPSG:6933 koordinat metresi daraltma/genişletme uygulandı. Bu koordinat
mesafeleri her yönde gerçek yer mesafesine eşit değildir; değerler kalibre
edilmiş hata payı, güven aralığı veya etiket eşiği sayılmaz. İşlem, geçişlerin
birleşim sınırına uygulanır; her uydu pikselinin fiziksel sınırını modellemez.

Önce komşu hücrelerin gözlem parçaları birleştirilir; analiz hücresi kenarı
uydu sınırı gibi daraltılmaz. Her hücrenin çevresinde en büyük ofsetten daha
geniş komşuluk korunur. AOI dışındaki gözlem bilinmediğinden bütün senaryolar
aynı 100 koordinat metresi iç sınırla karşılaştırılır. AOI delikleri korunur.

Orijinal nominal kara birleşimi 36.011,819 km². Karşılaştırma alanı
60.236,279 km²; AOI kenarından 490,835 km² dışarıda bırakıldı. 2.899 hücrenin
tamamı raporda tutuldu; iç karşılaştırma alanı kalmayan 22 hücrenin oranı
boş bırakıldı. Sıfır senaryosunun alanı 35.787,888 km² (%59,413).

| Koordinat ofseti | Karşılaştırma alanında yaklaşık kapsam |
|---|---:|
| -100 m | %56,563 |
| -50 m | %57,979 |
| -25 m | %58,694 |
| 0 m | %59,413 |
| +25 m | %60,124 |
| +50 m | %60,816 |
| +100 m | %62,147 |

Toplam kapsamın küçük değişmesi, her hücrenin aynı derecede kararlı olduğunu
göstermez. Küçük AOI parçalarında oran daha fazla oynayabilir. Bu ölçümden
bir gözlem eşiği veya otomatik negatif etiketi çıkarılmadı.

## Denetim ve sınırlar

CSV geri okuması bütün hücre/alan/oran değerlerini ve kaynak SHA256 özetlerini
kontrol eder. Sentetik testler komşu hücre sınırını, boş gözlemi, AOI deliğini,
dar parçayı, örtüşme ve dışarı taşmayı, analitik alanları ve bağımsız global
birleşim karşılaştırmasını sınar.

Gerçek örnekte doğrudan global birleşimle yapılan önceki hesap ayrıca korundu.
Yerel komşuluk hesabıyla sıfır senaryosu ve paydalar eşleşiyor; ofsetli
geometriler tam aynı değil. En büyük hücre alan farkı yaklaşık 26,64 m²,
senaryo toplamında en büyük fark yaklaşık 48,03 m² (0,000049 km²).
Bu farklar ayrıca raporlandı; hesap yolları için eşdeğerlik toleransı veya
fiziksel hata sınırı seçilmedi. Bu araç üretim etiketi için onaylı yöntem değildir.

Yerel çıktılar `outputs/reports/observation_coverage/` altında:

- `area_boundary_sensitivity_2019-01-14.json/.csv`: senaryolar ve bütün hücreler.
- `area_boundary_sensitivity_readback.json`: kaynak/CSV geri okuması ve
  global/yerel hesap farkları.

Önceki global hesap `outputs/verification/area_boundary_global_reference.*`
altında korunur. Kaynak geometri/CSV ve ham uydu dosyaları değiştirilmez.
Günlük gözlem `unknown`, negatif etikete izin `false` kalıyor.

Sıradaki bilimsel adım sabit analiz ızgarasına yeniden örneklemenin çözünürlük
ve ızgara başlangıç konumuna duyarlılığını incelemek; ardından eğitim döneminde
tarama kalitesi, zaman boşlukları ve bitki örtüsü paydasıyla gözlem kuralını
değerlendirmek. Tam dönem Colab işleme planı bu yöntem netleştikten sonra
küçük partiler halinde kurulacak. NASA Type teknik teyidi ayrıca açık.
