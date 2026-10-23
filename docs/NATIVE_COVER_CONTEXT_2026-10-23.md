# İlk tespit piksellerinin konum ve örtü bağlamı

23 Ekim 2026. Amaç: orman/çalılık kapsamını uygulamadan önce arşivdeki
ilk tespitleri gerçek kaynak piksellerine bağlamak ve merkez sınıfının
çevredeki örtüyü ne kadar temsil ettiğini incelemek. Bu çalışma aynı
21 amaçlı aday hücre-gündeki 25 farklı ilk tespit noktasına aittir;
bütün veri setinin hata oranını ölçmez.

## Tamamlanan işlem ve bulgular

18 yerel yangın/konum dosyası çifti kullanıldı. 25 arşiv kaydının tamamı,
sensör ve altı dakikalık kaynak aralığı içinde tekil yuvarlanmış koordinatla
eşleşti. Native satır/sütun, seyrek koordinat dizisi ve yangın güven sınıfı
uzlaştırıldı. 25 farklı native piksel anahtarı korunuyor. Arşiv/native merkez
farkı en fazla 0,607 metredir; bu değer **yuvarlanmış kayıt uyumudur**,
uydunun gerçek dünyadaki konum doğruluğu değildir.

Her merkezin aynı 32 satırlık tarama içindeki 3×3 komşuluğundan yaklaşık
dört köşe üretildi. EPSG:6933 üzerinde komşu dört merkezin ortalamasıyla
kurulan alan, yerel 2017 örtü rasterinin dönüştürülmüş hücreleriyle kesiştirildi.
Resmî piksel köşeleri kullanılmadığı için sonuç yaklaşık destek alanıdır;
sensörün fiziksel görüş alanı, yanan alan veya gerçek yangın sınırı değildir.
FIRMS scan/track değerlerinden kuzeye hizalı kutu varsayılmadı.

| Ölçü | Bu 25 noktadaki sonuç |
|---|---:|
| Kaynak pikseli ve güven sınıfı eşleşen | 25 |
| Aynı taramada yaklaşık alan kurulabilen | 25 |
| Yaklaşık alanında birden fazla eski örtü sınıfı bulunan | 21 |
| Merkez sınıfı orman/çalı olmayan | 21 |
| Bu 21 noktanın yaklaşık alanında orman/çalı kesişimi bulunan | 9 |
| Native giriş kalite bitleri nominal olmayan | 0 |
| Residual bowtie bayrağı bulunan | 1 |

Dokuz nokta, önceki 500 m çevre tanısındaki dokuz kimlikle aynıdır; bu,
500 metrenin doğru hata sınırı olduğunu göstermez. Yeni hesap pikselin
yönelimini komşu kaynak merkezlerinden alır ve **alan kesişimini** ölçer.
Eski çalışma harita piksel merkezi sayıyordu; iki oranın paydası farklıdır.

Kaynak scan boyutları 0,37–0,65 km, track boyutları 0,36–0,73 km arasında.
Yaklaşık destek alanı 0,144–0,514 km² aralığında. Bunlar yangın büyüklüğü değildir.
Bütün yaklaşık alanlar mevcut harita sınıflarıyla kaplıdır; sayısal artık
oranı en fazla 4,43×10⁻¹³'tür. Eksik harita alanı olsaydı sıfır orman/negatif
etiket olarak doldurulmayacaktı; ayrı bilinmeyen pay olarak tutuluyor.

## Somut örnekler

| Kaynak kimliği | Tarih | 2017 merkez sınıfı | Yaklaşık alanda 2017 orman/çalı payı |
|---|---|---|---:|
| SNPP_815579_4958 | 15 Mayıs 2018 | Yerleşim | %6,86 |
| SNPP_815579_17606 | 15 Ağustos 2018 | Tarım | %0 |
| SNPP_815579_146808 | 15 Ağustos 2021 | Orman | %100 |

İlk örnek karışıktır: merkez yerleşimde diye otomatik eleme de, küçük
orman/çalı kesişimi var diye kabul de gerekçelendirilmiş değildir. İkinci
örnekte harita tarımsal bağlamı destekler; tek başına gerçek olay türünü
kanıtlamaz. Üçüncü örnekte eski örtü uyumu güçlüdür fakat harita ile tespit
arasında dört takvim yılı vardır; güncel örtü/bağımsız olay kanıtı yine gereklidir.

SNPP_815579_160642 kaydındaki residual bowtie işareti saklandı. Aynı yerin
yinelenen gözlenmesiyle ilgili ürün bayrağıdır; tek başına kanıtlanmış çift
yangın kaydı veya yanlış tespit sayılmaz. Olay gruplamasında ayrı değerlendirilir.
Bu bayrağın FRP sayımlarında çift sayım açısından önemi NASA kılavuzunda
açıklanır ([C2 kullanıcı kılavuzu, s. 4–5](https://ladsweb.modaps.eosdis.nasa.gov/archive/Document%20Archive/Science%20Data%20Product%20Documentation/VIIRS_C2_AF-375m_User_Guide_1.2.pdf)).

## Kapanan ve açık kalan konu

Bu sınırlı örneklerde **hangi kaynak pikseline baktığımız ve o pikselin
yaklaşık alanının eski haritayla kesişimi** artık dosya düzeyinde izlenebilir.
Bu, habitat sınıfını güncel olarak doğrulamıyor. Referans yılı farkı
10 noktada bir, dokuz noktada dört, altı noktada altı takvim yılıdır.
Yerel `data/raw/landcover` alanında yalnız 2017 rasteri bulundu.

Önerilen sıradaki iş aynı noktalar için **tahmin anından önce edinilmiş**
optik görüntü/örtü kanıtını incelemektir. 2017 haritası temel referans olarak
korunurken değişim, bulut, sınıf karışımı ve odunsu tarım belirsizliği kaydedilir.
Dynamic World 2015'ten başlayan 10 m sınıf olasılıklarıyla bir adaydır;
ürün sonucu bağımsız gerçeklik sayılmaz. Yıl sonu bileşiğini yıl başına
taşımak veya yangın sonrası çıplak zemini yangın öncesi örtü gibi kullanmak
uygun değildir. Geriye dönük edinim zamanı ile ürünün o tarihte yayımlanmış
olması farklıdır; model girdisi kullanımı ayrıca zaman sözleşmesine tabidir.
[Dynamic World resmî katalog](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1).

Bu tur yeni bulut/indirme kuyruğu başlatılmadı. Habitat alan eşiği seçilmedi,
kayıt silinmedi, pozitif/negatif etiket atanmadı. Olay gruplaması, bağımsız
olay değerlendirmesi ve günlük gözlem kabulü açık kalıyor. Orman/çalı
alanının bulunması bu üç soruyu tek başına çözmez.

## Kaynak ve doğrulama

FIRMS açıklaması koordinatları piksel merkezi, scan/track alanlarını
piksel boyutu olarak tanımlar ([resmî alan tanımı](https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html)).
Copernicus sınıflarında odunsu çok yıllık tarım orman/çalı olarak görünebilir;
bu nedenle doğal örtü anlamı otomatik çıkarılamaz
([resmî katalog sınıf tablosu](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_Landcover_100m_Proba-V-C3_Global)).
Kaynaklar 23 Ekim'de açıldı; özel hesap veya dış ileti kullanılmadı.

12 yeni davranış testi dahil **47 ilgili test** geçti. Kayıp/çoklu koordinat,
tarama sınırı, geçersiz komşuluk, bilinen dikdörtgen alanı, kısmi raster kesişimi,
nodata/sınıf 0 ve harita dışı bilinmeyen alan sınandı. İlk geliştirme çalışmasında
eski matris çarpımı uyarısı testleri durdurdu; yeni kod düzeltildi ve son
testler Future/Deprecation/PendingDeprecation uyarılarını hata sayarak geçti.
Bu sayı bütün depo test sayısı değildir. Dört yeni Python dosyasında lint/format geçti.

Sonuç: `outputs/reports/dataset/native_candidate_cover_v1/20261023T143656Z_90c1c93b/`.
Readback SHA-256: `65443618bddc95f01a453f0186473891112d9712b50289e3c4613ac71470568b`.
243 doğrudan girdi hash'i başta/sonda korundu; CSV tam geri okundu ve üç
çıktı hash'i bağlandı. 98 eski çiftin metadata/raporları okunmuş, yalnız
seçilen 18 çiftin ham içeriği yeniden kullanılmıştır; eski tam pilot denetimi
yeniden yapılmış sayılmaz. 2024'ün 2.960 satırı yalnız tarih alanıyla atlandı;
2025 kapalıdır. Gözlem unknown, etiket izinleri false, nihai birleştirme yok.

Görsel: `outputs/reports/dataset/native_cover_figure_v1/20261023T143957Z_fef6f9c8/native_cover_examples.png`.
PNG SHA-256: `bd7e4291347039302c45c7d297e3cb67bacd89f104cee01b64ae02a400d8d511`.
Üç örnek amaçlı seçildi; görsel açılarak metin/renk/örtüşme kontrol edildi.
Bu görsel kontrol araştırmacının bilimsel incelemesi değildir. İlk yerleşimde
eksen/legend yakınlığı giderildi; eski görsel çıktısı korunup yenisi üretildi.
