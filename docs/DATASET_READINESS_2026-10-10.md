# Model veri setine geçiş planı

Kayıt tarihi: 10 Ekim 2026. Uydu gözlem kuyruğu çalışırken yerel özellik
hazırlığı ilerletilmektedir. Bu belge tamamlanmış model veri seti veya
operasyonel erişim onayı değildir.

## Hazır parçalar ve açık işler

| Parça | Mevcut kanıt | Sıradaki iş |
|---|---|---|
| Coğrafi anahtar | Dört il, 2.899 hücre, AOI kesişimleri | Küçük sınır hücrelerinin destek alanını izlemek; bütün hücreleri otomatik orman saymamak |
| Meteoroloji | 2018–2024 için 7.412.743 hücre-gün yerel denetimden geçti | Mevcut 11 aday özellik ve uygunluk bayraklarını anahtar/zaman sözleşmesiyle birleştirmek |
| Arazi ve örtü | 2.899 hücrenin statik tablosu hazır | Kıyı/sınır desteği, tarihsel harita erişimi ve habitat tanımını gerekçelendirmek |
| Bitki örtüsü | 32 hücre, dört mevsim, üç pencere denetlendi | Önce 2.899 hücrede tek eğitim kesim anı; ardından haftalık kesimlerle bir eğitim ayı |
| Uydu gözlem tanıları | VM üzerinde kalan eğitim ayları işleniyor | Oturum raporlarını ve sonuç arşivlerini yerelde geri okumak; eksik kaynakları ayrı tutmak |
| Olay ve hedef | İlk aktif tespit için 24 saatlik hedef tanımı kayıtlı | Tekrarlayan tespitleri olaylara gruplayıp belirsizlik ve güvenilir negatif politikası oluşturmak |
| Nihai tablo | Henüz oluşturulmadı | Kaynak manifestleri, anahtar/zaman kontrolleri ve bölünme denetimleriyle kabul etmek |

## Özelliklerin anlamı

Bir model satırı `(grid_id, prediction_timestamp_utc)` anahtarıyla tanımlanır.
Günlük kesim anı 00:00 UTC'dir. Sonraki 24 saat içinde **yeni olayın ilk aktif
uydu tespiti** hedeflenir; gerçek tutuşma zamanını kesin olarak ölçme iddiası yoktur.

| Grup | Aday alanlar | Zaman ve kullanım sınırı |
|---|---|---|
| Meteoroloji | `temperature_mean_c`, `temperature_min_c`, `temperature_max_c`, `dewpoint_mean_c`, `wind_speed_mean_ms`, `wind_speed_max_ms`, `soil_water_layer_1_mean`; dört `rain_*h_nonnegative_mm` toplamı | Kesim anından önceki kayıtlar; ERA5-Land geriye dönük yeniden analizdir. Gelecekte gerçekleşmiş hava özelliği kullanılmaz |
| Arazi | `elevation_mean_m`, `elevation_std_m`, `slope_mean_deg`, `northness_mean`, `eastness_mean` | Statik coğrafi adaylar; destek alanları ve kaynak sürümü ayrı korunur |
| Örtü | `forest_fraction`, `shrub_fraction`, `herbaceous_fraction`, `agriculture_fraction`, `urban_fraction`, `water_fraction` | 2017 referans haritası; geçmiş yayımlanma zamanı doğrulanmadı. Nihai habitat filtresi değildir |
| Bitki örtüsü | Her 30/60 günlük pencere için ayrı `ndvi_median_mean`, `ndmi_median_mean` | Geçmiş geçerli piksellerin medyanlarının alan ağırlıklı özetleri; günlük yeni ölçüm değildir |
| Denetim | Alan desteği, kaynak çekim zamanı, görüntü yaşı, `available_at`, kalite bayrakları ve sürümler | Kaynak ve eksiklik takibi; model girdisine ekleme ayrı deney kararıdır |
| Hedef/etiket denetimi | Olay kimliği, ilk tespit, hedef penceresi ve gözlem belirsizliği | Hedef penceresindeki gözlem tanıları tahmin girdisine sızdırılmaz; unknown otomatik sıfır olmaz |

NDVI bitki örtüsünün spektral yeşillik göstergesi, NDMI ise NIR/SWIR tabanlı
nemle ilişkili bir spektral göstergedir. NDMI doğrudan yakıt nemi ölçümü olarak
sunulmaz. Ölçek ve kalite bantları [Landsat kaynak tanımına](https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C02_T1_L2)
dayanır; değişkenlerin tahmin katkısı eğitim deneyiyle ölçülecektir.

## Bitki örtüsünde ölçekleme sırası

1. 1 Ağustos 2018 00:00 UTC için iki pencere, bütün 2.899 hücre ve 64 hücrelik
   gruplarla sınırlı hazırlık. İki eşzamanlı istek; ham integral ve sahne kimlikleri
   kalıcı kayıtlı. Kesim tarihi ve grup sözleşmesi değişirse checkpoint yeniden kullanımı reddedilir.
2. Ham integrallerin bağımsız yerel geri okuması ve eski 32 hücrelik örnekle eşleştirme.
3. İlk adım geçerse aynı eğitim ayının haftalık kesimlerinde günlük geçmişe göre
   eşleştirme denemesi. Yedi günlük aralık/sekiz günlük saklama deneysel adaydır;
   henüz model kalitesine göre doğrulanmış değildir.
4. Ölçülen kapsam/süre/çıktı boyutundan sonra eğitim yıllarına yayma. Daha geniş
   pencereyle kısa pencerenin eksikleri sessizce doldurulmaz.

Kaynak `available_at` bilinmediğinden özellikler geriye dönük aday olarak
tutulur. Üretimde tahmin anında gerçekten bulunabilen kaynakların sözleşmesi
ayrıca kurulacaktır. 2025 kapalı final testine bu çalışmada erişilmez.

## Etiket ve son birleştirme

Uydu kuyruğu biterken olay gruplaması ve gözlem politikası tasarlanabilir;
nihai hedeflerin kabulü ilgili gözlem kanıtını bekler. `negative_label_permitted=false`
korunur. Gerçekleşmiş yangın tespiti veya hedef pencere gözlem kapsamı, aynı
pencereyi tahmin eden modelin girdisi değildir.

Birleştirmede tam anahtar bütünlüğü, tekil satırlar, geçmişe göre özellik
seçimi, eksik değerlerin korunması ve sütun kaynağı kontrol edilir. İmputasyon
ve öğrenilen dönüşümler yalnız eğitim verisine/folduna fit edilir. Eğitim
2018–2023, doğrulama 2024 ve final test 2025 ayrımı korunur; yıl sınırını
aşan olaylar ayrıca denetlenir. Bu şartlar sağlanmadan model başarısı veya
veri setinin tamamlandığı ilan edilmez.

Güncel uygulama sonucu, tarihli bitki örtüsü raporuna ve [STATUS](STATUS.md)
dosyasına eklenecektir. VM'ye ek yük veya yeni kaynak oluşturma gerekmez.
