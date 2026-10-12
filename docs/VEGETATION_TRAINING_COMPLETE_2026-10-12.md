# Eğitim dönemi bitki örtüsü kuyruğu tamamlandı — 12 Ekim 2026

## Sonuç ve yöntem

Yerel `training_iso_v2_vpn_resume_20261012_6b68627a` işi
**06:49:26,372932 UTC / 09:49:26 Türkiye** tarihinde
`selected_training_range_verified` ile tamamlandı. Ocak 2018–Aralık 2023
arasındaki 72 eğitim ayı seçilmiş takvimle bire bir eşleşiyor. Hata alanı
yok, stderr sıfır bayt. 12 Ekim 11:24:55 Türkiye kontrolünde gerçek Windows
sorgusunda ilgili launcher/supervisor/çocuk süreç yok ve iki yazıcı kilidi yoktu.

Son çağrı 3 saat 46 dakika 17,921 saniye sürdü. 62 eski ay yeniden
doğrulandı; Mart–Aralık 2023'ün kalan 10 ayı hazırlandı ve kabul edildi.
Bu süre tüm altı yıllık ilk üretimin süresi veya karşılaştırmalı hız ölçümü değildir.

Tam takvim 2.191 gün ve 2.899 hücre içeriyor. Günlük tablolar 30/60 günlük
iki pencere için toplam **12.703.418 hücre-gün-pencere satırı** taşıyor;
6.351.709 takvim hücre-gününün iki pencereyle temsilidir. Bunlar yangın
olayı veya eğitim etiketi sayısı değildir. NDVI/NDMI değerleri ve kalite
destek bilgileri aday özellik olarak kalır; veri eksikleri bu sayımla kapanmaz.

## Son dosya bütünlüğü kontrolü

72 ayın 216 manifest/tablo/readback dosyası ve 13 runtime kaynağı,
toplam **229 dosya**, final kayıtlarındaki SHA-256 değerleriyle eşleşti.
Her aylık readback `monthly_daily_readback_passed`; ay/grid/takvim/pencere
satır sayıları manifestlerle eşleşiyor. Eski bilimsel kaynaklar değiştirilmedi.
Bu kontrolde CSV'ler hash ile geri okundu; tam bilimsel hesaplama yeniden
çalıştırılmadı. Üretimdeki aylık denetimler korunarak dosya bütünlüğü doğrulandı.

Özgün final progress ayrı kopyayla korundu. Yerel kanıt:
`outputs/reports/landscape/training_completion_v1/20261012T082646Z/completion_readback.json`;
SHA-256 `1d6352218200992dbc05323fcf29ae802da070af4e04fe1a0dda90d9ba9374c5`.

## Sınırlar ve sonraki adım

Bu sonuç bitki örtüsünün **2018–2023 yerel aday özellik kuyruğu** içindir.
Tüm veri seti, uydu VM kuyruğu veya model eğitimi tamamlanmış sayılmaz.
2024 bitki örtüsü hazırlığı ayrı aşamadır; 2025 final testine erişilmedi.
Geçmişte fiilî ürün erişilebilirliği ve bağımsız kaynak/saha doğrulaması
kanıtlanmış değildir. Yangın etiketi üretilmedi, model_ready false kalır.

Hazır toplu birleştirme planına yeni 72 aylık tamamlanma snapshot'ı
verilebilir; eski 61 aylık plan/denetim dosyaları değiştirilmez. Bilimsel
etiket, gözlem ve habitat kapıları ayrıca çözülmelidir. Bu kontrol yeni
birleştirme/üretim işi başlatmadı; VM, billing ve Earth Engine tier değişmedi.
