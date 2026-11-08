# Manavgat 2021 için yayımlanmış başlangıç saatleri — 8 Kasım 2026

Atalay, Sunar ve Dervişoğlu'nun makalesinde OGM yangın kayıt fişlerinden
aktarılan yedi başlangıç saati ve ayrı ilk müdahale saatleri var. Yayının
5. sayfasındaki Tablo 1 ile 6. sayfasındaki Şekil 2 aynı numaraları
kullanıyor. Açık yayındaki başlangıç işaretleri yaklaşık konum bağlamı
veriyor. Makalenin veri erişim açıklamasında uydu verisi belirtiliyor.
Özgün nokta koordinatlarının açık bir tablosu bulunmadı.
[Atalay vd., 2025](https://doi.org/10.3390/ijgi14020065) · [İTÜ yayın kaydı](https://research.itu.edu.tr/en/publications/spatial-autocorrelation-analysis-of-co-and-nosub2sub-related-to-f/).

## Tarih ve konum kontrolü

Türkiye saatindeki yedi başlangıç UTC'ye çevrildi. Örneğin 4 numaralı
kayıt 29 Temmuz 01.30 yerel saatten 28 Temmuz 22.30 UTC'ye geçiyor.
Tabloya göre 28 Temmuz'da yerel saatle üç, UTC'de dört kayıt var.
Makale metnindeki dört kayıt ifadesi ile yerel tarih tablosu arasındaki
fark için UTC kullanıldığı varsayılmadı. Hesapta tablodaki açık tarih
ve saat kullanıldı. [Atalay vd., Tablo 1](https://doi.org/10.3390/ijgi14020065).

Şeklin boylam ve enlem etiketleri ile simge merkezleri elle okundu.
Her eksende doğrusal dönüşüm kuruldu. Bir eksen etiketi sırayla
çıkarıldığında en büyük tahmin farkı boylamda 0,00254°, enlemde
0,00044°. Bu ölçüm yalnız eksen okumasının iç tutarlılığını gösterir.
Simgenin özgün noktadan ne kadar kaydırıldığı ve saha konumunun hatası
ölçülemedi. Yaklaşık merkez çevresindeki 1, 2 ve 3 km senaryoları
duyarlılık denemesidir. 1 km senaryosunda **7 vakanın 6'sı** birden çok
5 km hücreye dokundu. Hiçbir işaret için tek başlangıç hücresi kabul edilmedi.

## Yerel uydu karşılaştırması

Her vaka için yalnız 2021 uydu adayları, aynı UTC `(T,T+24h]` penceresi
ve belirtilen yarıçapla tarandı. Katalog satırları, bildirilen başlangıcın
öncesi ve sonrası olarak ayrıldı. Aşağıdaki sayılar aynı olay olduğu
varsayılmadan bulunan tespit satırlarıdır. Önceden mevcut 1 km/48 saat
gruplaması yalnız duyarlılık tanısı için kullanıldı.

| Vaka | Tablodan UTC başlangıç | Başlangıçta veya sonrasında 1 / 2 / 3 km içindeki kayıt sayısı | 2 km içindeki kayıtların keşif kümesi |
| --- | --- | --- | --- |
| 1 | 28 Temmuz 08.58 | 12 / 41 / 81 | Başlangıçtan önce kayıtlı üyesi yok |
| 2 | 28 Temmuz 13.00 | 0 / 1 / 11 | Başlangıçtan önce kayıtlı üyesi var |
| 3 | 28 Temmuz 20.45 | 7 / 21 / 38 | Başlangıçtan önce kayıtlı üyesi yok |
| 4 | 28 Temmuz 22.30 | 2 / 20 / 46 | Başlangıçtan önce kayıtlı üyesi yok |
| 5 | 31 Temmuz 16.00 | 0 / 1 / 2 | Başlangıçtan önce kayıtlı üyesi var |
| 6 | 2 Ağustos 10.00 | 0 / 0 / 0 | İncelenen dairede uygun satır yok |
| 7 | 3 Ağustos 04.30 | 4 / 27 / 69 | Başlangıçtan önce kayıtlı üyesi var |

2 km içindeki altı vakanın üçünde, başlangıçtan sonra görünen kayıtlar
daha önce başlamış keşif kümelerine bağlı. Bu gözlem tek başına
vakaların aynı fiziksel yangın olduğunu kanıtlamaz.

6 numaralı vakada 1 km dairesinin dokunduğu iki hücrenin üç komşu
nominal paketi okundu. Yaklaşık merkez hücresinde **430 seçili kara,
sıfır termal merkez**, komşu hücrede **434 seçili kara, 43 termal
merkez** vardı. İkinci sayı hücrenin tamamına aittir ve dairenin içindeki
sayım değildir. Bu fark, tek bir yaklaşık hücre üzerinden yangının
algılandığına veya kaçırıldığına karar vermeyi engeller.

## Kanıt sınırı ve doğrulama

Yedi saat, bağımsız idari kaynak kökenli **zaman referansı** olarak
saklandı. Vakalar aynı büyük yangın döneminden geldiği için genel
değerlendirme örneklemi oluşturmaz. Özgün başlangıç geometrisi ve
olay kimlikleri gerekir. Hedef alanı boş, günlük gözlem `unknown`,
pozitif ve negatif etiket izinleri `false` kaldı.

Üretici `python scripts/quality/review_manavgat_reported_starts.py`.
Yerel makbuz `outputs/reports/dataset/manavgat_reported_starts_v1/20261108T022757Z_358ef972/readback.json`.
SHA-256 `cf24f1c2839f3f92942de1d569644e599a84a854b76cb5263cd6e1871e3c7b9e`.
Yayın PDF kimliği, UTC dönüşümleri ve 21 yarıçap sayımı ayrıca kontrol
edildi. 36 ilgili test ve kod biçim kontrolleri geçti.
