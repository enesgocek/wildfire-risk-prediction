# Mersin nokta piksel incelemesinin hazırlığı — 18 Kasım 2026

WF1487 arşiv kaydı için `N20:2021228.2312` çiftini inceleyen yerel
komut hazırlandı. Başlangıç kontrolünde bu plana bağlı tamamlanmış
Earthdata indirme makbuzu bulunmadı. Gerçek nokta sınıfları henüz
hesaplanmadı. Kullanıcının özel girişle indirmeyi tamamlaması bekleniyor.

Komut, mevcut tek çift aracının plan ve tamamlanma makbuzunu kontrol
eder. Dosyaların boyut, checksum ve header eşleşmeleri tekrar sınanır.
Kayıtlı nokta EPSG:6933'e dönüştürülür. Önceki yöntemin tarama içindeki
komşu merkezlerden kurduğu yaklaşık piksel geometrisi kullanılır.
Tarama sınırlarındaki dış satır/sütunlar bu yöntemle temsil edilmez.
Konumun gerçek tutuşma noktasını temsil etmesi ayrıca açık konudur.

Her taramada, noktanın kesiştiği bütün maske kodları korunur. Bir piksel
sınırındaki çoklu kodlar tek sınıfa zorlanmaz. Araştırmacıya sunulacak
sonuç için 250 m ve 1 km çevrelerindeki sınıf alanları hesaplanır.
Bu yarıçaplar önceki konum belirsizliği incelemesinden alınan tanısal
ölçeklerdir. Piksel alanları aynı sınıf içinde birleştirilerek sayılır.
Girdi QA'sı uygun kara alanı, ham kara sınıfından ayrı hesaplanır.
Geolocation scan quality ve sensor mode alanları da kaydedilir.

Yalnız bildirilmiş saatin Türkiye saati yorumu olan 16 Ağustos 2021
21.30 UTC'den sonraki ve aynı hedef penceresindeki taramalar kabul edilir.
Kaynak saat standardı açık kaldığından bu yorum araştırma varsayımıdır.
Sonuç, gün boyunca gözlem yeterliliği veya etiket kabulü sağlamaz.
Günlük gözlem durumu `unknown`, negatif etiket izni `false`.

```powershell
.\.venv\Scripts\python.exe scripts/quality/audit_mersin_point_pixels.py
```

Hazırlıkta 34 test geçti. Yeni üç test, aynı sınıftaki örtüşmelerin alanını,
sınıf sınırındaki çoklu kodları ve kalite koşulunu sağlamayan kara ile
boş kapsamın korunmasını sınadı. Kalan testler mevcut tarama/pencere
işlevlerini kontrol etti. Ruff geçti. Gerçek dosya çalışması indirmeden
sonra ayrıca kaydedilecek. Birinci aşama sürüyor.
