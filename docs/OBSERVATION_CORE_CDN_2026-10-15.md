# Başlık teşhisi sonucu ve CloudFront uyumluluğu — 15 Ekim 2026

**Sonraki gerçek tekrar:** aşağıdaki ilk CloudFront sürümü yangın kaynağında
imza parametresi kontrolüyle durdu. Bu belgenin sonundaki çift imza biçimi
ve yeni plan kaydı güncel devam adımıdır; önceki deneme başarı sayılmaz.

## Gerçek teşhis ve yerel kaynak izi

Kullanıcı özel terminalde iki başlık teşhisini tamamladı. Yerel dizin
`outputs/reports/dataset/observation_core_access_v1/20261015T100327Z_a878c4f1/`;
`access_probe.json` SHA-256
`cb71291dadccfab73560d5dee8d7ad3e4ed0f0bff75b50407acdee081dfe1dde`.
Kapanış hash'i ve launcher'ın `worker_finished` durumu okundu.

İlk çiftin iki kaynağı da 303, farklı origin, aynı bilimsel dosya adı ve
sorgulu hedef verdi. Önceki kodun S3 hedef kontrolü ikisini de reddetti.
Bu kayıt indirme başarısı değildir; hedefin tam adı kaydedilmediği için
iki gerçek 303'ün ikisinin de aynı CDN olduğu kesinleştirilmiş sayılmaz.

Tarayıcıdan alınmış konum dosyasının Windows `Zone.Identifier` kaynak
metadatası ayrıca yerelde ayrıştırıldı. Tam URL ve sorgu değerleri
yazdırılmadı veya rapora alınmadı. Kamuya açık CloudFront host sınıfı,
CMR'deki bucket'ın tam bölgesel S3 host'u ve tam nesne anahtarıyla eşleşen
bir CDN rota biçimi görüldü. Expires/Signature/Key-Pair-Id ve A-userid
alanları var; değerleri saklanmadı. Windows metadatasının sonundaki NUL
yalnız bu yerel kayıt okunurken ayrıldı; gerçek HTTP doğrulayıcısı kontrol
karakterli imzayı kabul edecek şekilde gevşetilmedi. Geçmiş imzalı URL
yeniden ağ isteğinde kullanılmadı.

Önceki indiricinin yalnız doğrudan S3 imzalama biçimini kabul etmesi,
bu gerçek tarayıcı dağıtımıyla somut bir uyumsuzluktur. Bu uyumsuzluk
giderildi; yeni canlı aktarımın geçtiği henüz söylenemez.

## Dar kapsamlı değişiklik

NASA'nın kayıtlı iki HTTPS veri host'una yapılan tam kaynak isteğinin
tek Location yanıtında S3 veya CloudFront biçimi kabul edilebilir.
CloudFront desteği yalnız `d…cloudfront.net` dağıtım host biçimi, HTTPS,
varsayılan/443 port, kullanıcı/parola/fragment içermeyen hedef için açıldı.
CMR'deki tek izinli bucket ve **tam nesne anahtarı** eşleşmelidir.
Doğrudan bucket/key veya bir rota bileşeni altında bucket'ın tam bölgesel
S3 host'u ve tam key biçimi kabul edilir. Yalnız dosya adı eşitliği yetmez;
farklı bucket/key, traversal ve ters slash reddedilir.

Expires, Signature ve Key-Pair-Id tekil/dolu ve biçimsel olarak geçerli
olmalıdır; yalnız A-userid ek alanına izin verilir. CDN imzasını CloudFront
doğrular; yerel biçim kontrolü kriptografik doğrulama iddiası değildir.
CDN host'u tek başına güven kanıtı sayılmaz: Location yalnız onaylı NASA
kaynağından alınır, tam CMR bucket/key kontrolü ve son tam dosya boyut/
tarihsel SHA/varsa sağlayıcı checksum'u zorunludur. İkinci isteğe Earthdata
tokenı, parola, çerez, netrc veya ortam proxy'si aktarılmaz. Yeni kimliksiz
oturum yalnız bu tek imzalı hedefe gider; ikinci yönlendirme reddedilir.
S3 ile CloudFront başarı alanları ayrı kaydedilir.

## Test ve yeni hazırlık

CloudFront için **11 yeni vaka dahil 179 ilgili test** geçti. Tam key/
bucket/host/rota/imza değişiklikleri, ek/çift parametreler, ikinci
yönlendirme, kimliksiz oturum ve tam bayt/hash kontrolü sınandı. Kaynak
kayıtlarının ve 900 saniye/2 GB/20 GB sınırlarının anlamı korunur.
Beş değişen Python dosyasında lint/format geçti. Daha önceki başlık
teşhisinin dokuz testi de bu 179 içindedir; eski sayılara ek yeni bir
üretim sonucu uydurulmadı.

Yeni hash bağlı plan:
`outputs/reports/dataset/observation_core_transfer_v1/20261015T101223Z_e8e82f70/`.
`native_plan.json` SHA-256
`8e5168d5436da59bd60315f6f51315b9fb6f1ded1f0e7ebd123e0458620e2696`;
`readback.json` SHA-256
`0a412a5e1c338d1fa491036b8c8962271c796dc61b03feb0b3a19e8915d2a5f8`;
`completion_readback.json` SHA-256
`0ef788a6f4ad67a7e415f1c66b0918d1f0654b93048a09e877b71e29f70a0942`.
117 giriş/iki çıktı kapanışı ve 22 donmuş üretim girdisi kontrolü geçti;
eski native okuyucu tanığı ayrıca hazırlığın parçası olarak tekrarlandı.
Eski tarayıcı çiftinin 191.244.528 baytı aynı kaynaklarla yeniden kontrol
edildi. Önceki kabul edilmiş plan/rapor/ham dosyalar değiştirilmedi.

Yeni planın ayrı cache dizini henüz yok. Böylece aşağıdaki deneme eski
iki dosyayı cache'ten alarak uzak erişim başarısı ilan edemez. Yalnız aynı
ilk çift ve 191.244.528 bayt için gerçek indirme/başlık kontrolüdür:

```powershell
Set-Location "C:\PROJELERIM\wildfire-risk-prediction"
.\.venv\Scripts\python.exe scripts\firms\run_observation_core_pair.py --latest-plan --run-one --prompt-login
```

Kimlik bilgileri önceki teşhisten saklanmadığı için özel giriş yeniden
gerekir. Henüz yeni gerçek aktarım sonucu yok. Bu deneme bütün 292 çiftin
işlenmesi değildir; etiket/model, geniş mekânsal pilot ve nihai birleştirme
kapıları korunur. Yeni VM/EE işi veya eğitim dışı veri erişimi yoktur.

## Birincil kaynaklar

[NASA Cumulus dağıtım belgesi](https://nasa.github.io/cumulus/docs/next/deployment/)
TEA/CDN dağıtım mimarisini,
[TEA teknik belgesi](https://tea-docs.asf.alaska.edu/technical/)
CloudFront üzerinden veri erişimini açıklar.
[AWS CloudFront imzalı URL belgesi](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-signed-urls.html)
imza akışını ve sunucu doğrulamasını açıklar. Bu genel belgeler tek başına
projemizin canlı aktarımının başarılı olduğunu göstermez; yerel kaynak
metadatası ve tam dosya hash kontrolü ayrıca belirtilmiştir.

## Sonraki gerçek hata ve iki CDN imza biçimi

`outputs/reports/dataset/observation_core_native_v1/20261015T103030Z_44d28f9e/`
çalışması girişten sonra yangın kaynağında `cloudfront_parameters` ile
durdu. İlk yanıt 303, hedef sınıfı CloudFront ve imza alanlarının varlığı
doğrulandı; tam nesne kontrolü geçmişti. İmza koşulları geçmediğinden
hedefe istek yapılmadı, yeni ham dosya yazılmadı. `failure.json` SHA-256
`f69d866b4eac92b6ba98630e19bb2a1e2f7f0869c6b8ec04dd451f969af9fda3`.

İlk destek yalnız tarayıcı konum dosyasında görülen CloudFront canned
biçimini kapsıyordu. [TEA teknik kaynağı](https://tea-docs.asf.alaska.edu/technical/)
CloudFront üzerinden önceden imzalanmış S3 URL kullanımını da açıklar.
[TEA log belgesi](https://tea-docs.asf.alaska.edu/troubleshooting/)
A-userid/sourceip alanlarının anlamını belirtir. Bunların değerleri
kişisel olabilir; hiçbir değer rapora alınmaz. Gerçek eski hata kaydı
yalnız birleşik guard içerdiği için hangi alt parametrenin durdurduğu
geriye dönük kesinleştirilmedi. Belgelenmiş ikinci imza biçimini eksik
desteklemek somut kod eksikliğidir; bu düzeltme canlı başarı sayılmaz.

Şimdi tam CMR bucket/key ve kimliksiz tek adım korunarak iki ayrı biçim
kontrol edilir: S3 SigV4 taşıyan CloudFront veya CloudFront canned.
İkisi karışık olamaz. Her alan tekil/dolu, parametre adları sabit izin
listesinde ve seçilen imza biçimi geçerli olmalıdır. S3 SigV4 alanları
X-Amz-Algorithm/Credential/Signature ve bilinen Date/Expires/Security-Token/
SignedHeaders'tır; ek log alanları yalnız A-userid ve sourceip olabilir.
İmza doğrulamasını servis yapar; tam dosya SHA/boyut kontrolü zorunludur.

Yeni güvenli tanı yalnız hangi biçimin alanlarının bulunduğunu, tekil/dolu
değer koşulunu ve alan izin listesinin geçip geçmediğini boolean olarak
kaydeder. Alt guard'lar ayrı kod verir: cdn_query_cardinality,
cdn_signing_scheme, cdn_query_fields, cdn_sigv4_shape, cdn_canned_shape.
Hata mesajının son satırı artık kontrol kodunu içerir; kullanıcıyı yalnız
belirsiz genel durumu paylaşmaya yönelten önceki metin kaldırıldı.

**11 ek vaka dahil 190 ilgili test** geçti; final mesaj değişikliğinden
sonra etkilenen 75 aktarım/erişim testi ayrıca geçti. İki imza biçimi,
log alanları, karışık/eksik/bozuk/çift/bilinmeyen parametreler ve özel
değerlerin rapora geçmemesi sınandı. Beş dosyada lint/format geçti.
Yeni plan 117 giriş/iki çıktı ve 22 donmuş üretim girdisi kapanışında:
`outputs/reports/dataset/observation_core_transfer_v1/20261015T103459Z_e186e885/`.
`native_plan.json` SHA-256
`b3659c2b6a7694bd7b7a4b36f836c71d3f37d2d794244f2e5ce76fedd6d81387`;
`readback.json` SHA-256
`882f76486080db6ca90724b3a2d50edbeb27ffc7ba12e8f7f7cac3841e277a29`;
`completion_readback.json` SHA-256
`77e3398ee8dc4971a1e2448f94a6148d49cf4770262af06e10dd60f2e7eded61`.

İki eski ham dosya aynı boyut/hash ile korunuyor; yeni plan cache'i yok.
Yukarıdaki `--latest-plan --run-one --prompt-login` komutu bu yeni plana
bağlanır. Yalnız aynı iki kaynak/191.244.528 bayt ve 900 saniyelik sınır
geçerlidir. Özel giriş kullanıcıda yeniden yapılmalı; yeni gerçek aktarım
henüz yok. Etiket/model/bulut işi veya nihai birleştirme yapılmadı.

## Ek sağlayıcı alanlarının gerçek reddi ve düzeltme

`20261015T103944Z_3595d6a4` gerçek tekrarında canned imza alanları ve
tekil/dolu değerler geçti; sabit alan listesi `cdn_query_fields` ile
durdurdu. Ek alan adı/değeri kaydedilmediğinden sonradan uydurulmadı.
Failure SHA-256 `151a985751b21d6a5b997ee6dc32ef0c382855c5871e46358965a53890a950a1`.
Hedefe istek ve yeni ham dosya yazımı yok; eski tarayıcı çifti korunuyor.

[AWS canned URL belgesi](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-creating-signed-url-canned-policy.html)
sağlayıcının kendi sorgu alanlarını ve isteğe bağlı Hash-Algorithm alanını
destekler. [AWS imza açıklamasına](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-signed-urls.html)
göre ek alanları imzadan sonra değiştirmek imzayı bozar. Sabit ek-alan
listemiz gereğinden dardı. Yeni sürümlü politika, onaylı NASA yanıtının
aynı tam CMR bucket/key hedefindeki sağlayıcı alanlarını opak ve aynen
korur; ad/değerlerini yazmaz. İmza ailesi, ayrılmış alan çakışmaları,
tekil/dolu değerler ve tam dosya boyut/SHA/checksum koşulları korunur.

En fazla 32 alan, ASCII anahtar biçiminde 64 karakter, çözülmüş toplam
65.536 karakter ve değer başına 16.384 karakter sınırı vardır; kontrol
karakterleri yasaktır. versionId/partNumber/uploadId kaynak seçicileri
reddedilir. Custom Policy desteklenmez; Hash-Algorithm yalnız SHA1/SHA256
olabilir. İkinci yönlendirme izlenmez, ikinci oturuma EDL kimlik bilgisi
aktarılmaz. Önceki plan/rapor sessizce değiştirilmedi.

**13 yeni vaka dahil 203 ilgili test** geçti: iki imza ailesinde ek
alanların değiştirilmeden iletilmesi ve rapora geçmemesi, hash algoritması,
ayrılmış alanlar/seçiciler, çift/bozuk/aşırı büyük/kontrol karakterli
alanlar sınandı. Dört değişen Python dosyasında lint/format geçti.
Yeni plan `outputs/reports/dataset/observation_core_transfer_v1/20261015T104255Z_9750c1c4/`.
Plan SHA-256 `fa3cce2822c3825e28352468fa4db8e107f59215f95fab7b8272454900d44edc`;
readback SHA-256 `ecbceb5b5be38c24cb1f8eaca6c71e84fec5a79db20f05555f07029dc582f595`;
kapanış SHA-256 `2b52e3b54f55c919ce08bf6084563a44f40f857f4d84d23f0b7792cf9e1f5099`.
117 giriş/iki çıktı ve 22 donmuş girdi kontrolü geçti. İki eski dosyanın
191.244.528 baytı yeniden doğrulandı; yeni cache yok.

Aynı `--latest-plan --run-one --prompt-login` komutu yeni plana geçer.
Kapsam ilk çift/191.244.528 bayt/900 saniyedir; yeni gerçek aktarım sonucu
henüz yok. Etiket/model, nihai birleştirme veya bulut işi başlatılmadı.

## İlk gerçek otomatik aktarımın yerel kabulü

15 Ekim'de kullanıcı özel girişli tek çift komutunu tamamladı.
`outputs/reports/dataset/observation_core_native_v1/20261015T104742Z_295e4bc3/`
makbuzu `one_pair_bytes_and_headers_passed`; başlatıcı makbuzu
`child_completed` durumundadır. Giriş bilgileri kaydedilmedi; süreç sınırı
900 saniyedir. Bu süre gerçekleşen indirme süresi olarak yorumlanmaz.

SNPP:2018045.0000 çiftinin iki kaynağı CloudFront üzerinden alındı.
İkisinde de `reused=false`; kaydedilen toplam yeni ağ aktarımı
**191.244.528 bayt** (ondalık 191,24 MB). Yangın dosyası 1.087.180,
konum dosyası 190.157.348 bayttır. Bu sonuç önceki tarayıcı kopyalarının
önbellekten kabulüne değil, yeni otomatik aktarım kaydına dayanır.

Yerel geri kontrolde iki dosyanın gerçek boyutu ve tarihsel SHA-256
değeri tekrar hesaplanarak doğrulandı. Konum dosyasının sağlayıcı
checksum'u geçti; yangın dosyası için sağlayıcı checksum'u yoktur.
Native başlık denetimi yeniden çalıştırıldı: gerçek konum girdi bağı,
zaman/CMR aralığı, ortak 6.496×6.400 boyut, fire/QA türleri ve
SNPP:32640 yörünge kimliği geçti. Planın 117 girdisi ve 22 donmuş üretim
girdisi hash ile yeniden kontrol edildi. Yeni önbellekte yazıcı kilidi
ve `.part` dosyası yok; eski tarayıcı dosyaları korundu.

- Plan SHA-256: `fa3cce2822c3825e28352468fa4db8e107f59215f95fab7b8272454900d44edc`.
- `native_probe.json` SHA-256: `2da1534f3a0e57a8c736ea37199fc2158ba3f329f1862b96c2d5cf87788c05f3`.
- `completion_readback.json` SHA-256: `62e68750bf26033487e861a5d317c6439e9a72e91bf62da88cfe3882a12aed06`.

Kapanışın rapor hash'i gerçek raporla eşleşti. Önceki düzeltme aşamasında
çalıştırılan 203 testin sonucu tarihsel kayıttır; bu kabul sırasında
test paketi yeniden çalıştırılmadı. Yeni doğrulama gerçek dosya ve
makbuzların çevrimdışı geri kontrolüdür; yeniden indirme yapılmadı.

Kabul yalnız bu çiftin otomatik erişimi, baytları ve native başlıkları
içindir. Piksel konumları, tarama zamanı/kalite değerleri ve hücre
kapsaması henüz mekânsal olarak denetlenmedi; 292 çiftlik envanter veya
156 hücre-günlük pilot kabul edilmedi. Sonraki aşama bu mekânsal
kontrollerin mevcut çift üzerinde hazırlanmasıdır. Etiket üretilmedi;
`daily_observation_status=unknown`, `negative_label_permitted=false`,
`model_ready=false` korunur. Yeni bulut işi ve nihai birleştirme yoktur.
