# Gözlem çekirdeğinin güncel katalog kontrolü — 15 Ekim 2026

Amaç, [genişletme planındaki](OBSERVATION_EXPANSION_2026-10-15.md) 156
hücre-günün gerektirdiği 292 yangın/konum çiftinin aynı dosya kimliği ve
sürümle güncel NASA kataloğunda bulunup bulunmadığını kontrol etmektir.
Bu çalışma ham alan/zaman pilotunun yürütülmesi veya etiket kabulü değildir.
Ana eğitim kapsamı 2018–2023/72 ay, açık kaynak günleri ve kapalı hedef
kuralları korunmuştur.

## Kapsam ve yöntem

Önceki kabul raporu ve kaynak/plan CSV'lerinin SHA-256 kimlikleri doğrulandı.
Yalnız `calendar_core` bağlantısındaki **584 dosya** seçildi: 12 hedef gün,
36 nominal kaynak günü, 292 çift. Öncelikli 48 zor vaka veya 400 örneğin
tamamı için yeni sorgu yapılmadı. Örnek seçimi değiştirilmedi.

`scripts/firms/check_observation_core_catalogue.py --fetch`, kamuya açık
CMR `granules.umm_json` adresini kullanır. Her sorgu tek koleksiyon ve
en çok 16 dosya içerir. Üretici kimliğinin uzantılı/uzantısız biçimleri
tam adla aranır; wildcard ve büyük/küçük harf esnetmesi kapalıdır. Tam
dosya adı, işleme tarihini de içerir; yalnız aynı sensör/zamandaki yeni
bir dosya sürümü eski sürümün yerine geçirilmez.

Yanıtın `CMR-Hits` sayısı, JSON sayısı, dönen kayıtların tamamı ve timeout
durumu kontrol edilir. Kesik yanıt veya ağ hatası sıfır kayıt sayılmaz.
Koleksiyon, üretici kimliği, ürün/sürüm, altı dakikalık nominal
zaman aralığı, metadata dosya boyutu ve dosya adıyla eşleşen NASA veri
bağlantısı karşılaştırılır. Aynı ada birden fazla kavram dönerse birincisi
seçilmez; belirsizlik açık kalır. Dönen kavram ve revizyon kimlikleri
ayrıca kaydedilir; geçmiş bir CMR revizyonuyla eşitlik iddia edilmez.

CMR'nin çoklu üretici kimliği ve UMM JSON davranışı
[resmî CMR API belgesiyle](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html)
kontrol edildi. Veri URL'leri yalnız metadata alanıdır; takip edilmez.
Kimlik doğrulama, `.env`, Earthdata parolası/tokenı veya bulut servisi
kullanılmaz. İki eşzamanlı işçi ve sorgu başına en çok üç sınırlı taşıma
denemesi vardır. Kaydedilen yanıt baytları ve makbuzları hash ile bağlıdır;
yalnız aynı kod/kapsamla açık `--resume` çağrısı kullanılabilir.

## Ölçülen sonuç

Sorgular **14 Ekim 2026 23:54:02–23:54:39 UTC** aralığında tamamlandı;
Türkiye'de tarih **15 Ekim**'dir. Zaman damgası her yanıt makbuzunda tutulur.

| Ürün | Dosya | Tam kimlik ve metadata eşleşmesi | Boyut kaynağı |
|---|---:|---:|---|
| NOAA-20 yangın `VJ114IMG` | 132 | 132 | İkili MB'den yuvarlanan metadata |
| NOAA-20 konum `VJ103IMG` | 132 | 132 | `SizeInBytes` |
| S-NPP yangın `VNP14IMG` | 160 | 160 | İkili MB'den yuvarlanan metadata |
| S-NPP konum `VNP03IMG` | 160 | 160 | `SizeInBytes` |
| **Toplam** | **584** | **584** | 292 doğrudan / 292 yuvarlanmış |

Bu tam ad/koleksiyon sorgularında eksik kayıt, çoklu kimlik veya metadata
çatışması çıkmadı. **38 sorgu/38 HTTP denemesi** ile **2.032.266 metadata
baytı** okundu. Önceki planın **53.517.820.515 ham kaynak baytı** bir
indirme gerçekleşmiş gibi raporlanmaz; bu oturumda ham indirme sıfırdır.

292 konum dosyasında boyut tam bayt alanından karşılaştırıldı. 292 yangın
dosyasında mevcut yöntemle ikili MB alanı bayta yuvarlandı; en fazla bir
bayt metadata yuvarlama toleransı kullanıldı. Bunlar uzaktaki ham baytların
bu oturumda ölçümü değildir. Konum kayıtlarının 292'si MD5 verir; geçmiş
kaynak envanteri SHA-256 içerdiği için bu iki algoritma doğrudan eşitlik
kanıtı sayılamaz. 292 yangın kaydında sağlayıcı checksum alanı yoktur.
**Ham dosya içeriği veya checksum bu kontrolde yeniden doğrulanmadı.**

292 konum dosyasının katalogdaki HTTP dağıtım adresi LAADS Earthdata Cloud,
292 yangın dosyasınınki LP DAAC Earthdata Cloud alanındadır. Ön sorguda
LAADS'nin cloud alan adı tanındıktan sonra yeni tam çalışma üretildi.
[NASA LAADS'nin resmî açıklaması](https://ladsweb.modaps.eosdis.nasa.gov/alerts-and-issues/199515)
bu dağıtım alanını doğrular; eski ağustos bakım duyurusu güncel kesinti
kanıtı olarak kullanılmadı. Önceki kabul edilmiş çıktılar ve dondurulmuş
bulut indirme kodu değiştirilmedi.

## Açık kalan kapılar

- Katalogdaki kayıt ve URL, kimlik doğrulamalı veri uç noktasına erişim
  veya başarılı indirme garantisi değildir. Bu uç noktalara istek atılmadı.
- Dosya içeriği, yangın ürününün gerçek konum `InputPointer` bağı ve
  sensör/yörünge/tarama kalitesi sınırlı ham pilotta yeniden doğrulanmalıdır.
- Bu 584 dosyanın sonucu, ertelenmiş iki günün kaynak sorununun çözümü
  veya bütün arşivin güncel erişilebilirlik kabulü değildir.
- 156 amaçlı vaka, popülasyon etiket hata oranını ölçen rastgele örneklem
  değildir. Gözlem yeterliliği, olay kabulü ve negatif etiket protokolü açıktır.
- `daily_observation_status=unknown`, `negative_label_permitted=false`,
  boş hedefler ve nihai birleştirme için son kontrol/onay kapısı korunur.
  Model veya 2024/2025 veri erişimi yoktur.

## Canlı ürün açısından yeni kaynak sürekliliği konusu

Kontrol sırasında görülen resmî duyuru ayrıca incelendi. NOAA'nın **1 Ekim
2026 tarihli** bildirimine göre S-NPP'nin kalan bilimsel veri dağıtımının
**2 Kasım 2026 13:00 UTC**'de sonlandırılması planlanıyor. NASA LAADS,
tarihsel S-NPP VIIRS koleksiyonlarının arşivde kalacağını belirtiyor ve
yeni veri için NOAA-20/21 ürünlerine geçiş öneriyor. Tarih değişebilir.
[NOAA bildirimi](https://www.ospo.noaa.gov/data/messages/2026/10/MSG_20261001_1828.html),
[NASA LAADS açıklaması](https://ladsweb.modaps.eosdis.nasa.gov/alerts-and-issues/199516).

Araştırma yorumu: bu bildirim mevcut 2018–2023 arşivini iptal etmez; canlı
risk uygulamasının S-NPP'ye kalıcı bağımlı kurulamayacağını gösterir.
NOAA-20/21 kapsama farkı ve sensörler arası uyum, operasyonel veri/özellik
sözleşmesine geçerken ölçülmelidir. Yeni bir sensör sessizce aynı veri
sayılmadı; bu oturumda veri seti veya model kapsamı değiştirilmedi. Kullanıcıya
bu konu bildirildi; şu anda kullanıcıdan işlem istenmiyor.

## Kabul kaydı ve sonraki iş

Çıktı dizini:
`outputs/reports/dataset/observation_core_catalogue_v1/20261014T235401Z_f3cdca96/`.

- `request_manifest.json`: önceki kapsam/kod/girdi kimlikleri.
- `responses/`: 38 özgün JSON yanıtı ve 38 sorgu/zaman/hash makbuzu.
- `source_metadata_checks.json`, `source_metadata_checks.csv`: 584
  dosyanın aynı sonuç kimlikleri ve açık erişim/içerik kontrol sınırları.
- `readback.json`, `completion_readback.json`: sayı/bayt/kapı ve kapanış.

**30 yeni davranış testi dahil 135 ilgili test** geçti; deprecation ve
future uyarıları hata sayıldı. Kesik/timeout yanıtı, sıfır kayıt, belirsiz
kimlik, yanlış koleksiyon/sürüm/zaman/boyut/URL/checksum, MD5–SHA ayrımı,
2025 erişim yasağı ve etiket kapısının korunması denetlendi. Üç Python
dosyasında lint/format geçti. **29 giriş ve 79 çıktı** hash kapanışı
doğrulandı; **22 donmuş üretim girdisi** korundu. Yeni VM/EE işi yoktur.

`readback.json` SHA-256:
`251bbc38b26344b23d959312f59d9d75d708437103b1056db2f860165d164b39`.
`completion_readback.json` SHA-256:
`12a1019a77849b41b8f474a497f5fa9b941a047636f47b21f4de2f3308136553`.

Sonraki iş, doğrulanan çekirdeği sınırlı ham kaynak önbelleğiyle yürütecek
disk/süre/checkpoint ve veri erişimi düzenini hazırlamak; küçük bir gerçek
çiftte içerik/lineage kontrolünü geçirmektir. 53,52 GB'ı topluca indirmek
veya yeni bulut oturumu başlatmak bu kontrolün otomatik sonucu değildir.
