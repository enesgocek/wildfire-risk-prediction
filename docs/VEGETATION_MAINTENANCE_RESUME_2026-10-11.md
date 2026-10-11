# Bilgisayar bakımı sonrası bitki örtüsü devamı — 11 Ekim 2026

Kullanıcı kontrollü bakım duruşundan sonra açıkça yeniden başlatmayı istedi.
Yeni yerel çağrı başladı; VM, billing, tier veya bilimsel kod değiştirilmedi.
Bu kayıt [bakım duruşundan](VEGETATION_MAINTENANCE_PAUSE_2026-10-11.md) sonradır.

## Başlangıç kontrolleri

- Gerçek Windows sorgusunda eski bitki örtüsü süreçleri yok; iki yazıcı
  kilidi yok. Eski progress/final üzerine yazılmadı.
- Ocak 2018–Eylül 2021 arasındaki 45 ayın manifest/tablo/readback ve runtime
  pinleri, toplam 148 dosya, bakım duruşuyla aynı hash'lerle geri okundu.
- Ekim 2021'in 276 kısmi ham JSON'u duruş envanteriyle aynı hash'lerde.
  Bu koruma kontrolü tek başına tam Ekim kabulü değildir.
- Mevcut ISO proof/94 proof girdisi kontrolü ve Python paket sürümleri geçti.
  Diskte 115,45 GiB boş alan, 10 GiB rezervin üzerindedir.
- Mevcut kimlikle tek küçük Earth Engine scalar isteği geçti; kısıtlı kota
  uyarısı yok. Bu kontrol kalan EECU miktarını veya tüm kuyruğun kotaya
  sığmasını kanıtlamaz. Kimlik bilgileri yazdırılmadı.

Preflight: `outputs/reports/landscape/maintenance_resume_v1/20261011_bd22517d/preflight.json`;
SHA-256 `7736398b27304638b7ffa1f854966a96ff7a41b11deeb70d0d21689d41479c9a`.
Scalar bağlantı kaydı aynı dizinde `network_probe.json`;
SHA-256 `9ac774b6e6448c2f0447fb5b2bb0861743b66657380b7ba515a33858bf4934b5`.

## Çalışan çağrı ve süre

İş kimliği `training_iso_v2_maintenance_resume_20261011_bd22517d`;
başlangıç **19:56:57 UTC / 22:56:57 Türkiye**. Launcher 34268,
supervisor 7036; gerçek Windows sorgusunda iki hazırlık çocuğu da canlı.
İlk snapshot `running`, hata alanı yok, stderr sıfır; iki eski ay yeniden
doğrulanmış ve Mart 2018 geri okumasında. Bu aylar eski 45 aya eklenmez.
Mevcut kabul edilmiş aylar geri okunur, sonra Ekim 2021 kısmi kayıtları ve
kalan seçilmiş eğitim aylarından devam edilir.

Önceki **13 Ekim 17:53:22 Türkiye** son sınırı korunur; bakım molası süreyi
sıfırlamaz. Beş dakika rezerv düşülerek 42,857125783 saatlik çağrı açıldı;
üst duruş yaklaşık **13 Ekim 17:48 Türkiye**. Aynı V2/2018–2023 kapsamı,
tek eşzamanlı ay, iki EE isteği, dört saatlik alt çağrı ve 10 GiB rezerv
uygulanır. Seçilmiş aylar tamamlanırsa erken durur; hata/kota/disk durumunda
kayıt koruyan duruş vardır. Otomatik sınırsız hata denemesi kurulmadı.

İlk başlatma komutu PowerShell'in otomatik tarih dönüşümü nedeniyle süre
kapısında durdu; süreç veya job dizini açılmadı. Tarih nesnesi timezone'u
koruyarak DateTimeOffset'e dönüştürüldü; düzeltme sonrası tek çağrı açıldı.
Bilimsel runtime dosyalarında değişiklik yapılmadı.

Başlangıç kanıtı:
`outputs/reports/landscape/training_supervisor_v1/training_iso_v2_maintenance_resume_20261011_bd22517d/startup_check.json`;
SHA-256 `5ad90201c16a8cdb45b4410e319488f5db5870cad894eada445f376197374594`.
Yeni bilimsel dönem/etiket kabulü veya kesin bitiş garantisi değildir.
Bilgisayar açık ve uyku dışında tutulmalıdır; yerel elektrik/internet
kesintisi işi etkileyebilir. Bu başlangıçta yeni test yazılmadı; değişmeyen
kod için gerçek proof/hash/paket/bağlantı/süreç geri okumaları kullanıldı.
