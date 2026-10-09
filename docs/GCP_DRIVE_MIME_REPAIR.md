# Drive ZIP türü düzeltmesi — 6 Ekim 2026

> Dönemsel uygulama kaydı. Kurulum, maliyet ve bekleyen iş ifadeleri belgenin
> ilgili çalışma aşamasına aittir. Güncel durum [STATUS.md](STATUS.md), mevcut
> üretim yolu [devam rehberinde](GCP_SOURCE_AWARE_CONTINUATION_2026-10-09.md) izlenir.

Gerçek VM çalışması, worker'da ValueError ile durdu. Salt okuma teşhisi:
package_integrity/private_connection/oauth_refresh/drive_folder_access PASS;
drive_object_listing FAIL: Drive object type. Yalnızca MIME sayımını
paylaştım: **application/x-zip, 1 dosya**. Token, dosya kimliği veya içeriği
sohbetle paylaşılmadı. İlk yüklemenin bir dosya oluşturduğu görülüyor; geri
okuma/completion başarısı henüz kanıtlanmadı.

Eski adapter sadece application/octet-stream kabul ediyordu. Bu gereğinden
katıydı: MIME etiketi byte bütünlüğünün yerine geçmez. ZIP için octet-stream,
application/zip, application/x-zip ve application/x-zip-compressed; marker
için octet-stream, application/json ve text/plain kabul edilir. Yanlış rol,
Google editor/shortcut, HTML/image ve bilinmeyen türler reddedilir. Kimlik,
byte sayısı, SHA-256, ZIP üyeleri/CRC, bilimsel readback ve completion-last
korundu. Yeni yükleme metadata'sında role uygun ZIP/JSON türü kullanılır.
[Google MIME alanı](https://developers.google.com/workspace/drive/api/reference/rest/v3/files).

13 MIME regresyon testi; türü tanınsa bile değiştirilmiş byte'ların reddi ve
idempotent aynı dosya kontrolü eklendi. Teşhis betiğinin 12 testi statik kontrol
etiketleri dışında hata içeriği/token yazdırılmasını reddeder.

Yüklenmiş eski paket yeniden oluşturulmadı, eski remote kayıt silinmedi.
Yeni paket `outputs/gcp_drive_proof_v2/wildfire_gcp_drive_proof_v2.zip`:
6.866.338 bayt; SHA256
`7c0366b82afdf33f6b8c2873cbcd096efc2d1bb8237827cb8f8011504ade393f`.
Yeni manifest SHA
`bddfd564a8f6a0f0190e15abecbefd8efb6ca08890930e406bf09bb4b90f2982`;
ürün SHA/3.982.961 bayt ve donmuş bilimsel paket aynı. Yeni manifest ayrı iş
kimliği oluşturur; eski uncommitted dosya bitmiş sayılmaz. V2 worker/log
dizini `~/wildfire-gcp-drive-proof-v2`; paketi `~/wildfire-gcp-drive-package-v2`
altında aç. Mevcut özel bağlantı dosyası aynen kullanılır, yeniden OAuth yok.

V2 hata mesajları doğrulanmış kodun yalnızca sabit kontrol etiketleri ve
HTTP kodlarını gösterir; rastgele exception/response/credential gövdesi yok.
Süre/Stop, ödeme ve VM ayarı değiştirilmedi. Yeni NASA ham indirme yok.
Gerçek bulut v2 çalışması ve indirilen rapor hâlâ bekleniyor.

Son v2 paketle yerel save/restore ayrı süreçlerde gerçek bilimsel ürünle
geçti; tüm 467 test ve Ruff/144 Python dosyası biçimi geçti. İlk yüklenmiş
ZIP'in SHA'sı değişmedi. V2 sonucu `outputs/gcp_drive_proof_v2/received/`
altına alınır. Yerel özet doğrulayıcıda `--revision v2` seçilmelidir; orijinal
manifest/raporların üstüne yazılmaz.
