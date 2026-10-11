# Kesinti sonrası yerel bitki örtüsü devamı — 11 Ekim 2026

Kullanıcı elektrik/internet kesintisi sonrası eve geldiğini ve yerel kuyruğun
kontrollerle devam etmesini istedi; VPN'nin kapalı olduğunu teyit etti.
Önceki yetkilendirilmiş süre bugün 14:45 Türkiye'de dolmuştu. Kullanıcının
yenilenmiş, kalan dönem tamamlanana kadar devam isteğiyle yeni çağrı açıldı.

## Başlangıç kontrolleri

- Gerçek Windows süreç sorgusunda eski bitki örtüsü süreçleri yok.
- İki yazıcı kilidi yok; eski progress/manifest/raporlar değiştirilmedi.
- VPN molasında kayıt altına alınan 121 veri/rapor/runtime dosyası aynı hash'te.
- Dondurulmuş V2 ISO proof kontrolü geçti; 94 eski proof girdisi korundu.
- Ocak 2021'in 368 ham grubu özgün `validate_raw` sözleşmeleriyle kontrol edildi:
  23.192 hücre/pencere/kesim satırı geçerli. Bu tam ay kabulü değildir.
- Diskte 115,93 GiB boş alan, 10 GiB sınırının üzerinde.
- Mevcut kimlikle küçük Earth Engine scalar isteği geçti; kısıtlı kota uyarısı
  gelmedi. Bu deneme kalan EECU miktarını veya tüm kuyruğun kotaya sığmasını ölçmez.

Preflight:
`outputs/reports/landscape/power_resume_v1/20261011_2bf2c06e/checkpoint_preflight.json`;
SHA-256 `6bf5218ca3adeb90c34d1da649189ebd6ff125d3837079fb8f5f8347903baaf9`.
Bağlantı kaydı:
`outputs/reports/landscape/power_resume_v1/network_probe_f3d93033.json`;
SHA-256 `900f3d74c2f0946c945c4a95989d8920b14e92fd81526e31ba13514be9e92ead`.

## Yeni çağrı ve gözlenen durum

İş kimliği `training_iso_v2_power_resume_20261011_bb85a275`; başlangıç
14:53:22 UTC / **17:53 Türkiye**. Hidden Start-Process, launcher PID 6424;
üst Python PID 33832 ve çocukları gerçek Windows sorgusunda canlı görüldü.
İlk `running` kaydı Ocak 2018'i yeniden doğrulamış, Şubat'a geçmişti.
14:58:08 UTC snapshot'ında 16 eski ay doğrulanmış ve Mayıs 2019 geri okumasında
`running` görünür; launcher hata dosyası boş. Bu 16 ay eski 36 aya eklenmez.

Aynı V2/2018–2023 kapsamı, iki EE isteği, tek eşzamanlı ay, 4 saatlik bounded
alt çağrılar ve 10 GiB disk rezervi kullanılır. Eski kaynak/paket dosyaları
değişmedi; yalnız yeni job ve rapor alanı açıldı. Kabul edilmiş 36 ay, Ocak
2018–Aralık 2020, yeniden doğrulanarak kullanılır; sonra Ocak 2021 kısmi
kayıtlarından ve kalan aylardan devam edilir. Başlangıç geri okuması yeni
ham indirmeye veya tam veri seti kabulüne eşit değildir.

Kalan seçilmiş aylar tamamlanınca supervisor durur. Mevcut programın en yüksek
**48 saatlik** çağrı sınırı kullanıldı; yaklaşık **13 Ekim 17:53 Türkiye**.
Bu sınır bitiş garantisi veya otomatik yeniden silinen sayaç değildir.
Hata, disk rezervi veya kota kısıtı durumunda retained duruş kaydı tutulur;
sürekli hatalı yeniden deneme kurulmadı. Bu yeni kullanıcı isteği önceki
dolmuş süreye eklenen yetkilendirilmiş çağrıdır. Uyku/elektrik/internet kaybında
yerel süreç durabilir; bilgisayar açık ve uyku dışında tutulmalıdır.

Başlangıç kanıtı:
`outputs/reports/landscape/training_supervisor_v1/training_iso_v2_power_resume_20261011_bb85a275/startup_check.json`;
SHA-256 `add9376a683e6cb4d08b56f326bc6fea25252902615bdf3e8a8fb83d92272ebc`.
Launch kaydı SHA-256
`bde17f08122241ae609e24fb010532efa7771bcc58f7e16a0ff0722793bcd014`.

Kimlik bilgileri yazdırılmadı; Free Trial/billing/noncommercial tier değişmedi.
VM'deki uydu işi bu yerel başlatmada değiştirilmedi. Uzak VM'nin ayrıca
incelenmesi, ayrı görev ve kanıtla yürütülür. Kod değişmediğinden eski test
sayıları yeni test olarak sunulmadı; gerçek proof/hash/cache/bağlantı/süreç
kontrolleri ve başlangıç kaydı kullanıldı.

## Sonraki yerel geri okuma

15:09:55 UTC gözleminde 37 ay ve Şubat 2021'de running/hata yok görüldü.
15:23:41 UTC kaynak zamanlı sonraki snapshot 38 ay ve Mart 2021'i gösteriyor;
18:26 Türkiye gerçek Windows sorgusunda üst/çocuklar canlı, stderr sıfır.
Ocak 2021 `prepared_verified`/179.738, Şubat 2021 162.344 günlük aday
satırdır; iki ayın manifest, tablo ve aylık readback hash'leri karşılaştırıldı.
Readback tarihsel erişilebilirliği veya alan doğrulamasını kanıtlamaz; etiket
üretilmedi. Önceki 36 ay yeni ay olarak sayılmadı.
Snapshot `outputs/reports/landscape/training_supervisor_v1/training_iso_v2_power_resume_20261011_bb85a275/post_startup_20261011T152341Z.json`;
SHA-256 `907798e8789b89b855a76ef3e4326774859f6bed6cba428b6a5d4a1fc38ed2d0`.
