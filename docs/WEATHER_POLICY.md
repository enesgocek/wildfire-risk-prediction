# Meteoroloji kullanım kuralı — weather_model_v1

3 Ekim 2026. İlk geriye dönük model deneyi için muhafazakâr başlangıç kuralı.
Ham rasterlar ve günlük meteoroloji tabloları korunur. Yeni sütunlar ayrı
`data/interim/meteorology/model_v1/daily/` dizinine yazılır; bütün hücreler tutulur.
Bu işlem yangın etiketi veya nihai arazi uygunluğu üretmez.

## Alan kapsamı ve eksik veri

Her hücre için tüm hava özelliklerinin en küçük geçerli alan payı kullanılır.
Pay, hücrenin il sınırları içindeki bölümüne göredir. Sayısal tolerans 1e-9.

- Ana başlangıç deneyi: bütün özellikler dolu, alan payı tam ve büyük negatif
  yağış sorunu yoksa `weather_primary_eligible=True`.
- Ayrı duyarlılık deneyi: aynı koşullarla en az %90 pay için
  `weather_sensitivity90_eligible=True`. Bu eşik üstünlüğü kanıtlanmış bir standart değildir.
- Pozitif kapsamlı bütün dolu kayıtlar ayrıca `weather_observed_eligible` ile
  izlenir. Çok düşük kapsam, bütün hücreyi temsil ediyor kabul edilmez.
- Eksik değer NaN kalır. Komşudan veri taşıma, sıfırla doldurma veya imputasyon yok.
  Uygun olmayan kayıtlar daha sonra negatif yangın etiketi yapılmaz; kapsam dışı
  tahminler ve değerlendirme alanı ayrıca raporlanacak.

Kurallar model başarısına göre öğrenilmedi; etki incelemesi yalnızca 2018–2023
eğitim dönemini kullanır. 2024 için aynı kural değişmeden uygulanır. Önceki
bütünlük incelemesi 2024'ü de içeriyordu; bu işlem kör değerlendirme iddiası değildir.
2025 kapalıdır. Örtü uygunluğu ve nihai olay kuralları ayrı kararlardır.

## Küçük negatif yağış

ERA5-Land'in birikimlerden saatlik farklar üretilmesi kaynak belgede açıklanır.
Birikimli GRIB alanlarının sayısal kodlanması küçük yapay farklara neden olabilir.
Gözlediğimiz küçük negatif değerler bu açıklamayla uyumludur; tek tek kökenleri
kanıtlanmış değildir. [Saatlik kaynak](https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_HOURLY),
[ECMWF sayısal hassasiyet açıklaması](https://confluence.ecmwf.int/spaces/UDOC/pages/208501579/Why+are+there+sometimes+small+negative+precipitation+accumulations+-+ecCodes+GRIB+FAQ).

24/72/168/336 saatlik **alan ortalamalı ham toplam** için:

- `[-0,0001 mm, 0)` aralığı yeni `rain_*h_nonnegative_mm` sütununda sıfır olur;
  ham toplam ve `rain_*h_roundoff_clipped` bayrağı tutulur.
- Daha büyük negatif değer yeni sütunda NaN olur; kayıt
  `weather_large_negative_rain` ile işaretlenip üç deney profili dışında kalır.
- Gerçek sıfır, pozitif değer ve eksik değer korunur. Pozitif çisenti sıfırlanmaz.

0,0001 mm proje kalite sınırıdır; ECMWF'nin evrensel toleransı değildir.
Eğitimde en düşük ham toplam yaklaşık -0,0000484151 mm; sınırın altında kalan
büyük negatif kayıt bulunmadı. Bu dönüşüm saatlik negatifleri düzeltip yeniden
toplamakla eşdeğer değildir; pozitif toplamın içindeki olası iptalleri gidermez.
Yağışlı gün sıklığı veya FWI için daha ileri düzeltme ayrıca incelenecek.

Model girdi listesi yedi sıcaklık/çiy noktası/rüzgâr/toprak özelliği ve dört yeni
yağış toplamıdır: 11 özellik. Negatif saat sayıları, kapsam ve kalite bayrakları
varsayılan model girdisi değildir; denetim için korunur.

## Eğitimde ölçülen etki

2.191 gün, 6.351.709 hücre-gün. Bütün günlerde kaynak alan kapsamı aynı.

| Profil | Günlük hücre | Hücre-gün | Kapsamdaki aday tespit |
|---|---:|---:|---:|
| Tam alan: ana başlangıç | 2.400 | 5.258.400 | 25.004 / 30.295 |
| En az %90: duyarlılık | 2.466 | 5.403.006 | 26.106 / 30.295 |
| Pozitif alan: izleme | 2.710 | 5.937.610 | 28.891 / 30.295 |

Ana profil 5.291 aday tespitin bulunduğu kayıtları kapsamıyor. Bu sınırlama
başarı raporunda açıklanmalı; alternatif profiller aynı değerlendirme kapsamı
ve kapsam dışındaki kayıtlar ayrıca belirtilerek karşılaştırılmalı. Sayılar
geçici uydu tespitleridir; bağımsız yangın/pozitif etiket sayısı değildir.
Tanısal eşleştirme `(T,T+24h]` penceresine göredir; nihai olay etiketini oluşturmaz.

Eğitimde 414.099 eksik ve 679.210 kısmi kapsamlı kayıt var. 24/72 saat
toplamlarında 23.746/1.012 küçük negatif toplam işaretlendi; 168/336 saatte yok.
İnceleme raporu `outputs/reports/meteorology/weather_policy_training_review.json`;
kural, kod ve kaynak özetleri `data/interim/meteorology/model_v1/policy_manifest.json`.

## Uygulama ve sınırlar

61 test geçti. Üç gerçek örnek günün (2018-01-01, 2018-04-29, 2024-12-31)
dosya yazma/geri okuma kontrollerinden sonra tam dönem dönüşümü
manuel olarak tamamlandı. 2.557 gün ve 7.412.743 kaydın kaynak/çıktı dosyaları bağımsız
kapanış kontrolünden geçti. Komutlar
[betik rehberinde](../scripts/README.md#model-için-meteoroloji-kullanım-kuralı).

Hazırlama her girişin yıllık denetim özetini, anahtar/tarih/kaynak sözleşmesini
kontrol eder; çıktıyı geri okuyup özgün sütunların korunduğunu, uygun kayıtlarda
model özelliklerinin dolu ve yağışın negatif olmadığını doğrular. Kural modülü,
kaynak yöntemi veya eğitim incelemesi değişirse yeniden inceleme ister. Hazırlama
betiği özeti de dönem raporuna kaydedilir. Tam uygulamanın dönem raporu:
`outputs/reports/meteorology/model_weather_2018-01-01_2025-01-01.json`.

Kapanışta tüm dosya özetleri, eksiksiz tarih/grid/sürüm/şema sözleşmesi, özgün
sütunların korunması, NaN ve uygunluk bayrakları kontrol edildi. Yağış dönüşümü
ve kapsam kuralları hazırlama dönüşüm fonksiyonu çağrılmadan kaynak değerlerden
yeniden hesaplanıp kaydedilmiş sütunlarla karşılaştırıldı. Saatlik ERA5 kaynağı
tekrar hesaplanmadı; önceki yıllık kaynak denetimleri temel alındı.
Yerel rapor: `outputs/reports/quality/model_weather_2018_2024_audit.json`.

| Meteoroloji profili | Eğitim 2018–2023 | Doğrulama 2024 | Toplam |
|---|---:|---:|---:|
| Tam alan: ana başlangıç | 5.258.400 | 878.400 | 6.136.800 |
| En az %90: duyarlılık | 5.403.006 | 902.556 | 6.305.562 |
| Pozitif alan: izleme | 5.937.610 | 991.860 | 6.929.470 |

Bütün 7.412.743 kayıt tutuldu. 483.273 kayıtta eksik hava özelliği korunuyor;
792.670 kayıt dolu fakat kısmi kapsamlı. 24/72 saat toplamlarında 28.728/1.296
küçük negatif değer yeni sütunda sıfırlandı; 168/336 saatte yok. Büyük negatif
yağış bayrağı yok. Bu sayılar yangın etiketi veya nihai arazi uygunluğu değildir.

ERA5-Land yayımlanma zamanı bilinmiyor; kullanım hâlâ geriye dönük yeniden analiz.
Nihai olay kataloğu, etiketler ve eğitim tablosu ayrıca tamamlanacak.
