# Bitki örtüsünde kış ve yazın tam grid incelemesi

Deney ve kayıt tarihi: 10 Ekim 2026. Şubat ve Ağustos 2018 eğitim ayları,
2.899 hücrede ayrı 30/60 günlük pencerelerle hazırlanıp yerelde denetlendi.
Bu özellik hazırlığı VM'deki yangın gözlem tanılarından bağımsızdır.

## Kapsam ve ilerleme

| Ay | Gün | Haftalık kesim | Günlük aday satır | Ham grup dosyası |
|---|---:|---:|---:|---:|
| Şubat 2018 | 28 | 4 | 162.344 | 368 |
| Ağustos 2018 | 31 | 5 | 179.738 | 460 |
| Toplam | 59 | 9 | 342.082 | 828 |

Bir günlük aday anahtarı `(grid_id, prediction_timestamp_utc, window_days)`
biçimindedir. İki pencere aynı hücre/günü ayrı satırda tutar; toplam 171.041
benzersiz hücre-gün vardır. 72 eğitim ayının ikisi hazırlanmıştır; kalan 70
ay bu sonuçla tamamlanmış sayılmaz. Etiketli model tablosu henüz oluşturulmadı.

Şubat, önceki sabit mevsim denemesinin kış ayıdır; yangın sonuçlarına veya
model performansına göre seçilmedi. İki ay bütün mevsimler/yıllar için
temsili örneklem değildir. 2024 ve 2025 verileri bu çalışmada okunmadı.

## Destek ve görüntü yaşı

| Ay / pencere | Günlük satır | Destekli | Eksik | Eksik oranı | En az bir gün eksik hücre |
|---|---:|---:|---:|---:|---:|
| Şubat / 30 gün | 81.172 | 69.934 | 11.238 | %13,845 | 894 |
| Şubat / 60 gün | 81.172 | 79.491 | 1.681 | %2,071 | 154 |
| Ağustos / 30 gün | 89.869 | 89.764 | 105 | %0,117 | 7 |
| Ağustos / 60 gün | 89.869 | 89.776 | 93 | %0,103 | 3 |

Eksik oranının paydası ilgili ay/pencerenin bütün hücre-günleridir. Eksik,
geçmişte sekiz günlük saklama sınırında destekli özet bulunmamasıdır. Su,
kar, QA, yansıtım ve kaynak kapsamı dışlamaları birlikte etkilidir; bu tablo
yalnız bulut oranı veya yangın gözlem eksikliği değildir.

| Ay / pencere | En az %90 destekli günlük satır | Destekli satırlarda piksel medyan yaşı özetinin medyanı |
|---|---:|---:|
| Şubat / 30 gün | 39.838 | 16,65 gün |
| Şubat / 60 gün | 59.067 | 35,56 gün |
| Ağustos / 30 gün | 81.489 | 18,24 gün |
| Ağustos / 60 gün | 86.934 | 31,30 gün |

Yaş ölçüsü `median_pixel_age_mean_days` alanının destekli günlük satırlardaki
medyanıdır. Alan, hücre içindeki geçerli piksellerin medyan görüntü yaşlarının
alan ağırlıklı ortalamasıdır; günlük taşımada geçen süre eklenmiştir. Bu,
tekil kaynak görüntülerinin yaş dağılımı değildir. `%90` destek yalnız tanıdır,
model kabulü veya habitat filtresi değildir.

Şubat'ta geniş pencere daha çok satırda destek sağlıyor; görüntü yaşı da
daha yüksek. Bundan 60 günlük özelliğin daha iyi tahmin yaptığı sonucu
çıkarılamaz. İki pencere korunur; eksik kısa pencere geniş pencereyle doldurulmaz.

## Yöntem ve doğrulama

Kabul edilmiş aylık yöntem değişmedi: ayın ilk gününden yedi günlük kesimler,
ay içinde en yakın destekli geçmiş özeti en fazla sekiz gün taşıma, kaynak
ve yaş bilgisi kaydı. Gelecekten geri doldurma veya önceki ayla eksik doldurma yok.

Şubat'ın dört kesimi ve 23.192 özeti ham integrallerden geri okundu. Kuyruk
162.344 günlük satırı bağımsız kontrol sonrası kabul etti. Kış–yaz incelemesi
iki ayın bütün kaynak/manifest/günlük kayıtlarını tekrar bağımsız denetimden
geçirdi; uyarılar hata sayıldığında da geçti. Ağustos'un önceki kabul dosyaları
korundu. Bu denetim saha/uzman doğrulaması değildir.

Şubat aylık hazırlama çağrısı 1.046,375 saniye; kuyruk ve son kabul dahil
1.059,188 saniye (yaklaşık 17 dakika 39 saniye) sürdü. Dört kesimin tamamı
yeni hazırlandı. Ağustos'un 1.014,203 saniyelik önceki çağrısı ilk kesimin
yeniden kullanımını içeriyordu; iki süre eşit koşullu hız karşılaştırması veya
bütün dönem bitiş garantisi olarak yorumlanmadı.

Şubat'ın günlük CSV'si 65.546.911 bayt; 368 ham grup toplam 8.727.871 bayt.
Kuyruk, inceleme ve ilgili seri/aylık/gizlilik testlerinde 55 kontrol geçti;
Ruff geçti. Üretim sırasında yedi bağımlı kod/grid dosyasının hash'leri değişmedi.

## Kanıt dosyaları ve sürüm

- `data/interim/vegetation/month_v1/2018-02/manifest.json`
- `outputs/reports/landscape/month_v1/2018-02/preparation.json`
- `outputs/reports/landscape/month_v1/2018-02/queue_20261009t215929z_c90ba965.json`
- `outputs/reports/landscape/period_v1/20261009T215929Z_c90ba965/progress.json`
- Aynı çağrı dizininde `runtime_observation.json`.
- `outputs/reports/landscape/month_comparison_v1/winter_summer_training_2018_v1.json`

Şubat manifest SHA-256:
`bd2479e7e178bc01f37b7979bd5991f6bf46d3cac5447c9cc74e2e40741d6684`.
Ağustos kabulü [önceki aylık raporda](VEGETATION_MONTH_2018_08_2026-10-10.md).

Yerel çalışma sırasında gözlenen ortam: Python 3.12.14, Earth Engine API
1.7.46, pandas 2.3.3, NumPy 2.5.3, python-dotenv 1.2.3, pyproj 3.8.0.
Ortam kilidi ve proje ayar dosyası hash'leri yerel kayıttadır; ortam değişkenleri
kaydedilmedi. Kuyruk kodu gözlem anında `612200c` commit'indeydi. Çağrı dizini
adları UTC'dir; rapor tarihi Türkiye yerel takvimine göre 10 Ekim'dir.

## Açık konular

Tarihsel erişim zamanı bilinmediğinden veriler geriye dönük adaydır; mevcut
erişim koşuluyla operasyonel uygun satır sayısı sıfır. Habitat seçimi, etiket
politikası, imputasyon ve özellik katkısı ayrı gerekçe/deney gerektirir.
`negative_label_permitted=false` korunur; model eğitimi ve final test başlamadı.

Sıradaki iş, kalan eğitim aylarını [sınırlı kuyrukla](VEGETATION_PERIOD_QUEUE_2026-10-10.md)
genişletmek ve aynı eksiklik/yaş ölçülerini izlemektir. Bu çağrı tamamlandı;
arkada bırakılmış yerel hazırlık süreci veya yeni zamanlanmış görev yoktur.
