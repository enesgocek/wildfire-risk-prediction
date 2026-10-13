# V7 başlangıcında Drive OAuth hatası ve bağlantı yenileme — 13 Ekim 2026

## Amaç, kaynak ve bulgu

Kullanıcı V7 launcher/progress/süreç çıktısını paylaştı ve kontrol sonrası
VM Stop teyidi verdi. Launcher, 18 çocuk kanıtı ve 22 hazır ZIP'in korunduğunu,
Aralık uygun günler aşamasında **OAUTH HTTP 400** ve
`PARENT_FAILURE GOOGLE_HTTP_400 CLASS_ONLY` oluştuğunu gösteriyor. Sonra
`Guest poweroff requested: True`; süreç listesinde Python satırı yok.
Bu kullanıcı uzak günlük bildirimidir; bağımsız canlı VM sorgusu yapılmadı.

Hata Google Drive access token yenileme isteğindedir; Earthdata giriş
sonucu olarak yorumlanmaz. Alt OAuth kodu `UNCLASSIFIED`: invalid_grant,
invalid_client veya kesin token süresi dolması bu günlükten ayrılmıyor.
OAuth consent uygulaması External/Testing ise bu kapsamda refresh token
ömrü 7 gündür; yalnız temel kimlik scope'ları istisnadır.
[Google token ömrü ve iptal nedenleri](https://developers.google.com/identity/protocols/oauth2#expiration).
7 gün koşulu olası açıklamadır; uygulamanın canlı consent durumu ve eski
token'ın issue zamanı bağımsız doğrulanmadı. Yerel özel dosyanın yalnız
mtime/uzunluğu okundu: 6 Ekim 11:37:31 UTC / 374 bayt. Bu OAuth issue
zamanı yerine geçmez; içerik veya credential değeri yazdırılmadı.

`progress.json` hâlâ V6 hash'i, Haziran/pair_publication ve eski failed
alanlarını gösteriyor. Donmuş `accelerated_production.run` sırasına göre
Drive backend/token doğrulaması yeni state/progress yazımından öncedir;
bu yüzden yeni OAuth başarısızlığı eski Haziran state'ini değiştirmemiş.
Arşiv receipt varlığı üretici geçiş mesajıyla tutarlı. 65 tam ayın önceki
günlük/katalog kabulü korunur; yeni bilimsel ürün veya ay kabulü yoktur.

Kanıt `outputs/gcp_acceleration/source_aware_v7_18h_2026-10-13/oauth_failure_user_readback_20261013.json`;
SHA-256 `d401eef335403715ec4c8a5067348c0bc42298e6d817a0f30abdd86466dec4ee`.

## Hazırlanan değişiklik ve kontroller

Yerel `scripts/cloud/connect_drive.py --renew`, aynı istemci/scope/folder
ile yeniden tarayıcı izni alır. Yeni `--connection` yalnız renewal için
izinlidir; mevcut mutlak özel dosya yolunu kullanır. İlk oluşturma/yeni
klasör akışı bu kurtarmada kullanılmaz. Yeni token ile mevcut folder'ın
id/mime/trashed/canAddChildren alanları salt okunur doğrulanmadan eski
bağlantı atomik değiştirilmez. Tarayıcı/yanıt hata çıktısı yalnız sabit
etikettir; code/token/response body veya bilinmeyen metin yazdırılmaz.

İlk yerel tarayıcı denemesi exit 1 ile başarısız sonuçlandı; genel eski
hata çıktısı alt nedeni ayırmıyor. Sonrasında özel dosya mtime'ı hâlâ
6 Ekim olarak görüldü. Başarılı yenileme veya VM aktarımı raporlanmadı;
yeni güvenli sınıflandırmalı deneme insanın Google izin adımını gerektirir.

Yeni `scripts/cloud/install_renewed_drive_connection.py`, Linux VM'de
mevcut job.lock'ı exclusive/nonblocking alır; pinned üretim manifesti ve
Drive kütüphanesini doğrular. Home'daki yeni özel JSON ile mevcut config
aynı client_id/client_secret/scope/folder_id olmalıdır. Yeni OAuth token
ve aynı folder erişimi doğrulanır; dosyalar kontrol sırasında değişmişse
durur. Ardından 0600 izinle yalnız özel config atomik değiştirilir. Bilimsel
paket/registry/manifest/checkpoint/sonuç yazmaz, yeni Drive nesnesi veya
bulut işi oluşturmaz. OAuth token POST ve mevcut folder metadata GET'i
kullanır; private içerikleri stdout'a veya Git'e koymaz.

Renewal/installer/Drive transport kontrolleri birlikte **61 passed**;
lint/format geçti. Yanlış istemci/scope/folder, silinmiş/yazılamayan folder,
OAuth reddi, pending çakışması ve kontrol sırasında dosya değişimi
reddedildi; eski bağlantı korunur. Sentetik testler gerçek VM kurulum
kabulü değildir. 22 donmuş dosya ve V7 source hash'i aynı kaldı; V7/V8
bilimsel paket değişikliği yapılmadı.

Hazırlık kaydı
`outputs/gcp_acceleration/source_aware_v7_18h_2026-10-13/connection_recovery_prepared_20261013.json`;
SHA-256 `b74c69193b2d28b0284436a456d3c6a5b18fc0b66203cce9099784c9d1d90d94`.

## Bilgisayarda izin yenileme — VM Stop

Bilgisayarın **PowerShell** terminalinde, SSH/Cloud Shell dışında:

```powershell
Set-Location 'C:\PROJELERIM\wildfire-risk-prediction'
.\.venv\Scripts\python.exe scripts/cloud/connect_drive.py --renew --connection 'C:\Users\enesn\AppData\Local\wildfire-cloud-auth\drive_connection.json'
```

Açılan yeni Google sayfasında önceki Drive hesabı seçilir; kullanılan
uygulama dosyaları kapsamına izin verilir. Eski/zaman aşımına uğramış
localhost callback sekmesi kullanılmaz. Başarı için terminalde
`Authorization renewed; the same Drive folder and saved jobs are preserved.`
beklenir. Dosya proje dışında aynı özel konumda kalır. JSON içeriği veya
callback URL'si sohbete/Git'e/Drive sonuç klasörüne gönderilmez. Başarılı
mesaj gelmeden VM'de üretime geçilmez.

## VM'ye kontrollü kurulum — yalnız yenileme başarılıysa

VM Start yapıp SSH Upload File ile iki dosyayı home'a yükle:

- Bilgisayardaki yenilenmiş **özel** `drive_connection.json`.
- `outputs/gcp_acceleration/source_aware_v7_18h_2026-10-13/connection_recovery_package/install_renewed_drive_connection.py`.

Bu özel JSON aktarımı önceki üretim paketlerini yükleme adımından ayrıdır;
app bağlantısı sona erdiği için yalnız private config yenilenir. Home'da
aynı adlı eski dosya varsa doğrudan mv/overwrite yapılmaz; gerçek yükleme
adı ve iki dosyanın kimliği tekrar değerlendirilir. Betik yalnız home'daki
exact `drive_connection.json` adını kabul eder, eski istemci/klasör eşitliği
ve canlı token/folder kontrolü olmadan config'in üzerine yazmaz.

VM SSH'de:

```bash
if printf '%s  %s\n' \
  '9265effd06a3863dc5fd281325216caca83b049ff800fb6faa63f536b4181472' \
  "$HOME/install_renewed_drive_connection.py" | sha256sum --check; then
  timeout 180s ~/wildfire-gcp-work/.venv/bin/python \
    ~/install_renewed_drive_connection.py
fi
```

Üç PASS beklenir: `same_client_scope_folder`, `renewed_token_and_existing_folder`,
`private_connection_installed`. Bu çıktıyı paylaş; kimlik bilgisi paylaşma.
Hata varsa production tekrar başlatılmaz, VM Stop yapılır.

Başarı sonrası [aynı V7 devam rehberi](GCP_SOURCE_RESUME_V7_2026-10-13.md)
kullanılır: yeni Start'ın 18 saat/STOP/automaticRestart=false ayarı ve
güncel terminationTimestamp alınır. Bağlantı düzeltmesi wrapper/registry
scope'unu değiştirmez. V7 exact V6 state ve korunmuş arşiv geçişini tekrar
kontrol eder; generic yeni bilimsel failed durumların kabul kapısı açılmaz.
Bu oturumun OAuth parent tanısı korunur, silinmez. Poweroff ve checkpoint
kimlikleri aynı kalır. Bu rehber yazıldığında yeni bağlantı/VM kurulumunun
başarısı ve tekrar başlatılmış üretim henüz doğrulanmamıştır.
