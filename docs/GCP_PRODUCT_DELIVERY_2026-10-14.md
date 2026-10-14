# Uydu ürünlerinin yerel teslimi ve ayrıntılı geri okuma — 14 Ekim 2026

## Amaç ve kapsam

V7'nin 70 tam ay/59 uygun kısmi gün log/katalog kapanışından sonra ürün
baytlarını VM açmadan korumak ve ayrı yerel bilimsel denetime almak.
Kullanıcı bu aşamaya devam talimatı verdi; VM Stop teyidi korunuyor.
Asıl hedef 72 aydır; iki eksik kaynak günü hâlâ açık. Yeni GCP işi veya
NASA ham kaynak işleme kuyruğu başlatılmadı, Drive nesnesi değiştirilmedi.

## Gerçek teslim sonucu

Mevcut özel bağlantıyla yalnız üretim scope'una ait Drive metadata'sı
okundu. 41.442 nesne / 56.400.524.639 bayt dizin kapsamı var; bu tutar
kompakt sonuçların yanında çift günlüklerini de içerir. Metadata varlığı
tek başına payload veya bilimsel kabul sayılmadı.

Yeni `scripts/cloud/receive_gcp_products.py`, tamamlanma kaydını ve onun
hash ile bağlı ZIP'ini salt okunur indirir. Exact protokol, görev/scope/
worker kimliği, payload anahtarı/boyutu/SHA ve unknown/negative=false
koşulları kontrol edilir. Aynı adlı yerel dosya farklıysa durulur;
eski baytlar değiştirilmez. Tek yazar kilidi, en fazla dört indirme
süreci, 4 GiB toplam kompakt teslim sınırı ve 10 GiB disk rezervi var.

| Teslim türü | Adet |
|---|---:|
| Aylık kaynak/metadata manifesti | 71 |
| Tam ay sonuç paketi | 69 |
| İki kısmi aydan günlük paket | 59 |
| Toplam completion/payload çifti | 199 |

**199/199 teslim tamamlandı; ZIP toplamı 1.278.737.639 bayt** (1,28 GB,
ondalık). İlk teslimde bütün payload'lar canlı Drive'dan okundu. Her
dosya kaydındaki boyut/SHA ile eşleşti. Süre 609,30 saniye; bu kaynak
yeniden işleme hızı değil, bu bağlantıdaki teslim süresidir.

Temmuz 2023 bu üretim scope'una dahil değildir; önceden ayrı kabul edilen
31 günlük referansı [kendi raporunda](COLAB_MONTH_RESULTS_2023_07.md) korunur.
69 tam ay paketi + bu referans, logdaki 70 tam ayı oluşturur. Yeni teslim
referansı yeniden doğruladı iddiası taşımaz. Haziran/Aralık full-month
completion sorguları iki ayda da absent döndü; kısmi ay tam gösterilmedi.

Dosyalar `outputs/gcp_delivery/2026-10-14/compact/products/` altındadır.
Bu kompakt teslim, 56,4 GB'lık dizinin tamamının ikinci yedeği değildir;
tam çift geometri günlükleri ayrıca korunmalı/değerlendirilmelidir.
VM kaynak kaldırma planındaki bağımsız sonuç koruma kapısı açık kalır.

## Yerel native kontrolün başlangıç kaydı

Yeni `scripts/cloud/audit_gcp_products.py`, payload baytlarını yeniden
hash'ler; donmuş metadata/compact doğrulayıcılarını kullanır. Aylık/günlük
ZIP üye/CRC/boyut, receipt ve günlük marker kimlikleri, tam takvim,
kaynak metadata/checksum/tarih bağları, 2.899 hücre anahtarı, alan/oran ve
tarama/sınıf sayımları denetlenir. Ağ socket'leri bu aşamada engellidir;
Earthdata bilgisi veya ham kaynak indirmesi gerekmez. Çift geometri
birleşimleri yeniden hesaplanmaz; kaynak hash referansları kontrol edilir.

**Gerçek pilot:** Ocak 2018, 31 gün/139 kaynak çifti, 143,64 saniye;
native compact tablo/kaynak/zaman denetimi geçti. Pilot sürücüsü ve
raporu ayrı korunmuştur. Sonraki sürücüde yalnız süre/işletim kontrolleri
eklendi: 2 saat sınırı, çocuklarda tek sayısal kütüphane thread'i ve
kesinti raporu. Donmuş bilimsel kod değiştirilmedi.

Tam teslim kontrolü **14 Ekim 15:06 Türkiye**'de dört yerel süreçle
başlatıldı. Kapsam 71 üretim ayındaki 2.158 uygun gündür; Temmuz 2023'ün
ayrı 31 günü bu çağrıya katılmaz. İki saat tamamlanma garantisi değil,
gün/ay başlarında kontrol edilen oturum sınırıdır. Süre dolması/PAUSE/
hata halinde tamamlanmış aylık readback'ler korunur; genel başarı kaydı
yalnız bütün seçilmiş aylar geçerse üretilir. Bu rapor hazırlanırken
dört çocuk süreç görüldü. Sonraki kontrolde ilk dört ayın (Ocak–Nisan
2018) 120 günü geçti; bütün dönem kabulü henüz yoktur. Bilgisayar
açık/uyanık kalmalı; VM kapalı kalır.

Çalışma dizini:
`outputs/gcp_delivery/2026-10-14/compact/audit/20261014T120616395916Z/`.
İlerleme `progress.json`, son başarı `accepted_readback.json`, kesinti
`stopped.json`; başlangıçta ilk ay kapanana kadar progress olmayabilir.
Stdout/stderr `compact/native_full_stdout.log` ve `native_full_stderr.log`.
Gerekli kontrollü duruş için `compact/PAUSE` dosyası gün sınırında okunur;
kendiliğinden otomatik yeniden başlama kurulmadı.

Yeni teslim/audit/Drive davranış kontrolleri **53 passed**, lint/format
geçti. Tek warning, reddedilmesi sınanan ZIP tekrar üyesinin oluşturma
uyarısıdır. Yanlış scope/worker/policy/anahtar, bozuk payload, immutable
çakışma, başka yazar kilidi, uygunsuz takvim, ZIP üyeleri ve ağ/süre
sınırları için olumsuz kontroller var. Test başarısı bütün dönem gerçek
native denetiminin tamamlandığı anlamına gelmez.

## Bütün dönem kontrolü tamamlandı

Tam denetim **14 Ekim 16:05:57 Türkiye**'de
`delivered_compact_native_readback_passed` ile bitti: **71 ay, 2.158 gün,
18.423 kaynak çifti**, dört süreçte **3.581,05 saniye** (59 dakika
41 saniye). Bu süre yerelde teslim edilmiş kompakt ürünlerin sayısal,
kaynak ve zaman geri okumasıdır; NASA ham kaynak işleme hızı değildir.
Stderr sıfır bayt, `stopped.json` yok, audit yazıcı kilidi kaldırılmıştır.

Final `accepted_readback.json` her ayın ayrı değişmez readback'ini
taşır. `progress.json` son ara bildirim olan 71/71 `running` durumunda
kalmıştır; başarı kanıtı genel final raporudur. Eski ara kayıt veya
kabul edilmiş ürün dosyaları bu nedenle elle değiştirilmedi.

Temmuz 2023'ün önceden kabul edilen 31 günüyle birlikte mevcut kapsam
**2.189/2.191 eğitim takvim günü**dür: 70 tam ay ve iki kısmi ayın
59 günü. İki kaynak günü eksik kalır; bu sayı etiketli veya modellemeye
uygun örneklem sayısı değildir. Gözlem/negatif etiketi, tam geometri
birleşimi, bağımsız olay doğrulaması ve bulut kaynaklarını tamamen
kaldırmak için gereken ek sonuç koruması ayrı konulardır.

Final kanıt:
`outputs/gcp_delivery/2026-10-14/compact/audit/20261014T120616395916Z/accepted_readback.json`.
SHA-256: `52be7c3e8fb02798a1e21538607a4612a0c479c105b90157b195385eea4d6781`.
16:35 Türkiye'deki ayrı kapanış kontrolü bütün aylık readback'lerin
final ile eşitliğini, exact takvim/çift sayılarını, 199 payload'ın
yeniden boyut/SHA eşleşmesini ve 22 donmuş girdinin değişmediğini
doğruladı. Bu kontrol sayısal algoritmayı yeniden çalıştırmaz.
Kayıt `outputs/gcp_delivery/2026-10-14/native_final_handoff_20261014.json`,
SHA-256 `ff03cedb8b8483998b1453ae2c9597f1bf2268a24ad93516f24d93e8e6bad9df`.
Sonraki yerel aşama [72 aylık aday özellik birleştirmesidir](DATASET_TRAINING_JOIN_2026-10-14.md).

## İki kaynak günü araştırması

Kullanıcı NASA'dan 3–5 gün önce alındı/inceleniyor bileti aldığını,
sonrasında teknik yanıt gelmediğini bildirdi. Bu biletin sekiz geolocation
dosyası için çözüm sunduğu veya aynı teknik konuyu kapsadığı varsayılmadı.

Anonim resmî CMR'de sekiz required_geolocation exact adı yeniden arandı:
sekiz HTTP 200 / sıfır hit. İlgili sekiz fire granülünün desenli isim
sorguları her biri tek kayıt döndürdü; dönen V002 üretim adları mevcut
donmuş katalogla aynı, yeni uyumlu fire sürümü bulunmuş sayılmaz.
Bu aramalar bütün NASA arşivlerinden yokluk veya sürüm eşdeğerliği kanıtı
değildir. Raw kaynak indirmesi ve kaynak registry değişikliği yapılmadı.

[NASA VJ103IMG ürün tanımı](https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/VJ103IMG),
dosya son alanını üretim zamanı olarak açıklar; geolocation alanları
üst seviye ürünlerin girdisidir. [NASA L1 değişim notları](https://ladsweb.modaps.eosdis.nasa.gov/api/v2/content/archives/Document%20Archive/Science%20Data%20Product%20Documentation/Processing%20and%20Algorithm%20Version%20History/VIIRS_Level-1_Change_Summary.pdf)
koleksiyon değişimlerindeki geolocation güncellemelerini anlatır; bunlar
bu sekiz dosyanın özel farkını açıklayan veya eşdeğerlik veren bir yanıt
değildir. Gün dizinleri web aracında açılamadı; bu erişim sınırlaması
dosya yokluğu diye kullanılmadı. Ad değiştirme/guard kaldırma uygulanmaz.

Çözüm seçenekleri: exact eski girdiye erişim veya sağlayıcının teknik
bilgisiyle eşleşen yeni fire/geolocation çiftinin ayrı provenance ve
bilimsel kabulü. Gerekirse sağlayıcıya verilecek teknik sorular: registry'deki
sekiz eski dosya erişilebilir mi; mevcut fire dosyalarının bildirdiği girdiye
karşı hangi arşiv/işleme sürümü kullanılmalı; desteklenen eşleşmeyi hangi
metadata ve checksum'lar kanıtlar? Dış iletişim gönderilmedi. Yeni iki günlük
iş ancak kaynak çözümü doğrulanınca ayrı planlanır; 70 ay tekrarlanmaz.

## Kanıtlar

Çıktı kökü `outputs/gcp_delivery/2026-10-14/`:

- `drive_inventory_20261014.json`: SHA-256
  `bc1ff5c0246a05787afb3971335694cc08ed949cc47c4ac78de1b9e523f53d7f`.
- `compact/receive_final_20261014T120535015447Z.json`: SHA-256
  `74827f6b182bc4acac4ab42651e7417daa9f1cbf974fd0c87aa52ab3e2eb9057`.
- Pilot `compact/audit/20261014T115953508233Z/accepted_readback.json`: SHA-256
  `56a95a8dcbbfba70aeb82600bcdae5155998b7ab2d33b9101cd12acc5d13ddb3`.
- `pilot_audit_driver.py`: SHA-256
  `22d5673981b7d85ba67dc7e41078a3556ec0232f40a8e7c907705809ba1852c8`.
- `cmr_required_geolocation_recheck_20261014.json`: SHA-256
  `ae5f043e73afc3f121ea9a766a67585a1cce2737878a2c7703f8541cc7242be8`.
- `cmr_fire_alternatives_20261014.json`: SHA-256
  `7d0073d84ebdcb19f36fa2ce94f22b6c58108c631e7a87b9f552065491bc072b`.
- `deferred_month_marker_check_20261014.json`: SHA-256
  `3828beab4d659742f04605c9ba59917982ec1edd021819337f4f818d4c9529ba`.
- Hazırlık/çalışma snapshot'ı `delivery_prepared_readback_20261014.json`:
  SHA-256 `32a90d8ee90005af2f771f6abcf5eca438f175be4c4a7001f9f935dc6c5e105a`.
  Sürücü hash'leri, 53 kontrol ve o andaki native ilerleme ayrı kayıtlıdır.

Private bağlantı/token/değerler raporlara ve Git'e alınmadı. Kaynak ürünler,
completion kayıtları ve önceki raporlar değiştirilmedi. Nihai etiket kapısı,
habitat/olay kararları, 2024 doğrulama hazırlığı ve kapalı 2025 final testi
bu veri teslimiyle açılmış veya tamamlanmış sayılmaz.
