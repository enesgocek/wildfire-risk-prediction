# Olay ve ilk hücre karar protokolü — 14 Ekim 2026

Durum: ölçülmüş senaryo duyarlılığı ve araştırmacı/danışman değerlendirmesine
açık kabul taslağı. Bir olay tanımı seçilmedi, insan incelemesi tamamlanmadı.
Bu kayıt, [kapalı etiket denetiminin](TARGET_ADMISSION_REVIEW_2026-10-10.md)
yerine geçmez. Eğitim 2018–2023; 2024/2025 bu işlemde okunmadı.

## Amaç ve yöntem

Önceki [53 amaçlı vaka](LABEL_EVIDENCE_REVIEW_2026-10-14.md) ve
[sınır karşılaştırması](PERIMETER_REFERENCE_REVIEW_2026-10-14.md), hangi
olay/ilk hücre kararlarının aday hedefi değiştirdiğini ölçmek için kullanıldı.
Ham uydu verisi yeniden işlenmedi ve yeni kümeleme yapılmadı.

Aynı `detection_id` içeren vaka çiftleri bağlandı. Bu bağın geçişli
bileşenleri yalnız **inceleme grubu** olarak tutuldu; fiziksel yangın veya
nihai `event_id` değildir. A–B ve B–C örtüşüyorsa A ve C doğrudan ortak
tespit taşımadan aynı grupta olabilir. Grup kimliği sıralı vaka kimliklerinin
hash'inden üretildi; satır sırası sonucu değiştirmez.

Her grubun mevcut varyantlarında ilk zaman, eşzamanlı bütün ilk hücreler ve
`(T,T+24h]` sözleşmesine göre aday T karşılaştırıldı. Gece yarısındaki ilk
tespit önceki T'ye aittir. Kaynak üyelik sayıları/zamanları/hücreleri tekrar
kontrol edildi. Aynı tespitin farklı senaryolarda koordinat, hücre, sensör
ve zamanı değişemez. Bu seçkide bulunmayan senaryo, aynı sonucu veriyor
sayılmadı. Amaçlı örneklemden genel hata oranı veya eşik üstünlüğü çıkarılmaz.

## Ölçülen sonuç

53 senaryo vakası ve 28 farklı üyelik örüntüsü **11 inceleme grubunda** toplandı.
Ölçüler bu seçkinin 2018–2023 kapsamına aittir; bağımsız yangın sayısı değildir.

| Karşılaştırma | En az iki farklı sonuç veren grup |
|---|---:|
| İlk tespit zamanı | 4 / 11 |
| İlk hücre kümesi | 3 / 11 |
| Aday hedef günü T | 3 / 11 |
| Aynı senaryoda birden çok seçilmiş küme içeren grup | 1 / 11 |

Son satır bölme/birleştirme bağlamına işaret eder; yanlış birleşme kararı
değildir. Satırlar örtüşür, toplanarak farklı grup sayısı bulunmaz.

Hedef günü değişen üç gruptaki **dokuz varyant** inceleme sırasının başına
alındı; kalan 44 varyant da korunur. Bu sıralama örnek dışlama değildir.

| İnceleme grubu | Varyant | İlk tespitler arasındaki aralık | Aday hedef günleri |
|---|---:|---:|---|
| `review_830c74851331775e` | 3 | 204,32 saat | 23/27 Mayıs ve 1 Haziran 2019 |
| `review_508c95a48652218a` | 3 | 23,68 saat | 27/28 Aralık 2023 |
| `review_5feb9ec77ed469eb` | 3 | 24,52 saat | 29/30 Aralık 2023 |

204,32 saat gerçek tutuşma belirsizliği veya hata ölçüsü değildir; örtüşen
seçilmiş kümelerin kaydedilmiş ilk zaman farkıdır. En erken zamanı doğru
saymak, zincirle eklenen eski bir tespiti yeni olayın başlangıcı yapabilir.
Aralık grupları kaynak eksikliği ve dönem kenarı bağlamıyla birlikte
incelenmelidir; bu işlemde otomatik dışlanmadılar.

Manavgat bağlamındaki başka bir grup 10 varyant/sekiz senaryo içerir;
ilk zaman aralığı 13,18 saat, üç farklı ilk hücre kümesi vardır. Ancak
aday gün aynıdır. Dolayısıyla yalnız gün tutarlılığı ilk hücreyi doğrulamaz.
Son sınırdan yaklaşık 174 m dışarıdaki nokta için tolerans uydurulmadı.

Sınır incelemesi yapılmış 21 varyantın 18'inde en az bir ilk nokta son
sınırların dışında kalır; bu 18 yanlış pozitif anlamına gelmez. Üç
varyantta tarihçe uyuşmayan ek coğrafi bağlantı bulunur. Diğer 32 varyantta
bu dar 2021 referans incelemesi yapılmamıştır; eşleşme yokluğu ölçülmüş
değildir. Her vakada bütün gerekçeler ayrı listede korunur.

## Kabul taslağı: gerekli kararlar

Makine okunur `decision_protocol_draft.json` altı başlığın tamamını
`unaccepted` olarak taşır. Her kabul kaydı politika sürümü, sorumlu inceleyici,
UTC inceleme zamanı, gerekçe, kanıt yolu/SHA-256 ve kaynak bağımlılık/sınırlarını
içermelidir. Bu alanların varlığı tek başına bilimsel kabul değildir.

| Başlık | Karar için gerekli kanıt ve önerilen işlem |
|---|---|
| Kaynak semantiği | Arşiv/Type sürüm anlamı ve istisnalar belgelenir; NASA teknik yanıtı alınmış varsayılmaz. |
| Olay tanımı | Öncelikli dokuz varyantta önceki tespit/zincir/ayrılma bağlamı incelenir; yeni olay ve devam eden tespit ayrımı gerekçelendirilir. Eşikler final teste göre seçilmez. |
| İlk hücre | Aynı ilk zamandaki bütün hücreler korunur; canonical hücre alfabetik diye hedef yapılmaz. Çok hücre ve konum belirsizliği için tutarlı, sürümlü kural gerekir. |
| Habitat | Bitki örtüsü kapsamı, tarım/su/sınır durumları ve harita referans yılı etkisi ayrı gerekçelendirilir. Eksik meteoroloji habitat dışılığı sayılmaz. |
| Negatif gözlem | Tam hedef penceresine hizalama ve yeterlilik ölçütü bilimsel olarak gerekçelendirilir. Ürün varlığı veya hotspot yokluğu yeterli değildir. Pozitif olay kanıtı da bütün negatifleri doğrulamaz. |
| Dönem kenarı | Sağdan dahil pencere, eksik önceki/sonraki bağlam ve ortak olayın splitler arası taşınması için dışlama/embargo kararı kaydedilir. |

Önerilen uygulama: önce dokuz öncelikli varyant ve Manavgat'taki bölme/ilk
hücre örneği kaynakla değerlendirilir; ardından 400 tabakalı hücre-günlük
pilotla gözlem/negatif politikasının uygulanabilirliği sınanır. Referansın
zaman/konum ve sensör bağımlılığı her kararla birlikte tutulur. EFFIS'in
ortak uydu kökeni bağımsız doğruluk yapılmaz; ham kaynak saatine UTC
varsayımı eklenmez. Son yanmış sınır, ilk gün yanmış alan veya predictor değildir.

Bütün milyonlarca satırın manuel etiketlenmesi önerilmiyor. İncelenmiş
örnekler üzerinde gerekçelendirilmiş kuralın sürümü dondurulup otomatik
uygulanması ve belirsizlerin ayrı tutulması hedefleniyor. İnceleme kapsamı
ve seçim yanlılığı raporlanmadan bu örnekler bütün veriyi doğrulamaz.
Şu an 453 insan formu hâlâ `not_reviewed`; bağımsız uzman kabulü yoktur.

## Doğrulama ve çıktı

Komut: `.venv/Scripts/python.exe scripts/quality/review_event_decisions.py`.
İşlem ağ bağlantısını engeller; kabul edilmiş kaynakları salt okunur açar.
Yeni üç çıktı CSV/JSON geri okumasından, 40 giriş hash kapanışından geçti;
önceki 11 inceleme çıktısı ve 22 donmuş bulut girdisi aynı kaldı.
51 ilgili test ve üç dosyada lint/format geçti. Kontroller geçişli örtüşme,
gece yarısı, ilk hücre bağları, satır sırası, eksik senaryo/referans,
bozuk üyelik/tarih/koordinat ve yanlış etiket/bağımsızlık kabulünü kapsar.

Kabul edilen yerel dizin:
`outputs/reports/dataset/event_decisions_v1/20261014T171606Z_3062f053/`.

- `case_decision_queue.csv`: 53 vaka; gerekçeler, grup, sıralama ve boş hedef.
- `overlap_families.csv`: 11 grubun değişim ölçüleri ve bütün vaka kimlikleri.
- `decision_protocol_draft.json`: açık altı karar ve kayıt koşulları.
- `readback.json` SHA-256:
  `d0210a017a57a3a5d327237e280ecfb4aae9dbc00e892b888759613c9a791a55`.
- `completion_readback.json` SHA-256:
  `2ea6726f73a9ebe2d156816cbddb1781687155e99fef9d9f562f50c5467f71a7`.

Önceki `171344` ve `171520` deneme dizinleri geliştirme çıktısıdır;
bu finalin kabul kaydı olarak kullanılmaz. Mevcut `target_admission.py`
değişmedi. Hiçbir 0/1 hedef, nihai olay kimliği, tampon mesafe veya senaryo
seçilmedi. `unknown`, iki etiket izninin `false` olması ve
`model_ready=false` korunur. Yeni bulut işi veya kaynak silme yapılmadı.
