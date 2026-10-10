# Model veri setine geçiş planı

Kayıt tarihi: 10 Ekim 2026. Uydu gözlem kuyruğu çalışırken yerel özellik
hazırlığı ilerletilmektedir. Bu belge tamamlanmış model veri seti veya
operasyonel erişim onayı değildir.

## Hazır parçalar ve açık işler

Son güncelleme: [1 Ağustos 2018 birleştirme denemesi](FEATURE_JOIN_PILOT_2026-10-10.md)
2.899 hücrede 27 adayı ve ayrı kalite tablosunu geri okudu. Tam veri seti
ve etiket kabulü değildir. Yerel V2 progress kaydı 11:53:32 UTC'de
Ocak 2018–Mart 2019 **15 ayı** doğrulanmış gösteriyor; Nisan hazırlanıyor.
Aşağıdaki ilk hazırlık ölçümleri tarihli ön çalışmalardır; kalan ay sayısı
bu güncel kayıt üzerinden 57'dir ve aktif Nisan ayını içerir.

| Parça | Mevcut kanıt | Sıradaki iş |
|---|---|---|
| Coğrafi anahtar | Dört il, 2.899 hücre, AOI kesişimleri | Küçük sınır hücrelerinin destek alanını izlemek; bütün hücreleri otomatik orman saymamak |
| Meteoroloji | 2018–2024 için 7.412.743 hücre-gün yerel denetimden geçti | Mevcut 11 aday özellik ve uygunluk bayraklarını anahtar/zaman sözleşmesiyle birleştirmek |
| Arazi ve örtü | 2.899 hücrenin statik tablosu hazır | Kıyı/sınır desteği, tarihsel harita erişimi ve habitat tanımını gerekçelendirmek |
| Bitki örtüsü | Son yerel V2 progress kaydında Ocak 2018–Mart 2019 15 ay doğrulanmış | Kalan 57 eğitim ayına genişletme; aktif Nisan 2019 dahil; kesim/saklama kararının model katkısını değerlendirmek |
| Uydu gözlem tanıları | VM üzerinde kalan eğitim ayları işleniyor | Oturum raporlarını ve sonuç arşivlerini yerelde geri okumak; eksik kaynakları ayrı tutmak |
| Olay ve hedef | 24 saatlik hedef tanımı kayıtlı; 30.295 eğitim adayının dokuz gruplama grafiği ve ilk zaman/hücre/penceresi denetlendi | Zincirleme vaka incelemesi, nihai olay kimliği ve güvenilir negatif politikası oluşturmak |
| Nihai tablo | Henüz oluşturulmadı; tek eğitim günü için özellik/kalite birleştirmesi geri okundu | Etiket/gözlem kabulünden sonra özellik–hedef–split manifestleriyle tam dönem tablosunu kabul etmek |

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
3. Aynı eğitim ayının haftalık kesimlerinde günlük geçmişe göre eşleştirme
   denemesi tamamlandı: Ağustos 2018, beş kesim ve 179.738 satır; iki bağımsız
   yerel geri okuma geçti. Yedi günlük aralık/sekiz günlük saklama deneysel
   adaydır; henüz model kalitesine göre doğrulanmış değildir.
4. Şubat 2018 kış genişlemesi ve iki ayın destek/yaş incelemesi geçti. Eğitim
   yıllarına yayma için tek yazar, kaynak hash'i, disk ve süre bütçeli kuyruk
   hazır. Kış kısa penceresinde %13,845 eksik var; daha geniş pencereyle
   kısa pencerenin eksikleri sessizce doldurulmaz.

Kalan aylar için [otomatik toplu hazırlık](VEGETATION_TRAINING_AUTORUN_2026-10-10.md)
başladı. Aylar tek tek sohbet onayıyla açılmaz; ayrı bilimsel kayıt/denetim
birimi olarak otomatik ilerler. Tam dönem kabulü ve habitat/etiket işleri
henüz tamamlanmadı.

Kaynak `available_at` bilinmediğinden özellikler geriye dönük aday olarak
tutulur. Üretimde tahmin anında gerçekten bulunabilen kaynakların sözleşmesi
ayrıca kurulacaktır. 2025 kapalı final testine bu çalışmada erişilmez.

## Etiket ve son birleştirme

[Hedef kabul hazırlığı](TARGET_ADMISSION_REVIEW_2026-10-10.md), mevcut
bilimsel kararlar açıkken 0/1 atamasını reddeden kontrolü ve dokuz eğitim
keşif kataloğunun hedef penceresi geri okumasını tamamladı. Özellikler
kesim günü/ertesi gün/ay sonu dahil dört günde kontrol edildi. Bu, nihai
etiket politikasının veya bütün dönem birleştirmesinin kabulü değildir.

[Olay gruplaması geri okuması](EVENT_GROUPING_REVIEW_2026-10-10.md), dokuz
senaryonun matematiksel eşleşmesini ve inceleme kataloglarını tamamladı.
Uzun süre/geniş alan zincirleri ve ilk anda çok hücreli gruplar otomatik
olay veya pozitif etiket kabul edilmedi. Habitat ön incelemesi de bütün
hücreleri koruyor; nihai kapsam seçimi açık.

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

Güncel uygulama sonucu [kış–yaz bitki örtüsü raporunda](VEGETATION_TRAINING_SUPPORT_2026-10-10.md)
ve [STATUS](STATUS.md) dosyasında kayıtlıdır. VM'ye müdahale edilmedi.
