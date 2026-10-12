# VPN molası sonrası bitki örtüsü devamı — 12 Ekim 2026

Kullanıcının açık başlatma isteği üzerine yerel kuyruk yeni iş kimliğiyle
devam ettirildi. [Önceki duruş](VEGETATION_VPN_PAUSE_2026-10-12.md) kaydı ve
eski job/progress korunur. VM, billing, tier ve bilimsel üretim kodu değiştirilmedi.

## Başlangıç kontrolü

Gerçek Windows sorgusunda eski bitki örtüsü süreçleri ve iki yazıcı kilidi
yoktu. Ocak 2018–Şubat 2023 arasındaki 62 ayın manifest/tablo/readback ve
runtime kaynakları, toplam 199 dosya, önceki duruşla aynı hash'lerdeydi.
Mart 2023'ün 169 kısmi ham JSON'u da aynı kimliklerde korundu; bu tam Mart
kabulü değildir. ISO proof/94 proof girdisi, kaynak hash'leri ve Python
paket sürümleri geçti. Diskte 111,78 GiB boş alan, 10 GiB rezervin üzerindeydi.

Mevcut kimlikle tek küçük Earth Engine scalar isteği başarılı ve kısıtlı
kota uyarısı yok. Bu kontrol tüm kuyruğun kotaya sığacağını veya VPN
durumunu kanıtlamaz; kimlik bilgileri ve servis hata metinleri yazdırılmadı.

Kanıt dizini: `outputs/reports/landscape/vpn_resume_v1/20261012_6b68627a/`.
`preflight.json` SHA-256:
`34c3dff82b9fc10d9651f3907a9e423d5f57b1c451a800d881ddfc03c64843e3`.
`network_probe.json` SHA-256:
`c25357377a5ff6745e66f272be605feddb0f8baf48d5a3d5b83d6ea7f2085df1`.

## Yeni çağrı ve süre

İş `training_iso_v2_vpn_resume_20261012_6b68627a`, başlangıç
**03:03:08 UTC / 06:03:08 Türkiye**. Launcher 17332, supervisor 30196 ve
hazırlık alt süreçleri gerçek Windows sorgusunda canlıydı. İlk progress
`running`, hata alanı yok; stderr sıfır bayt. Kuyruk eski ayların geri
okumasıyla başladı. İlk çağrıda düşük ay sayısı önceki 62 ayın silindiği
anlamına gelmez; yeni çağrının yeniden doğruladığı ayları gösterir.

Başlatma bütçesi 35,754188180 saat; önceki **13 Ekim 17:53:22 Türkiye**
son sınırı ve beş dakika rezerv korunur. Üst duruş yaklaşık 17:48'dir;
seçilen aylar tamamlanırsa erken durur. Aynı V2, 2018–2023 kapsamı, tek
eşzamanlı ay, iki EE isteği, dört saatlik batch ve 10 GiB rezerv kullanılır.
Eski aylar tekrar indirilmez; yeniden denetimden sonra Mart kısmi kayıtları
ve kalan eğitim aylarından devam edilir. Kesin bitiş veya model kabulü yoktur.

Başlangıç kanıtı yeni job dizinindeki `startup_check.json` dosyasıdır.
SHA-256: `b76b4102f786c7e1596e23afad3ac4938cb96cd1365ad16e2577a7aeccb7ede3`.
Bu snapshot'ta üç eski ay yeniden doğrulanmış ve Nisan 2018 geri okuması sürüyordu.
Bu devam için yeni test veya bilimsel üretim yöntemi değişikliği yapılmadı;
gerçek proof/hash/paket/bağlantı/süreç kontrolleri uygulandı. Bilgisayar
açık ve uyku dışında tutulmalı; VPN için yeniden kontrollü duruş istenmelidir.
