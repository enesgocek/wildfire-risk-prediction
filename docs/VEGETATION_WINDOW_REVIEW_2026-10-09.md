# Bitki örtüsü pencerelerinin mevsim karşılaştırması

Deney ve kayıt tarihi: 9 Ekim 2026. Amaç, günlük risk modeline aday NDVI/NDMI
özelliklerinin alan desteği ile güncellik dengesini incelemektir. Bu çalışma
model performansını, operasyonel veri erişimini veya bütün dönem serisini doğrulamaz.

## Kapsam ve yöntem

2018 eğitim yılının 1 Şubat, 1 Mayıs, 1 Ağustos ve 1 Kasım tarihlerinde 00:00
UTC kesim anları kullanıldı. Önceki örnekle aynı, sıralı kimliklerden eşit
aralıkla seçilen 32 hücre her karşılaştırmada korundu. Seçimde yangın etiketleri,
2024 doğrulaması veya 2025 final testi kullanılmadı. Dört tarihin sonuçları
bütün mevsimler/yıllar veya dört ilin tamamı için temsil iddiası taşımaz.

Landsat 8 Collection 2 Level 2 görüntüleri `[T−pencere,T)` aralığında seçildi.
16, 30 ve 60 günlük pencereler aynı yansıtım ve kalite politikasıyla incelendi.
Kırmızı/NIR/SWIR1 bantlarının ölçeği 0,0000275, ofseti −0,2; QA_PIXEL
dışlama bitleri 0, 1, 2, 3, 4, 5, 7; QA_RADSAT koşulu sıfırdır. Fiziksel
yansıtım aralığı ve pozitif indeks paydaları ayrıca denetlendi.
[Kaynak ve bant tanımları](https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C02_T1_L2).

NDVI ve NDMI piksel medyanları, EPSG:6933 üzerinde 30 m hesap ızgarasında AOI
kesişim alanıyla ağırlıklandırıldı. Aynı geçerli destek için gözlem sayısı,
en yeni geçerli görüntünün piksel yaşı ve geçerli görüntülerin piksel medyan
yaşı da özetlendi. Kaynak koleksiyonunun en son çekim zamanı tek başına her
hücrenin gerçek görüntü yaşı olarak kullanılmadı. Piksel medyan yaşı, indeks
değerinin tek bir görüntüye ait olduğunu ifade etmez.

Alan oranı QA, su, yansıtım ve kaynak kapsamı dışlamalarını birlikte yansıtır;
yalnız bulut oranı değildir. Sınır ağırlıkları nedeniyle birin biraz üzerindeki
oranlar korunur. `%90` destek eşiği yalnız karşılaştırma tanısıdır; model kabul
veya orman uygunluk kuralı olarak belirlenmedi.

## Ölçülen sonuçlar

Her hücre/tarih/pencere için toplam **384 özet**, 12 kalıcı ham JSON ve kaynak
kimlik/zaman kayıtları üretildi. Tamamen desteksiz hücre sayıları:

| Kesim tarihi, 2018 | 16 gün | 30 gün | 60 gün |
|---|---:|---:|---:|
| 1 Şubat | 5 | 4 | 0 |
| 1 Mayıs | 3 | 0 | 0 |
| 1 Ağustos | 0 | 0 | 0 |
| 1 Kasım | 3 | 0 | 0 |

AOI'nin en az %90'ında geçerli destek bulunan hücre sayısı, 16/30/60 günlük
pencerelerde sırasıyla Şubat için 15/15/25; Mayıs için 23/25/30; Ağustos için
22/29/30; Kasım için 18/29/30 oldu. Sıfır desteksiz hücre, bütün alanların
eksiksiz olduğu anlamına gelmez.

60 günlük pencerede destekli hücrelerin piksel medyan yaşı özetlerinin
medyanı Şubat 33,1; Mayıs 20,6; Ağustos 27,8; Kasım 32,3 gün oldu. 30 günlük
pencerede aynı tanım sırasıyla 7,6; 12,6; 15,7; 18,3 gündür. Bu dağılımlar
aynı piksel/zaman popülasyonuna dayanmıyor; daha geniş pencere daha eski
görüntülerle birlikte yeni destek alanları da getiriyor.

32 hücrelik her uzak istek için katalog okuma ve integral alma toplam süresi
2,91–5,38 saniye ölçüldü. En fazla iki istek eşzamanlı yürütüldü. Sabit istek
sırası, Earth Engine önbelleği ve paylaşılan kapasite nedeniyle bu ölçümler
soğuk veri indirme hızı veya bütün dönem bitiş süresi olarak kullanılamaz.

Karşılaştırma grafiği: `outputs/figures/landscape/seasonal_v1/window_comparison_2018.png`
ve aynı isimli SVG. Ölçümler `outputs/reports/landscape/seasonal_v1/review_32cells.json`
ve `comparisons_32cells.csv` içindedir.

## Günlük geçmişe göre seçim örneği

Her kesim tarihinden bir gün önce başlayıp dokuz gün sonrasına uzanan 44 örnek
tarih, 32 hücre ve üç pencere üzerinden **4.224 satırlık geriye dönük** tablo
üretildi. En yakın geçmişteki destekli özet, deneysel olarak en fazla sekiz
gün korunuyor; piksel yaşları tahmin gününe kadar ilerletiliyor. Bu kayıtlar
gerçek günlük yeni görüntü veya günlük yeniden hesaplanan medyan değildir.
Gelecekten geri doldurma, interpolasyon, komşudan doldurma ve sıfırla doldurma yok.

3.321 satırda geçmiş özet seçilebildi; 903 satır eksik kaldı. Eksik sayısı hem
özet öncesi/eskime sınırı örneklerini hem destek bulunmamasını kapsar; genel
veri boşluk oranı olarak yorumlanamaz. Sekiz günlük saklama süresi ve önerilen
yedi günlük üretim aralığı henüz model kalitesiyle sınanmış kararlar değildir.

Geçmiş yayımlanma/erişilebilirlik zamanı bilinmediği için `available_at` boş
bırakıldı. Aynı girdilerle hazırlanan **4.224 satırlık operasyonel uygunluk
kontrol örneğinde hiçbir satır erişim koşulunu geçmedi**. Bu, kaynağın
kullanılamayacağı sonucunu değil, mevcut kanıtla geçmiş operasyonel uygunluk
iddiasının kurulamayacağını gösterir.

## Doğrulama ve izlenebilirlik

Geometri, kaynak dosyaları, ortak yöntem kodu ve çıktı SHA-256 değerleri
manifestlere kaydedildi. Bağımsız yerel denetim, ortak dönüşüm fonksiyonunu
çağırmadan ham integrallerden bütün 384 özet değerini tekrar hesapladı.
8.448 günlük örnek satırında zaman/anahtar/eksiklik koşulları, en yakın
uygun geçmiş kaydın seçimi ve 3.321 destekli satırın yaş ilerletmesi denetlendi.
Bu denetim ayrı uydu kaynağı veya saha gözlemiyle doğrulama değildir.

Yeni bitki örtüsü, mevcut arazi, yapılandırma ve hava politikası/kalitesi için
**71 ilgili test geçti**; yeni kodlarda Ruff başarılı. VM, donmuş bulut
paketleri ve önceki `v1` arazi/ilk örnek kayıtları değiştirilmedi. Yangın
etiketi üretilmedi; final test erişimi olmadı.

Ana kayıtlar:

- `data/raw/vegetation/seasonal_v1/`: 12 ham kaynak/integral JSON.
- `data/interim/vegetation/seasonal_v1/snapshots_32cells.csv`: 384 özet.
- `data/interim/vegetation/seasonal_v1/manifest_32cells.json`: kaynak/çıktı sözleşmesi.
- Aynı ara dizinde `daily_asof_retrospective_pilot.csv` ve `daily_asof_operational_pilot.csv`.
- `outputs/reports/landscape/seasonal_v1/local_readback.json`: bağımsız geri okuma sonucu.

## Bütün dönem için sonraki karar

16 günlük pencere tek başına üretim adayı olarak yeterli kapsam göstermedi.
30 günlük güncel ve 60 günlük geniş özetlerin **ayrı aday özellikler** olarak
korunması, ilk geniş kapsam denemesinde karşılaştırılması planlandı. Eksik
30 günlük değer 60 günlük değerle sessizce değiştirilmeyecek. Hangi pencerenin
tahmin başarısına katkı verdiği ancak geçerli etiketlerle eğitim dönemi
karşılaştırmasından sonra belirlenebilir.

Her gün aynı geçmiş görüntüleri tekrar hesaplamak yerine, sürümlü ve kaynak
kimlikleri kayıtlı periyodik özetlerin günlük tabloya geçmişe göre eşlenmesi
ölçekleme adayıdır. Bütün yıllara geçmeden önce 2.899 hücreyi içeren bir eğitim
ayında grup boyutu, yeniden başlatma, farklı sınır hücreleri, destek dağılımı,
ölçülen süre ve çıktı boyutu denetlenmelidir. Bu geniş deneme henüz yapılmadı;
32 hücre süresinden bütün dönem için süre garantisi verilmedi.

Önceki arazi tablosundaki 17 küçük sınır hücresi incelemesi, habitat politikası
ve kaynak erişilebilirliği açık konulardır. Yangın gözlemlerinin `unknown`
durumu ve negatif etiket yasağı bu özellik hazırlığıyla değişmez.
