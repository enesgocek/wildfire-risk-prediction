# Veri setini tamamlama planı ve teslim sınırı — 4 Kasım 2026

## Dürüst teslim durumu

2018–2023 için 72 aylık, 27 özellikli aday takvim hazırdır. Önceki
denetimde 6.351.709 aday hücre-gün vardır; bunlar nihai uygun eğitim
satırları değildir. Güncel kabul edilmiş 0/1 hedef parçası bulunmuyor.
Bu nedenle hazır özellik tablosu ile eğitime hazır veri seti aynı
teslim olarak sunulamaz. Sayılar önceki yerel raporlardan alınmıştır;
bu plan için bütün özellik dosyaları yeniden hesaplanmadı.

Kesin gün/saat tahmini için kabul edilmiş hedef protokolü, geçerli
örneklem büyüklüğü ve tam hedef üretiminin yerel süre ölçümü yoktur.
Bugün, yarın veya belirli sayıda gün içinde tamamlanma taahhüdü
vermek kanıtlanmış bir tahmin olmaz. Mevcut teknik yükün yanında
bilimsel karar/kanıt eksikleri bulunuyor; yalnız işlem beklemiyoruz.

## Kalan altı iş paketi

| Sıra | İş | Çıkış ölçütü | Güncel durum |
|---|---|---|---|
| 1 | Habitat: hücre ve aday yerel kapsamı | Sürümlü kabul/belirsizlik gerekçesi, harita yaşı/konum/tarım ayrımı, kapsam etkisi | 25 noktalık kanıt hazır; nihai kural açık |
| 2 | Yeni olay ile süren yangını ayırma | Gruplama/zaman/üyelik kuralı, çok ilk noktanın korunması ve duyarlı örnekler | Dokuz gruplama karşılaştırması hazır; üretim kuralı açık |
| 3 | Gözlem yeterliliği ve 0/1/belirsiz etiket | Hedefin anlamı, pozitif/negatif kanıt, gözlem boşluğu ve sınama gerekçesi | 156 amaçlı birimlik yöntem pilotu var; güvenilir negatif kabulü yok |
| 4 | Hedef parçası ve model satır politikaları | Kabul edilmiş kurallarla hedef üretimi; eksik özellik, dönem kenarı, olay/split sızıntısı ve anahtar kontrolü | Hazırlık kodu var; kabul edilmiş hedef tablosu yok |
| 5 | Beş parçanın taze son denetimi ve kullanıcı onayı | Meteoroloji, arazi/örtü, bitki örtüsü, gözlem ve hedef manifest/hash/şema/zaman sonuçları; rapora bağlı onay | Gerçek nihai birleştirme onayı yok |
| 6 | Nihai birleştirme ve incelenebilir teslim | Onaylanan aynı parçalarla üretim, geri okuma, veri sözlüğü, örnekler ve sınırlamalar | Önceki aşamalara bağlı |

Bunlar altı küçük komut değildir. Özellikle 1–3 yöntem ve kanıt
gerektirir; kod hazırlığı tek başına bu aşamaları kapatmaz. İşler
arasında bağımsız teknik hazırlık sürdürülebilir; kabul edilmiş
bilimsel koşullar atlanamaz. 2024 karşılaştırma verisinin tamamı ayrı
hazırlanmalıdır; bu eğitim teslimiyle hazır sayılmaz. 2025 kapalıdır.

## Habitat için şimdi somutlaştırılan öneri

Yeni incelemeyi sınırsız örnek/görsel üretimine dönüştürmeden mevcut
bulgular şu protokol önerisine taşınmalıdır. Bu metin henüz üretim
kabulü, oran eşiği veya örnek dışlama onayı değildir:

1. **İki ölçek korunur.** Risk hücresinin doğal orman/çalılık kapsamı
   olay bulunmasından bağımsız belirlenir. Adayın yerel örtüsü ayrıca
   değerlendirilir; bütün ilk noktalar ortak aday kimliğiyle saklanır.
2. **Üç kanıt durumu ayrı tutulur.** Doğal odunsu bağlamı destekleyen,
   yönetilen tarımsal bağlamı destekleyen ve karışık/çözülemeyen durumlar
   kayda alınır. Bunlar doğrudan pozitif/negatif hedef sınıfları değildir.
3. **Harita oranı tek başına kabul değildir.** C'de merkez/alan farkı,
   E'de mozaik sınıfının bilinmeyen iç oranı ve F'de meyvelik bağlamı
   bu gerekliliği gösterir. %50, tek merkez veya herhangi bir kesişim
   mevcut kanıtla otomatik üretim kuralı yapılmaz.
4. **Zaman kanıtı açık olmalıdır.** Tahmin öncesi görüntü ve kalite
   kaydı bağlanır; güncel doğal/yönetilen kullanımın yorumlanabilirliği
   ayrıca değerlendirilir. 2018 haritası sonraki yıllara otomatik
   taşınmaz; aynı yıl referansı da otomatik olay öncesi sayılmaz.
5. **Çözülemeyenler saklanır.** D/R03 gibi karışımlar ve kaynaklar arası
   çelişkiler inceleme havuzunda kalır. Tek bir meyvelik noktası bütün
   risk hücresini kapsam dışında bırakmaz; çok noktalı adayın diğer
   üyeleri silinmez. Doğrulanmamış yerel bağlam otomatik 0 olmaz.
6. **Kuralın etkisi ayrıca ölçülür.** Protokol seçildikten sonra gerçek
   aday havuzunda kaç birimin destekli/belirsiz kaldığı, yıl/il/örtü
   seçimi ve konum/tarih hassasiyeti raporlanır. Amaçlı 25 örnekten
   tüm veri setine doğruluk oranı çıkarılmaz.

C için ağaçlık, E/F için tarımsal, D/R03 için karışık ön bağlam önerisi
mevcut örneklerin inceleme sonucudur; bu altı koşulun hepsinin
sağlandığı veya bu noktaların nihai kabul edildiği anlamına gelmez.
Kapsamı etkileyen yeni kararlar somut etkileriyle araştırmacıya sunulur.

## Kritik engel: güvenilir negatif

FIRMS'te bir tespit bulunmaması tek başına gerçek yangın yokluğu
değildir. Hedef gözlenen yeni aktif yangın olayına ilişkin bir proxy
olarak açık tanımlanmalı; gözlem yeterliliği ve kaçırılmış olay
belirsizliği buna göre gerekçelendirilmelidir. Mevcut durum
`daily_observation_status=unknown`, `negative_label_permitted=false`.
Bunlar teslimi hızlandırmak için değiştirilmeyecek.

Kabul edilebilir gözlem/etiket protokolü desteklenemiyorsa ana hedef
için tam denetimli eğitim verisi hazır denemez. Katalogda tespit var/yok
gibi başka hedefe geçmek ayrı bilimsel karar gerektirir; kullanıcının
ana hedefi koruma kararı nedeniyle kendiliğinden uygulanmaz.
OGM veya NASA yanıtı tek zorunlu çözüm yolu değildir; bir yanıtın gelmesi
de otomatik bilimsel kabul sağlamaz. Yeni bulut işi yetkisi yoktur.

## Çalışma sırasının daraltılması

Sıradaki çalışmanın odağı bu habitat taslağındaki açık kabul koşulları
ve ardından gözlem/negatif protokolünün hangi kanıtla kapanabileceğidir.
Yeni görsel veya rapor yalnız bu açık koşullardan birini çözüyorsa
üretilmelidir. Model/arayüz iskeleti veya aynı sonucun tekrar raporu,
hazır etiketli veri setine ilerleme olarak sayılmayacaktır.

Yöntem ve kapsam netleştiğinde hedef üretimi sınırlı bir yerel çağrıda
ölçülür. Tam kapsam ve kaynak sınırlarıyla bu ölçüme dayanan koşullu
süre verilebilir. Nihai teslim öncesindeki taze denetim ve kullanıcı
onayı korunur. İlerleme, yeni dosya sayısıyla değil bu altı paketin
çıkış ölçütlerinin sağlanmasıyla raporlanır.

## Dayanaklar ve doğrulama sınırı

- [Güncel uydu–CORINE karşılaştırması](HABITAT_IMAGE_OVERLAY_2026-11-04.md).
- [Ortak 25 noktalık kanıt tablosu](HABITAT_EVIDENCE_MATRIX_2026-11-04.md).
- [Özellik ve kabul bağımlılıkları envanteri](PREPARATION_INVENTORY_2026-10-16.md).
- [Gözlem protokolü saat/kalite kanıtı](OBSERVATION_PROTOCOL_EVIDENCE_2026-10-15.md).
- [Araştırma aşamaları](research/RESEARCH_PLAN.md), [zaman/split sözleşmesi](PROJECT.md)
  ve nihai birleştirme öncesi kullanıcı onayı kuralı (`AGENTS.md`).

Bu adım kayıtların okunması ve yöntem önerisinin hazırlanmasıdır.
Yeni bilimsel hesaplama, güncel tüm veri hash denetimi, yöntem onayı,
eğitim, etiket veya nihai birleştirme yapılmadı. Yalnız belge değişikliği
için üretim/test/bulut kuyruğu başlatılmadı.
