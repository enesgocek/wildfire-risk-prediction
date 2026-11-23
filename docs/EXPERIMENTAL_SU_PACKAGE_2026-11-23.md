# İncelenebilir deneysel S/U paketi

23 Kasım 2026. Araştırmacı açık A seçimiyle ana 24 saatlik hedefi
araştırma sorusu olarak koruyup mevcut verilerden incelenebilir
deneysel paket hazırlanmasını istedi. **Paket ve bağımsız veri/arşiv
denetimi tamam; gerçek tarayıcı ekranının kullanıcı kontrolü bekleniyor.**
Ana yöntem bilimsel kabulü, yeni eğitim ve nihai etiketli veri
birleştirmesi yapılmadı.

## Paketi açma ve kapsam

Yerel dizin:
`outputs/reports/dataset/experimental_SU_inspection_v2/20261123T102954Z_6d6e52c1/`

`inceleme.html` tarayıcıda açılır; `review_data.js` aynı klasörde
kalmalı. Taşımak için `deneysel_SU_inceleme.zip` bütün dosyaları
içerir; yaklaşık 15,9 MB (15.924.436 bayt). Arşiv bir klasöre
açılıp HTML dosyası oradan çalıştırılmalı.

| İçerik | Sayı |
|---|---:|
| 2018–2022 kaynak koşullu hücre-gün | 44.082 |
| Farklı mevcut 5 km hücre | 822 |
| Özellik | 27 |
| 27 özelliği tam satır | 41.358 |
| En az bir özelliği eksik satır | 2.724 |
| En az bir ayarda eski aday önerisi bulunan anahtar | 1.670 |
| Ayara göre öneri üyeliği değişen anahtar | 412 |
| Eski 2018–2021 pilot rolü | 37.509 |
| Eski 2022 inceleme rolü | 6.573 |

Bu, kaynak adaylarının hücre/ay çevresindeki mevcut takvimdir;
bütün 2.889 hücre için tam panel veya temsili nüfus örneklemi değil.
2023–2025 bilimsel değerleri pakete alınmadı. Önceki rastgele U
örnekleminden yalnız 19 anahtar burada bulunuyor; eski örnekleme
ağırlıkları yeni takvime taşınmadı, yeni ağırlık üretilmedi.

## S ve U nasıl okunmalı?

**S**, seçili ayarda zaten var olan aday üyelik önerisinin bağlamıdır.
Gerçek yangın Y=1 veya kabul edilmiş L değildir. **U**, bu ayarda
üyeliği atanmamış takvim kaydıdır; yangın yokluğu değildir. Varsayılan
görünüm dokuz ayardan en az birindeki öneriyi gösterir; bu bir üretim
ayarı seçimi veya genel S kabulü sayılmaz.

| Korunan ayar | Önceki öneri anahtarı |
|---|---:|
| d500m_t24h / t48h / t72h | 1.670 / 1.635 / 1.611 |
| d1000m_t24h / t48h / t72h | 1.356 / 1.340 / 1.319 |
| d2000m_t24h / t48h / t72h | 1.299 / 1.285 / 1.258 |

Örneğin aynı satır bir ayarda aday önerisi, başka ayarda atamasız
olabilir; ekranda her ayar ayrı görünür. Gerçek hedef ve kabul
edilmiş L boş, günlük gözlem `unknown`, negatif etiket izni `false`.
WF1538 kararı korunuyor; bu anahtar öneri grubuna geri alınmadı.
Belirsiz ilk hücreler özgün aday geçmişi dosyasında silinmeden duruyor.

## İçerik ve bağımsız denetim

- `features.csv`, `provenance.csv`, `original_review_roles.csv` ve
  `original_candidate_lineage.csv` önceki dosyaların birebir bayt
  kopyalarıdır; sayılar/eksikler değiştirilmedi.
- `inspection_memberships.csv` dokuz öneri bayrağı, eksik sayısı,
  önceki pilot rolü ve il alan kesişimini aynı anahtara bağlar.
  Yalnız inceleme metadatasıdır; nihai etiketli birleştirme değil.
- `feature_dictionary.json` birim ve anlamları; `README.txt`
  kullanım/sınırlamaları açıklar. Web değerleri yalnız görüntüleme
  için yuvarlanır; tam hassasiyet kaynak CSV'de kalır.

Ayrı okuyucu 44.082 anahtarın ve 27 alanın görüntüleme verisiyle
eşleşmesini, 396.738 senaryo bayrağını, eksik sayılarını ve boş
hedefleri kontrol etti. Altı kaynak/zaman alanında kayıtlı politika
kesiminden sonraya taşan değer 0. Bu içerik penceresi kontrolüdür;
gerçek tarihsel erişim/yayımlanma saati doğrulaması değildir.

İlk audit'te varsayılan tarih ayrıştırma, kesirli/kesirsiz saniyeleri
aynı sütunda görünce iki bitki örtüsü alanında 84'er geçerli ISO
zamanını eksik ayrıştırdı ve durdu. Kaynaklar değiştirilmedi; açık
`ISO8601` ayrıştırma ve bozuk metin reddi regresyon kontrolüyle audit
ayrı tamamlandı. Bu durum kaynak zamanı hatası olarak sunulmadı.

ZIP CRC kontrolü, dosya envanteri ve her arşiv üyesinin yerel
dosyayla tam bayt eşitliği geçti. Beş yeni davranış testi dahil
son birleşik koşuda **33 ilgili test** geçti; dört yeni Python dosyası
kod/biçim kontrolünden geçti. Önceki FWI'nin 39 testi bu koşuya
eklenerek güncel toplam gibi raporlanmadı.

## Ekran kontrolü: kullanıcıda kalan tek doğrulama

Tarayıcı aracı `file://` protokolünü güvenlik politikasıyla reddetti.
Başka yüzey veya dolaylı yürütmeyle bu engel aşılmadı. Sayfanın gerçek
ekranda çalıştığı otomatik olarak gözlenmiş sayılmıyor; aşağıdaki
sayılar bağımsız veri hesabından geliyor:

1. İlk açılış: **44.082** satır, 1.670 aday bağlamı, 2.724 eksik
   özellikli satır, 822 hücre.
2. “Yıl: 2022”: **6.573** satır.
3. Buna “İnceleme grubu: S” eklenince: **242** satır (ayar: tümü).
4. Bir satır seçince 27 özellik ve dokuz ayrı öneri durumu açılmalı.

Bu yalnız kullanılabilirlik kontrolüdür; araştırmacıdan yangın etiketi,
bilimsel geçiş veya nihai veri seti onayı istenmiyor.

## İzlenebilirlik ve bundan sonrası

- Paket makbuzu: `experimental_SU_inspection_v2/20261123T102954Z_6d6e52c1/readback.json`;
  SHA-256 `86270dea5d9d12a1764ead780dcfa79166bed60a0977bf712e3df497d84bc366`.
- ZIP SHA-256: `13a90a265c3b17906b9ac8bb16e7210b4190368678a3698091a719bfd20bf7a4`.
- Ayrı denetim: `experimental_SU_inspection_audit_v2/20261123T103325Z_7ab004e5/readback.json`;
  SHA-256 `85fb7ac20f5d3e0564fe2ec66a5e4801f469d5c860cd5933b6a17e5be6c74356`.

Makbuzlar `outputs/reports/dataset/` altında. Bilimsel ana yöntemin
üç geçiş konusu açık. Araştırmacı seçimi, deneysel veri hazırlığına
izin verdi; koşullu kaynak bağlamını doğrulanmış yangın hedefi yapmadı.
Yeni model eğitimine veya nihai birleştirmeye ayrıca geçilmedi.
Önce ekran incelemesinin sonucu kaydedilecek; ardından deney kapsamı
bu paket ve açık iddia sınırlarıyla somutlaştırılabilir.
