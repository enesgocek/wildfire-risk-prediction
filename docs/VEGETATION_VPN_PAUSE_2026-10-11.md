# VPN molası için yerel bitki örtüsü duruşu — 11 Ekim 2026

Kullanıcı yaklaşık 30 dakikalık VPN kullanımı için yerel kuyruğun duraklatılmasını
istedi. Yeniden başlatma tercihi, VPN kapandıktan sonra kullanıcı bildirimi ve
bağlantı kontrolüdür. Otomatik zamanlayıcı veya otomatik yeniden başlatma kurulmadı.

## Süreç ve duruş

Canlı Windows süreç ağacı, supervisor PID 22500, launcher 32604 ve iki
ay hazırlık çocuğu 32388/28960 olarak doğrulandı. İzole gizli konsolun süreç
listesi ayrıca kontrol edildi; yalnız bu iş ve sinyal yardımcısı vardı.
Konsola CTRL_C_EVENT gönderildi. Dondurulmuş Python kodu değiştirilmedi;
mevcut KeyboardInterrupt/child cleanup/final progress yolları kullanıldı.
VM üzerindeki V4 uydu işi bu yerel duruştan etkilenmedi.

Final kayıt 11 Ekim **00:22:25,930884 UTC / 03:22:25 Türkiye**:
`interrupted_checkpoints_retained`; aktif batch de aynı durumda, hata alanı
yok. Supervisor/launcher/çocukları gerçek Windows sorgusunda kalmadı.
İki yazıcı kilidi normal cleanup ile kalkmış; elle silinmedi.

## Korunan kayıtlar

36 ay, Ocak 2018–Aralık 2020, supervisor'ın doğrulanmış listesinde bulunuyor.
Bu 36 ayın manifest, günlük tablo ve readback hash'leri ayrı ayrı kayıtla
eşleştirildi: 108 veri/rapor dosyası ve 13 runtime kaynak/pin dosyası,
toplam **121 dosya aynı**. Hash eşleştirmesi kabul edilmiş dosyaların
değişmediğini denetler; bu duruş için bilimsel üretim yeniden çalıştırılmadı.

Ocak 2021 henüz tamamlanmamış. Ayın ham kesim klasörlerinde 368 JSON grup
dosyası bulundu; bu sayım tek başına grup bilimsel kabulü veya tam ay kabulü
değildir. Tamamlanmamış isteğin yeniden yapılması gerekebilir; tamamlanmış
aylar ve geçerli checkpoint'ler yeniden kullanılacaktır.

İlk ön-duruş envanter denemesinde runtime sözlüğündeki `supervisor` rolü
dosya yolu sanıldığından envanter dosyası yazılmadı. Final geri okuma bu rolü
doğru dondurulmuş supervisor yoluna eşleştirdi; 121 kimlik denetimi geçti.
Bu envanter hatası üretim dosyası değişikliği veya kayıp anlamına gelmez.

Kanıt:
`outputs/reports/landscape/vpn_pause_v1/20261011_ac047933/pause_readback.json`;
SHA-256 `0f8e8826af580687cdd940d9053d164d3dede853684e3eff0a832291593ea864`.
Orijinal final progress aynı klasörde `stopped_progress.json` olarak korunur.

## Yeniden başlatma koşulları

Kullanıcı VPN'yi kapattığını bildirdikten sonra gerçek eski süreç/kilit yokluğu,
korunan dosyalar/proof/runtime kimlikleri, disk rezervi ve küçük kimlikli
Earth Engine bağlantısı kontrol edilecek. Yeni job kimliğiyle aynı V2,
2018–2023 kapsamı, iki EE isteği ve 10 GiB rezerv kullanılacak.
Eski job/progress üzerine yazılmayacak. İlk başta mevcut ayların yeniden
doğrulanması normaldir; sıfırdan ham veri indirme değildir.

Önceki yetkilendirilmiş son zaman **11 Ekim 11:45:01 UTC / 14:45:01 Türkiye**
korunur; moladan sonra yeni bir 24 saat sayacı açılmaz. Beş dakika rezervle
yaklaşık 14:40 Türkiye'ye kalan bütçe hesaplanacak. Mevcut minimum bir saat
başlatma bütçesi kalmamışsa süreyi sessizce uzatmadan durum bildirilecek.
Bu duruşta kimlik bilgileri okunmadı/paylaşılmadı; billing/tier/VM değiştirilmedi.
