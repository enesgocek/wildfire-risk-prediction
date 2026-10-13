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

## Terminal kapanması sonrası yerel canlı doğrulama

Kullanıcı yeni akışta `Authorization received. Return to your terminal.`
mesajını, ardından terminali kapattığını bildirdi. Başarı çıktısı elde
edilemediği için yalnız callback mesajı kabul edilmedi. Özel dosyanın
mtime'ı 13 Ekim 14:17:33 UTC / 17:17:33 Türkiye, boyutu 374 bayt olarak
görüldü; pending dosyası ve Python süreç satırı yoktu.

Yerel canlı kontrol yeni dosyadan OAuth refresh ve mevcut folder metadata
isteğini çalıştırdı. Exact şema, drive.file kapsamı, folder id/mime/trashed,
canAddChildren ve istek sırasında özel dosya baytlarının değişmediği geçti.
Credential/folder değerleri yazdırılmadı veya rapora kaydedilmedi. Drive
nesnesi oluşturulmadı; mevcut klasöre yazma yetkisi metadata ile sınandı,
gerçek yazma işlemi yapılmadı. VM'deki eski client/folder eşitliği henüz
kontrol edilmedi; bu sonraki private installer'ın zorunlu koşuludur.

Kanıt `outputs/gcp_acceleration/source_aware_v7_18h_2026-10-13/local_connection_verified_20261013.json`;
SHA-256 `5beba1638f7b558744a9200d1b3ed380c8ad832f69c4e4c33763a360242f52dd`.
Yeni yerel bağlantı doğrulandı; önceki başarısız izin denemesi tarihli
bulgu olarak korunur. VM kurulumu ve üretim devamı henüz doğrulanmadı.

## VM kurulum çıktısının geri okuması

Kullanıcı ilk yüklemede installer dosyasının bulunamadığını bildirdi;
hash kontrolü başarısız olduğundan `if` içindeki kurulum çalışmadı. Dosya
yüklendikten sonraki SSH çıktısında pinned hash OK ve
`PASS same_client_scope_folder`, `PASS renewed_token_and_existing_folder`,
`PASS private_connection_installed` görüldü. Installer sözleşmesine göre
eski VM client/scope/folder ile eşitlik, canlı OAuth/folder kontrolü ve
özel config atomik kurulumu geçti. Credential değerleri paylaşılmadı.

Bu kullanıcı uzak çıktı geri okumasıdır; bağımsız canlı VM sorgusu veya
yeni üretim kabulü değildir. Yerel V7, yeni registry ve installer hash'leri
yeniden karşılaştırıldı ve değişmedi. Aynı V7 ile devam öncesinde mevcut
Start'ın yeni terminationTimestamp ve 18 saat/STOP/automaticRestart=false
ayarları istenir; eski zaman kullanılmaz. Önceki 65 ay korunur, kaynak
ertelemesi ve negatif etiket kuralları değişmez.

Kanıt `outputs/gcp_acceleration/source_aware_v7_18h_2026-10-13/vm_connection_install_user_readback_20261013.json`;
SHA-256 `0b538635157a12cd1cc2f124a7daa4ede39f0af65a5f29e6d28a1eeae21c29b8`.

## OAuth kurtarma sonrası güncel oturum sınırı

Üç private installer PASS sonrasında kullanıcı Cloud Shell describe
çıktısı paylaştı: RUNNING, maxRunDuration 64800 saniye, STOP ve
automaticRestart=false. Yeni terminationTimestamp
`2026-10-14T13:35:01.727602Z` (14 Ekim 16:35 Türkiye). Eski kapanış
zamanı kullanılmaz. Yerel saat kontrolü 13 Ekim 19:45:06 UTC olduğundan
yeni sınır gelecektedir; Start sonrası geçen süre üst sınırdan düşer,
üretim çağrısı yeni bir 18 saat başlatmaz.

V7 ve registry SHA-256 değerleri başlatma rehberiyle aynı. Kullanıcıya
aynı pinned V7, yeni zaman ve --poweroff ile yalnız bir başlatma komutu
verilir; yeni paket veya kaynak/etiket kuralı değişikliği yoktur. Bu
kullanıcı ayar çıktısı ve yerel hazırlık kontrolüdür; bağımsız VM sorgusu
veya üretimin gerçekten başladığı kabulü değildir. Launcher/progress
ile running ve yeni V7 kimliği sonraki adımda doğrulanır.

## OAuth kurtarma sonrası uzak üretim ilerlemesi

Kullanıcı ilk kontrolünde progress `running`, phase `june_safe_days`,
V7 hash `37a4c4c904b49cac1bb4bc690b485fea19b41e922f24002526ca5ad9d6d0bc3b`
ve `2026-10-14T13:35:01.727602Z` sınırı bildirdi. error_type/failed_month/
failed_phase None; pairs_processed_this_invocation 16. Launcher'da dört
Aralık aşaması referans ayı yeniden doğrulanmış, Haziran aşamasına
geçilmiş ve 16 saved/verified satırı görülmüş. Önceki kapanma/hata
satırları aynı logun önceki denemesine aittir; güncel progress ve ardından
gelen yeni üretim satırları yeni çağrının çalıştığını gösterir.

Beş tam ay değeri bu çağrıda geri okunan ayları ifade eder, önceki
65 aylık kabulün silindiği anlamına gelmez. Bu kullanıcı uzak çıktı
kontrolüdür; yeni tam ay veya yerel bilimsel payload kabulü yoktur.
13 Haziran 2018 ve 31 Aralık 2023 ertelenmesi, gözlem unknown ve negatif
etiket false koşulları korunur. Bir sonraki takipte yeni çift/gün ve
phase ilerlemesi izlenir; başlatma komutu tekrar çalıştırılmaz.
