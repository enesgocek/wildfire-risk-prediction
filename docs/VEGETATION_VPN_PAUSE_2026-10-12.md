# VPN için bitki örtüsü duruşu — 12 Ekim 2026

Kullanıcının açık durdurma isteği üzerine yalnız yerel bitki örtüsü kuyruğu
duraklatıldı. Otomatik yeniden başlatma kurulmadı; VM işi değiştirilmedi.

## İşlem ve sonuç

`training_iso_v2_maintenance_resume_20261011_bd22517d` işinin gerçek Windows
süreç ağacı launcher 34268, supervisor 7036 ve alt süreçler 32704/34984
olarak doğrulandı. İzole konsolda yalnız bu iş ve sinyal yardımcısı bulundu;
CTRL_C_EVENT gönderildi. Açık ağ isteği bu sinyalden sonra kapanmadığı için
yalnız alt süreç 34984, üst süreç/görev/başlama zamanı doğrulanarak sonlandırıldı.
Bu adım sıradan Ctrl+C temizliğinden ayrı kaydedildi; tamamlanmamış istek
yeniden başlatmada tekrar alınabilir.

Ana kuyruk mevcut kesinti ve temizleme yollarını tamamladı. Final kayıt
**02:30:39,247967 UTC / 05:30:39 Türkiye**:
`interrupted_checkpoints_retained`; aktif batch aynı durumda ve hata alanı yok.
Son gerçek Windows sorgusunda ilgili launcher/supervisor/alt süreç kalmadı.
İki bitki örtüsü yazıcı kilidi normal temizleme ile kalktı; elle silinmedi.

## Veri koruması ve sınırlama

Doğrulanmış listede **62 ay, Ocak 2018–Şubat 2023** kaldı. Bu ayların
186 manifest/günlük tablo/readback dosyası ve 13 runtime kaynağı, toplam
**199 dosya**, duruş öncesi ve sonrası aynı SHA-256 değerleriyle geri okundu.
Mart 2023'ün 169 ham JSON dosyası ayrıca hash envanterine alındı. Bu kısmi
envanter tamamlanmış ay veya yeni bilimsel kabul sayılmaz.

Kanıt dizini: `outputs/reports/landscape/vpn_pause_v1/20261012T022851Z/`.
Özgün ön/final progress ve aktif batch baytları ayrı kopyalarla saklandı.
`pause_readback.json` SHA-256:
`7e141075c2f619455ab64f3605926b5ba0478e67394142b2b5f017dab7c0c304`.
Kimlik bilgileri okunmadı veya raporlanmadı; bilimsel üretim kodu değişmedi.

## Devam koşulu

Kullanıcı VPN'yi kapatıp yeniden başlatmayı istediğinde süreç/kilit yokluğu,
korunan hash'ler, disk ve bağlantı kontrol edilecek. Yeni job ile geçerli
checkpoint'lerden devam edilecek; eski progress üzerine yazılmayacak.
Önceki son sınır **13 Ekim 14:53:22 UTC / 17:53:22 Türkiye** ve beş dakika
rezerv korunur; mola yeni süre bütçesi oluşturmaz. Sınır dolarsa sessizce
uzatılmaz. Bu duruş bulut üretimi veya otomatik devam yetkisi değildir.
