# Ağustos 2018 günlük bitki örtüsü adayları

Deney ve kayıt tarihi: 10 Ekim 2026. Eğitim dönemindeki tek ay için yerel
özellik hazırlığıdır; VM'deki uydu gözlem kuyruğuna müdahale edilmedi.

## Amaç ve yöntem

Antalya, Muğla, İzmir ve Mersin'deki 2.899 hücrenin NDVI/NDMI adaylarını
günlük tahmin anahtarlarına geçmişe göre eşleştirmek. 1/8/15/22/29 Ağustos
00:00 UTC kesimlerinde ayrı 30 ve 60 günlük geçmiş görüntü pencereleri kullanıldı.
1 Ağustos'un kabul edilmiş özeti doğrulanarak yeniden kullanıldı; dört yeni
kesim, 64 hücrelik gruplar ve en fazla iki Earth Engine isteğiyle hazırlandı.

Her hücre/gün/pencere için en yakın destekli geçmiş özet, en fazla sekiz günlük
yaş sınırıyla seçildi. Gelecekten geri doldurma, interpolasyon veya 30 günlük
eksik değeri 60 günlük değerle değiştirme uygulanmadı. Kaynak, pencere,
manifest ve görüntü yaşı günlük satırda korundu; görüntü yaşına geçen süre eklendi.
Bu satırlar her gün yeni bir uydu görüntüsü alındığı anlamına gelmez.

## Sonuçlar

| Ölçüm | Sonuç |
|---|---|
| Kapsam | 31 gün × 2.899 hücre × 2 pencere = 179.738 satır |
| Beş kesimdeki özetler | 28.990 satır |
| Ham grup dosyaları | 460 JSON; toplam 11.242.113 bayt |
| Günlük aday CSV | 76.620.808 bayt |
| Hazırlama çağrısının süresi | 1.014,203 saniye; yaklaşık 16 dakika 54 saniye |
| En büyük seçilen özet yaşı | 8 gün |

Süre ilk kesimin yeniden kullanımını, dört yeni kesimi ve günlük tablo hazırlığını
içerir. Bağımsız son denetim süresi bu ölçüme dahil değildir. Soğuk başlangıçla
bütün dönem için hız veya bitiş garantisi olarak kullanılamaz.

| Pencere | Günlük satır | Destekli satır | Eksik satır | En az bir gün eksik hücre |
|---|---:|---:|---:|---:|
| 30 gün | 89.869 | 89.764 | 105 | 7 |
| 60 gün | 89.869 | 89.776 | 93 | 3 |

Eksik satırlar korundu. Destek bulunması tek başına habitat uygunluğu veya
model için yeterli kalite anlamına gelmez; alan destek oranları ayrıca kayıtlıdır.

## Doğrulama ve kaynak bütünlüğü

Bağımsız yerel denetim, beş kesimin ham integrallerini ve 28.990 özetini
yeniden okudu; 179.738 günlük satırın anahtarlarını, geçmiş seçimini, eksik
değerlerini, taşınan değerlerini ve ilerleyen görüntü yaşlarını kontrol etti.
İki ayrı denetim geçti; sonuç raporlarının baytları eşleşti. İkinci denetimde
deprecation uyarıları hata sayıldı ve uyarı oluşmadı.

Denetleyici, eğitim dışı/bozuk ayları dosya erişiminden önce reddeder. Kabul
edilmiş rapor aynı sonuçta korunur; farklı sonuç için yeni rapor adı gerekir.
Bu davranışlar için altı yeni test ve bitki örtüsü/gizlilik testleri birlikte
29 kontrolü geçti. Önceki genel koşumda 734 test geçmiş, bir test atlanmıştı;
bu sayılar farklı kapsamlı koşumlardır. Ruff kontrolü geçti.

Birincil yerel dosyalar:

- `data/interim/vegetation/month_v1/2018-08/daily_candidates.csv`
- `data/interim/vegetation/month_v1/2018-08/manifest.json`
- `outputs/reports/landscape/month_v1/2018-08/preparation.json`
- `outputs/reports/landscape/month_v1/2018-08/local_readback.json`
- `outputs/reports/landscape/month_v1/2018-08/local_readback_v2.json`
- `outputs/reports/landscape/month_v1/2018-08/scope_summary.json`

Aylık manifest SHA-256:
`6428b03d04068c73449acb861085be71b01ed70fbc0bc8eaa50889bb56d73164`.
Manifest beş kaynak manifestinin hash'lerini ve üretim kodunun sürümünü bağlar.
Büyük veri ve makine çıktı dosyaları Git'e alınmaz; yöntem ve sonuç özeti izlenir.

## Sınırlar ve sonraki adım

Kaynakların tarihsel yayımlanma/erişim zamanı bilinmiyor. Mevcut erişim
koşulunda operasyonel kullanıma uygun satır sayısı sıfır; tablo yalnız geriye
dönük adaydır. Bu bir saha doğrulaması, tamamlanmış etiketli veri seti veya
tahmin başarısı değildir. Yangın etiketi üretilmedi, model eğitilmedi ve
2025 kapalı final testi okunmadı.

Haftalık kesim ve sekiz günlük saklama deneysel kararlardır. Sıradaki çalışma
eğitim dönemine kontrollü genişletme, habitat/gözlem politikası ve özellik/etiket
birleştirme denetimleridir. Mevcut negatif etiket yasağı korunur.
