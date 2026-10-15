# Tek çift denemesinde HTTP 303 ve dar düzeltme — 15 Ekim 2026

**Sonraki gerçek tekrarlar:** iki deneme ValueError ile durdu. Kesin guard
eski kayıtta bulunmuyor. [Yeni güvenli teşhis ve güncel kısa komut](OBSERVATION_CORE_DIAGNOSTICS_2026-10-15.md)
ayrı kayıttır; aşağıdaki testler canlı indirme başarısı değildir.

İlk gerçek yerel indirme denemesi, `SNPP:2018045.0000` çifti için veri
yanıtı aşamasında **HTTP 303** nedeniyle durdu. Bu bir başarı kaydı değildir.
Önceki hazırlık ve kabul edilmiş bilimsel çıktılar değiştirilmedi; düzeltme
yeni kod hash'leriyle yeni plan dizininde hazırlandı.

## Yerel hata kanıtı

`outputs/reports/dataset/observation_core_native_v1/20261015T001237Z_71e3538e/`
altındaki `failure.json`, fazı `bounded_file_transfer`, hata türünü
`DataResponseError`, HTTP durumunu `303` olarak bildiriyor. Başlatıcı makbuzu
alt sürecin başarısız tamamlandığını ve kimlik bilgisi yazılmadığını kaydediyor.
Özel hata mesajı, token veya Location URL'si saklanmamış.

- `failure.json` SHA-256:
  `eecc737c8c7a5e392a88b035b500ebe0106104e7a640bfaae028a9b421599274`.
- `launcher_receipt.json` SHA-256:
  `6c550d569112148c2360ee7b7e76dec33e89491804c9717995d12656c1ba6105`.

İncelemede bu planın yerel ham önbelleğinde **sıfır dosya** bulundu.
Dolayısıyla bu denemede tamamlanmış bir dosya veya temizlenmesi gereken
yarım dosya/kilit yok. Bu gözlem diğer çalışma dizinlerine genellenmez.
Hata kaydı parola yanlışlığı veya kaynak dosyanın yokluğu olarak yorumlanmadı.

## Neden ve sınır

İlk indirme kodu bütün yönlendirmeleri reddediyordu. Bu tercih gereğinden
katıydı: NASA'nın Cumulus dağıtım belgesi, kimliği doğrulanan isteğin
bilimsel dosya için imzalı S3 adresine yönlendirilebildiğini açıklar.
[NASA Cumulus Distribution API](https://nasa.github.io/cumulus-distribution-api/).

İki özgün NASA adresine yapılan anonim, gövdesi okunmayan başlık sorgusunda
302 ve Earthdata giriş alanına yönlendirme görüldü. Bu anonim sorgular
kullanıcının önceki **kimlik doğrulamalı 303 hedefini** kanıtlamaz. İlk
denemede Location kaydedilmediği için o hedefin S3 olduğu sonradan kesin
ilan edilmez. Yeni sürüm yalnız izin verilen tam S3 hedefini canlı istekte
doğrulayacaktır; genel otomatik yönlendirme açılmaz.

## Uygulanan düzeltme

İlk istek yine yalnız kabul edilmiş tam NASA dosya adresine gider.
302/303/307/308 dönerse hedef için şu koşullar birlikte aranır:

1. HTTPS, varsayılan/443 port, kullanıcı/parola ve fragment içermeyen hedef.
2. Katalogdaki `GET DATA VIA DIRECT ACCESS` kaydında tanımlı **aynı S3
   bucket ve tam nesne yolu**. Bu kapsamda yalnız `lp-prod-protected`
   veya `prod-lads` kabul edilir; başka dosya/sürüm seçilmez.
3. Yalnız ilgili bucket'ın bölgesel/global S3 host biçimi veya us-west-2
   bölgesel path biçimi; genel `*.amazonaws.com` izni verilmez.
4. Beklenen AWS imzalı istek parametreleri. İmzayı servis doğrular;
   yerel kontrol imzanın kriptografik doğrulaması diye sunulmaz.
5. Ayrı, temiz bir HTTP oturumu: Earthdata Authorization, Basic auth,
   çerezler, ortam/netrc bilgisi veya Referer taşınmaz. İkinci yanıtın
   da yönlendirmesi takip edilmez; yalnız 200 kabul edilir.

İmzalı URL yalnız bellekte kullanılır. İmza sorgusu, yönlendirme başlığı,
özel hata metni veya token çıktıya yazılmaz. Boyut sınırı, geçmiş SHA-256,
varsa sağlayıcı checksum'u, kısmi dosyayı koruma ve native girdi bağı
kontrolleri aynen kalır. Tek çift/191.244.528 bayt, bir işçi, 2 GB plan
önbelleği, 20 GB boş disk ve 900 saniyelik alt süreç sınırı değişmedi.

## Doğrulama ve yeni plan

**15 yeni yönlendirme vakası dahil 37 aktarım testi**, toplam **152 ilgili
test** geçti. Kabul edilen tek adımlı yönlendirme, ikinci oturumun kimlik
bilgisi/çerez taşımaması, yanlış bucket/yol/host, eksik imza, HTTP'ye dönüş,
giriş sayfası hedefi, eksik/çoklu CMR nesnesi ve ikinci yönlendirmenin reddi
denetlendi. Önceki bozuk/yarım dosya ve disk/süre testleri de geçti.
Dört Python dosyasında lint/format geçti.

Yeni çevrimdışı hazırlık yine eski kabul edilmiş `SNPP:2019014.0042`
çiftinde başlık okuyucuyu sınadı; bu yeni çekirdeğin indirme başarısı değildir.
**117 giriş/iki çıktı** hash kapanışı ve **22 donmuş üretim girdisi** korundu.
Yeni gerçek indirme için kullanıcının özel terminal girişi bekleniyor;
bu oturumda yeni ham dosya indirilmedi, bulut işi veya model başlatılmadı.

Yeni plan dizini:
`outputs/reports/dataset/observation_core_transfer_v1/20261015T001645Z_d3c51e9a/`.

`native_plan.json` SHA-256:
`3d2af7cbf5a73244cb4778dec5d2532039767b0ba41b1b9a2e33b718251a8c88`.
`readback.json` SHA-256:
`9444c56f9f97e8b71a9a91582f19322eabf3d775b8b2082962f6d5543908ad1f`.
`completion_readback.json` SHA-256:
`2b8fcb6c0bb882884b10289a63de6c0feafac660a53454d9c1e28a4553344ff1`.

Eski planın kimliği yeni kodla uyuşmaz; eski JSON'lar elle düzeltilmedi.
Yeniden deneme için bilgisayardaki proje klasöründe PowerShell:

```powershell
.\.venv\Scripts\python.exe scripts\firms\run_observation_core_pair.py --plan outputs\reports\dataset\observation_core_transfer_v1\20261015T001645Z_d3c51e9a\native_plan.json --run-one --prompt-login
```

Kimlik bilgileri bilinçli olarak saklanmadığı için yeniden gizli istemde
giriş gerekir. Sohbette yalnız genel PASS/hata satırı paylaşılır. Gerçek
indirme ve içerik kabulü tekrarın sonucuna bağlıdır; `unknown`, kapalı
negatif izni, boş hedefler, nihai birleştirme kapısı ve eğitim dışı veri
erişim yasağı korunur.
