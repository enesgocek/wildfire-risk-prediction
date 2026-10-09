# Bütün hücrelerde bitki örtüsü ölçekleme denemesi

Deney ve kayıt tarihi: 10 Ekim 2026. Uydu gözlem VM oturumundan bağımsız,
mevcut Earth Engine bağlantısı ve yerel çalışma ortamıyla tamamlandı.
Amaç, 32 hücrelik geçmiş örneğin yöntemini 2.899 hücreye genişleterek kapsam,
gruplama, yeniden başlatma ve çıktı boyutunu sınamaktır. Günlük/aylık seri,
operasyonel erişim veya model performansı doğrulaması değildir.

## Kapsam ve yöntem

Kesim anı 1 Ağustos 2018 00:00 UTC, eğitim dönemindedir. Landsat 8 Collection 2
Level 2 için ayrı `[T−30 gün,T)` ve `[T−60 gün,T)` pencereleri kullanıldı.
Önceki kalite/ölçek/NDVI/NDMI ve görüntü yaşı yöntemi değiştirilmedi.
Kaynak sahne kimlikleri ve çekim zamanları her grupta kayıtlıdır; bütün zamanlar
kesim anından önce doğrulandı. `available_at` bilinmediği için boş kalır.
[Kaynak ve kalite bantları](https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C02_T1_L2).

Bütün grid kimlikleri sıralanıp 64 hücrelik 46 gruba ayrıldı; son grup 19
hücredir. Her pencere için aynı gruplar işlendi: toplam 92 kalıcı ham kayıt.
En fazla iki istek eşzamanlı yürütüldü. EPSG:6933/30 m hesap ızgarası,
AOI kesişim bölgeleri, alan ağırlıklı integraller ve `tileScale=4` kullanıldı.
[Earth Engine bölgesel azaltma API'si](https://developers.google.com/earth-engine/apidocs/ee-image-reduceregions).

Checkpoint sözleşmesi tarih, pencere, grup kimlikleri, geometri ve yöntem/kod
özetlerini içerir. Sözleşme veya değer kontrolü geçmezse eski grup sessizce
kullanılmaz. İlk sandbox isteği bağlantı/TransportError ile durdu; ağ erişimli
çağrı başarılı oldu. Yeni VM veya bulut kaynağı oluşturulmadı; çalışan
yangın üretim hattı ve dondurulmuş paketler değiştirilmedi.

## Ölçülen sonuçlar

| Kontrol | 30 gün | 60 gün |
|---|---:|---:|
| Coğrafi hücre | 2.899 | 2.899 |
| Geçerli piksel desteği bulunmayan hücre | 3 | 3 |
| AOI alanının en az %90'ında destek bulunan hücre | 2.676 | 2.800 |
| Hücre destek oranlarının medyanı | 0,999910 | 1,000000'a yakın |
| Destekli hücrelerin piksel medyan yaşı özetlerinin medyanı | 15,65 gün | 26,67 gün |

Her iki pencerede aynı 2.896 hücre desteklidir. Desteksiz üç hücrenin mevcut
2017 örtü tablosunda `water_fraction=1` olması, su piksellerinin dışlanmasıyla
uyumludur; ayrı kaynak veya saha doğrulamasıyla sebep kanıtı değildir.
Hücreler silinmedi; destek sıfır ve indeksler eksik kaldı. %90 eşiği tanısaldır,
model uygunluğu veya orman habitatı kararı değildir. Destek oranı yalnız
bulutu değil QA/su/yansıtım/kaynak kapsamı dışlamalarını birlikte yansıtır.

Toplam **5.798 özet** üretildi. Başarılı hazırlık çağrısında ölçülen süre
**316,75 saniye** (yaklaşık 5 dakika 17 saniye); grup başına katalog/integral
çağrısı 2,66–15,89 saniye. Ham JSON'lar 2.249.014 bayt; CSV 1.966.318 bayt.
Paylaşılan Earth Engine kapasitesi ve önbellek etkileri nedeniyle bu süre,
soğuk veri indirme hızı veya bütün yıllar için bitiş garantisi değildir.

## Yerel doğrulama

Bağımsız betik, ortak `summary_row` dönüşümünü çağırmadan ham integrallerden
bütün 5.798 satırı yeniden hesapladı. Dosya hash'leri, grid kapsamı, tekil
anahtarlar, zaman pencereleri, destek/indeks/görüntü yaşı sınırları ve NaN
koşulları denetlendi. Önceki kabul edilmiş 32 hücrelik örneğin aynı tarih ve
iki pencereye ait **64 satırı** ayrıca eşleştirildi. NDVI/NDMI için en büyük
mutlak fark sırasıyla yaklaşık 5,61×10⁻¹⁵ ve 1,61×10⁻¹⁵; alan integrali farkı
yaklaşık 1,97×10⁻⁷ m². Sayısal tolerans içinde uyuştu.

Ağ bağlantısı audit hook ile kapatılarak 92 gerçek checkpoint'in tekrar
kullanımı denetlendi. Yeniden kullanım geçti, ham dosya baytları değişmedi;
kontrol 0,313 saniye sürdü. Bu süre veri hazırlama hızı olarak sunulmaz.
Meteoroloji, statik tablo ve yeni bitki örtüsü tablosunun 2.899 grid kimliği
eşleşti; nihai hedef/özellik birleştirmesi yapılmadı.

Yeni gruplama/checkpoint kontrolleri ve mevcut bitki örtüsü zaman/özellik
kuralları için **34 test geçti**; yeni betik/test dosyalarında Ruff başarılı.
2025 final testine erişilmedi; yangın etiketi oluşturulmadı.

## Çıktılar ve sonraki adım

- Ham kaynak/integral kayıtları: `data/raw/vegetation/full_grid_v1/2018-08-01_b64/`.
- Tablo ve manifest: `data/interim/vegetation/full_grid_v1/2018-08-01_b64/`.
- Hazırlık ve geri okuma: `outputs/reports/landscape/full_grid_v1/2018-08-01_b64/preparation.json`, `local_readback.json`.
- Ağ kapalı yeniden kullanım ve grid eşleşmesi: aynı rapor dizininde `reuse_and_keys.json`.
- Manifest SHA-256: `b597caa129b1e028ceb38862797b2df334fe60ad0134f6c7f7404a59bb94c9db`.

İlk geniş kapsam denemesi geçti. Sırada aynı eğitim ayının haftalık kesim
özetleri ve günlük geçmişe göre eşleştirmesi var. Tarihsel yayımlanma zamanı,
habitat seçimi, sınır desteği ve nihai etiket politikası açık kalır. Bir aylık
deneme geçmeden bütün dönem günlük serisinin hazır olduğu söylenmez.
[Veri setine geçiş planı](DATASET_READINESS_2026-10-10.md).
