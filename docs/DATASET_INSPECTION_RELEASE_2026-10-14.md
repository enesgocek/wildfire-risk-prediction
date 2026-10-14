# Eğitim verisinin denetlenmiş inceleme sürümü — 14 Ekim 2026

Durum: tam özellik/gözlem takvimi yeniden doğrulandı; inceleme teslimi ve
hash kapanışı tamamlandı. Etiketli/model eğitimine hazır sürüm değildir.

## Araştırmacının kararı ve teslim kapsamı

Araştırmacı, ana 24 saatlik yeni olay hedefinin korunmasını ve denetlenmiş
inceleme sürümünün hazırlanmasını seçti. Daha sonraki açıklamasında süre
hedefi için bilimsel kabul koşullarının gevşetilmemesini istedi. Ayrı bir
katalog-var/yok hedefi seçilmedi; mevcut unknown/kapalı etiket koşulları
korunur. Karar `configs/inspection_release_v1.json` içinde kayıtlıdır.
Bu karar nihai etiketli birleştirme onayı değildir.

Mevcut aday takvim 2018–2023, 72 ay, 2.191 gün, 2.899 hücre ve
6.351.709 hücre-gündür. Meteoroloji 11, arazi örtüsü/topografya 12,
bitki örtüsü dört olmak üzere **27 aday özellik** vardır. Eğitim özellikleri
daha önce hazırlanmıştır; bu iş yeniden ham üretim veya model eğitimi değildir.

İnceleme teslimi bütün günlük aday parçalara hash bağlı bir dizin sağlar.
Günlük feature ve provenance tabloları korunur; aynı veriler büyük tek bir
dosyaya kopyalanmaz. 400 sabit pilot örneği 27 özellikle ayrı, sınırlı bir
önizleme olarak bağlanır. Bu işlem 6,35 milyon satırın etiketlerle nihai
birleştirilmesi değildir. Örnekleme ağırlığı, su kapsamı ve kaynak/zaman
bayrakları korunur; boş hedefler sıfıra çevrilmez.

Özgün takvimdeki 10 harita-su hücresi parça dizininden silinmez. Önceden
kabul edilen su kapsamı kuralı sonraki kullanımda ayrıca uygulanmalıdır.
400 örnek eşit olasılıklı değildir; ham sayılar popülasyon oranı değildir.
2024 doğrulama ve 2025 final test bu teslimin parçası değildir.

## 181 arka plan adayındaki yeni kontrol

[Önceki protokol karşılaştırmasındaki](LABEL_PROTOCOL_REVIEW_2026-10-14.md)
181 arka plan adayı, gözlenen termal merkezi ve katalog ilk aday eşleşmesi
olmayan; kaynak paketleri mevcut ve nominal kara merkezi desteği bulunan
amaçlı alt kümedir. Bütün 400 örneğin tabaka/ağırlık denetimi seçimden önce
korundu. Komşu kaynak günlerinden kaydedilen taramalar yeniden okundu;
pencere sınıfları, kara merkezi sayıları, zarf birleşimleri ve en uzun
boşluk önceki sonuçla karşılaştırıldı. Eksik kaynak ve sınır vakaları
arka plan kategorisine taşınmadı.

| Kabul edilmemiş örnek tarama koşulu | Kalan ham örnek | Bunlarda kara/bulut alan birleşimi çakışması |
|---|---:|---:|
| Nominal kara alan payı en az 0,80 | 170 | 105 |
| Nominal kara alan payı en az 0,90 | 167 | 102 |
| En az 0,90 alan ve iki farklı kara destekli kaynak granülü | 162 | 97 |
| En az 0,90 alan, iki sensör ve en çok 12 saat zarf boşluğu | 132 | 70 |

Koşullar örnek ölçü kesimleridir; bilimsel eşik veya negatif politika
seçilmedi. Kaynak granülü sayısı, bağımsız geçiş veya tüm hücreyi
gözlemleme sayısı değildir. 181 örneğin 163'ünde iki, 18'inde bir sensörün
kara merkezi vardır. 115 örnekte nominal kara/bulut alan birleşimleri
çakışır; bu farklı geçişlerdeki alanların çakışması olabilir, otomatik
veri hatası değildir. Alan tanıları nominal gün içindir; komşu günlerle
tarama zarfı hesabı aynı alan geometrisini pencereye yeniden kırpmaz.

Kara merkezli tarama zarfları arasındaki en uzun boşluklar yaklaşık
10,64–23,70 saattir. Bunlar gerçek yangının gözden kaçtığı süre veya
uydunun sürekli gözlem süresi değildir. Bu ölçülerden, bir merkez veya
alan kesimini geçen bütün günlerin fiziksel yangınsızlığı çıkarılamaz.

NASA, geçişler arasında başlayan/biten yangınlar ve bulut/duman/örtü
nedeniyle tespit kaçabileceğini belirtir. Bu resmî açıklama proje için
belirli bir alan veya saat eşiğini doğrulamaz.
[NASA FIRMS notları; 14 Ekim'de yeniden okundu](https://firms.modaps.eosdis.nasa.gov/alerts/notes.php).
Mevcut çıkarım: sıfır etiketin ne anlama geldiği ve hangi gözlem desteğiyle
kabul edileceği sürümlü bir protokole bağlanmalıdır. Mutlak hatasızlık
iddiası yerine gerekçe, belirsizlik ve sınama kapsamı kaydedilecektir.

## Parça kontrolleri ve kabul ayrımı

| Parça | Teknik kontrol | Bilimsel kabulün sınırı |
|---|---|---|
| Meteoroloji | Günlük anahtar/şema, kaynak ve parça hash'leri, geçmiş pencere ve NaN sayımı | ERA5-Land retrospektiftir; gerçek zaman erişimi iddiası yok |
| Arazi/örtü | Sabit grid, kaynak kimliği ve özellik şeması | Tam su kararı mevcut; nihai habitat kapsamı ayrıca gerekçelendirilmeli |
| Bitki örtüsü | 30/60 günlük ayrı sütunlar, kaynak/QA/takvim ve eksikler | Eski görüntü, destek alanı ve modelde eksik değer politikası ayrı |
| Gözlem | 72 aylık CSV'nin güncel hash/anahtar/takvim ve eksiklik geri okuması | unknown korunur; hedef penceresindeki tanılar model girdisi değildir |
| Hedef | Boş hedefin korunması, açık bilimsel engellerin kaydı | 0/1 kabulü ve nihai hedef parçası henüz yok |

`parts_preflight.json` teknik kontroller ile bu açık kabul koşullarını
ayrı gösterir. Bu dosya `all_parts_final_review_passed` veya bilimsel
protokol kabulü değildir; mevcut nihai birleştirme denetimi onu reddeder.
Kullanıcının istediği son kontrol ve açık onay, bilimsel protokol ile hedef
parçası hazır olduğunda güncel kimliklerle ayrıca yapılacaktır.

## İnsan gözüyle inceleme

Önce `candidate_inspection_preview_400.csv` ve `feature_dictionary.json`
açılabilir. İnceleme sırasında:

1. Bir satırın hücre/tarih anahtarını, sütun birimlerini ve 30/60 günlük
   bitki örtüsü ayrımını kontrol edin.
2. NaN ile ölçülmüş sıfırı ayırın; özellikle meteoroloji ve bitki örtüsü
   eksiklerini doldurmayın.
3. `water_scope_included`, `window_incomplete_packet_set` ve
   `window_boundary_scan_present` bayraklarını ayrı okuyun.
4. `target` boşluğunun bilinmeyen/kabul edilmemiş hedef olduğunu koruyun.
   Tablonun görünümü olay veya negatif etiket doğrulaması değildir.

İstenen insan incelemesi kullanılabilirlik, anlam ve açık kararların
anlaşılması içindir; milyonlarca kaydı gözle tek tek etiketlemek değildir.
[19 olay örneğinin üç somut tanığı](SENSITIVE_PILOT_TRACE_2026-10-14.md)
ilk gün/hücre kuralının sonuçlarını ayrıca gösterir.

## Kontrollü devam sırası

1. Gözlem ölçülerinin alan/geçiş/zaman anlamını açık protokole dönüştürmek;
   sınırlı kaynak örneklerinde yeterlilik ve kalan belirsizliği sınamak.
2. Olay/tekrar/ilk hücre kuralını duyarlılık ve referans kanıtıyla
   gerekçelendirmek; kaynak Type konusu, habitat ve dönem kenarlarını bağlamak.
3. Kabul edilen yeni protokolle hedef parçalarını üretmek; parça son
   kontrollerini araştırmacıya sunup açık onaydan sonra nihai birleştirmek.

Katalogdaki aday yokluğunu fiziksel yangın yokluğu olarak yeniden adlandırma,
bilinmeyeni sıfıra çevirme veya senaryoların uzlaşmasını bağımsız doğruluk
sayma yapılmadı. Kalite önceliği, açık gerekçeli ve tekrar üretilebilir
kararlarla ilerlemektir.

## Çalıştırma ve kapanış kaydı

Yeni betik: `scripts/quality/review_release_readiness.py`.
Önce `prepare_dataset.py audit --require-complete-calendar` ile güncel
tam aday denetimi alınır; yeni betiğe bu rapor ve SHA-256 verilir.
Betik bütün günlük parça baytlarını ve 72 gözlem tablosunu ayrıca doğrular;
sınırlı önizleme ve teslim dizini oluşturur. Ağ erişimi engellidir.

Tam özellik denetimi 14 Ekim **23:22 Türkiye**'de geçti:
`outputs/reports/dataset/candidate_audit_v1/20261014T202202Z_ba43b54a/readback.json`.
SHA-256 `7e20556fcdf4aa90e32ce98605ebe57f9d81f4c839a0a6cb2a946a1a9df0fa12`.
72 ay/6.351.709 aday satırı, kaynak/method kimlikleri, günlük anahtar,
şema, geçmiş pencere ve eksik değer denetimlerinden geçti.

Yeni teslim dizini:
`outputs/reports/dataset/release_readiness_v1/20261014T202658Z_0c89a9de/`.

- `full_candidate_parts_index.csv`: 2.191 günlük feature/provenance
  çiftinin yolları ve hash'leri; 6.351.709 aday satırına erişim dizini.
- `candidate_inspection_preview_400.csv`: 400 satır/40 sütun; 27 özellik,
  anahtarlar ve ayrı inceleme alanları. Bütün target alanları boş.
- `feature_dictionary.json` ve `README.md`: sütun anlamları ve okuma rehberi.
- `background_evidence.csv`, `hypothetical_screens.csv`, `background_screens.png`:
  181 arka plan örneği ve kabul edilmemiş dört tarama kesimi. Görsel kontrol edildi.
- `observation_fresh_audit.json`: 72 CSV/6.351.709 gözlem satırı yeniden
  okundu; iki kaynak gününün 5.798 eksik ürün satırı aynı kaldı.
- `parts_preflight.json`: beş parçanın teknik kontrol/bilimsel kabul ayrımı.

Dokuz teslim dosyası geri okundu; **9.772 girdi kimliği ve 22 donmuş
bulut girdisi** kapanışta aynı. Yeni 28 davranış testiyle birlikte
**119 ilgili test**, üç Python dosyasında lint/format geçti. Testler
satır kaybı/ekstra anahtar, holdout, eksik/sıfır ayrımı, örnekleme ağırlığı,
su bayrağı, bozuk kaynak sayımı, kabul edilmemiş alan/sensör kesimleri ve
kapalı nihai birleştirmeyi kapsar. Bu teknik başarılar insan veya bilimsel
etiket kabulü olarak sunulmaz. Eski üretim/kabul dosyaları değiştirilmedi.

Teslim `readback.json` SHA-256:
`f494acb939d84024d5399139ea4e0fc6e45327c45114dfca2e441a6218d612ef`.
Kapanış SHA-256:
`25f83533cfd8c8c55584484dd8d35840c409c94c71b03ffa18668054d7d5d37b`.
Ham veri ve teslim çıktıları yereldir; kod/araştırma kaydı dışında Git'e
gönderilmez. Etiket üretimi, model eğitimi, nihai birleştirme veya yeni
bulut işi yapılmadı. Eğitim dışı özellik/gözlem CSV'leri okunmadı;
çok dönemli eski kaynak raporları yalnız kayıtlı kimlikleriyle korundu.
