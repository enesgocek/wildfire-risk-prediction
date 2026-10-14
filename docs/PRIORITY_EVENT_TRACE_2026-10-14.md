# Öncelikli dokuz vakanın bağlantı ve kaynak incelemesi — 14 Ekim 2026

Durum: yerel otomatik kanıt incelemesi tamamlandı; fiziksel olay kimliği,
Type semantiği ve etiket kabulü açık. Kaynak, önceki
[karar duyarlılığı paketidir](EVENT_DECISION_PROTOCOL_2026-10-14.md).
Bu işlem bağımsız uzman veya danışman incelemesi olarak kaydedilmedi.

## Kapsam ve yöntem

Hedef günü değişen üç inceleme grubunun dokuz varyantı ele alındı. Toplam
246 senaryo-üye satırı, senaryo tekrarları çıkarılınca **100 farklı
tespit** içeriyor; bunlar 100 bağımsız yangın değildir. Kabul edilmiş
üyelikler değişmedi. Her varyantın üye kimlikleri hash ile, ilk/son zamanları
ve bütün eşzamanlı ilk hücreleri kaynak tabloyla kontrol edildi.

Kayıtlı mesafe/zaman kuralı yalnız bu dokuz kümenin kendi üyeleri üzerinde
yeniden sınandı: WGS84 jeodezik nokta merkezleri, en çok 500/1.000/2.000 m
ve senaryodaki 48/72 saat. Dokuzunun da iç grafı bağlı bulundu. Bu dar
kontrol bütün eğitim kataloğunun yeniden gruplanması veya atlanmış başka
üyelerin olmadığına ilişkin yeni bir küresel kabul değildir.

Her grubun bütün varyantlarında ortak olan tespitlerden zaman/kimlik
sırasıyla bir inceleme bağlantı noktası seçildi. Her eşzamanlı ilk tespit
için bu noktaya en az kenarlı yol çıkarıldı; eşit yollar kimlik sırasıyla
belirlendi. Bu nokta doğru ilk hücre olarak seçilmedi. Bir noktadan
oluşan yol da kaydedildi. Toplam **20 yol-düğüm satırı** ve **dokuz
ikili üyelik karşılaştırması** dosyadan geri okundu.

Graf yönsüzdür; yol yangının yayılma yönü veya fiziksel devamlılık kanıtı
değildir. Etiket denetiminde kullanılan sonraki tespitler model girdisi
veya tahmin anında bilinen olay durumu sayılmaz.

## Üç somut bulgu

| İnceleme grubu | Farklı tespit | Ölçülen bağlam | Açık değerlendirme |
|---|---:|---|---|
| `review_830c74851331775e` | 93 | 2019 Mayıs–Temmuz; üç varyantın toplam süreleri 912,63 / 1.031,90 / 1.236,22 saat | Uzun tekrarlı termal zincirin aynı olay mı, ayrı olaylar mı olduğu çözülmeli |
| `review_508c95a48652218a` | 5 | 27–29 Aralık 2023; 500/1.000/2.000 m kuralıyla ilk zaman/hücre değişiyor | Mekânsal zincir, önceki kaynak kayıtları ve dönem sonu bağlamı birlikte incelenmeli |
| `review_5feb9ec77ed469eb` | 2 | 29–30 Aralık 2023; iki sensörden tespitler arası 948,32 m / 24,52 saat | 500 m'de önceki noktanın seçilmiş kümeye bağlanmaması gün/hücreyi değiştiriyor; fiziksel olay birliği açık |

İlk grubun süreleri yaklaşık **38,03–51,51 gün** eder; gerçek bir yangının
bu kadar sürdüğü sonucu değildir. Kuraldaki 72 saat, **her kenarın** zaman
farkını sınırlar; toplam küme süresinin üst sınırı değildir. Geniş mesafe
varyantında 23 Mayıs'taki ilk nokta, ortak 1 Haziran noktasına dört kenarla
bağlanıyor; bu kenarların zaman farkları 36,00 / 49,05 / 47,38 / 71,88 saat.
Dolayısıyla kayıtlı gruplama hesabı açıklanabildi; bilimsel olay kimliği
bu hesapla doğrulanmış olmadı.

Beş tespitli Aralık grubunun 1.000 m varyantında seçilen yol, 28 Aralık
01:14 → 29 Aralık 00:56 → 28 Aralık 23:15 UTC biçimindedir. Son adım
zamanda geriye gider. Mesafeler 856,04 ve 433,33 m'dir. Bu yönsüz bağlantı
örneği, sonradan gelen bir noktanın önceki noktaları birleştirebildiğini
gösterir; gerçek zamanlı bir olay izleyicisinin doğrulandığı anlamına gelmez.

## Kaynak ve dönem istisnaları

Önceki eğitim kapsamlı `firms_candidates_static_proximity.csv` çıktısı
hash ile bağlandı; 100 tespit için koordinat/zaman/kimlik eşitliği kontrol
edildi. **98/100 tespit** için daha önceki bir Type=2 kaydı 1.000 m içinde
bulunuyor: 2019 grubunun 93 ve beş tespitli Aralık grubunun beş kaydı.
İki tespitli diğer grupta bu aralıkta kayıt bulunmuyor.

Bu amaçlı seçkideki oran genel veri için hata oranı değildir. Type=2
satırları bağımsız tesis sayısı değildir; yakınlık endüstriyel kökeni,
eşleşme yokluğu bitki yangınını kanıtlamaz. Üretim Type sürümünün teknik
teyidi hâlâ açık; NASA'dan yeni yanıt alınmış varsayılmadı. Hiçbir kayıt
bu yakınlığa veya tekrarına dayanarak otomatik elenmedi. Gelecekteki Type
kayıtları aynı tabloda ayrı kalır; bunlar tahmin girdisine dönüştürülmedi.

Her varyant için ilk zamandan senaryo boşluğu kadar önce ve son zamandan
aynı boşluk kadar sonraya uzanan **takvim bağlamı** oluşturuldu. Altı
Aralık varyantında bu aralık, ertelenmiş **31 Aralık 2023** nominal kaynak
gününü ve 2024 tarafını içeriyor. 2024 verisi açılmadı; yalnız zaman sınırı
hesaplandı. Bu işaret tam `(T,T+24h]` gözlem kapsamı değildir; eksik bir
nominal günün etkisini yaklaşık takvim karşılaştırmasıyla çözdüğü iddia
edilmez. Gözlem durumu `unknown`, negatif izin `false` kaldı.

## Karar ve sonraki işlem

Dokuz varyantın hesabındaki gün değişimi artık bağlantı düzeyinde
açıklanıyor. Buna rağmen bu varyantlar için otomatik pozitif, negatif,
tek olay veya endüstriyel kaynak kararı verilmedi. Mevcut 53 vaka ve 400
tabakalı hücre-günlük insan inceleme formları tamamlanmış sayılmadı.

Araştırma önerisi: uzun tekrarlı zincirler ve dönem sonu bağlamı eksik
örnekler, kabul edilmiş eğitim hedeflerine zorla katılmadan ayrı belirsizlik
grubunda değerlendirilmelidir. Bunun nihai dışlama, bölme veya olay devamı
kuralına dönüşmesi için bağımsız olay/yer kullanımı kanıtı ve sürümlü
araştırmacı/danışman değerlendirmesi gerekir. Bu rapor o kararı onaylamaz.
Önceki karar protokolünün altı kabul başlığı açık kalır.

Sıradaki teknik çalışma, 400 tabakalı hücre-günlük pilotta hedef pencere
hizalamasını, eksik kaynak ve gözlem tanılarının sınırlarını inceleyerek
negatif etiket politikasının hangi kanıtlarla gerekçelendirilebileceğini
ölçmektir. Dokuz vakanın belirsizliği bu ayrı hazırlığı engellemez.

## Doğrulama ve çıktı

Komut: `.venv/Scripts/python.exe scripts/quality/trace_priority_event_cases.py`.
Ağ engelli yerel işlem, yeni bulut işi yok. 57 ilgili test geçti; son
koşuda kullanımdan kalkma uyarıları hata olarak ele alındı. Üç kod dosyası
lint/format kontrolünden geçti. Testler uzun toplam süre/kısa kenar,
çoklu ilk nokta, ortak bağlantı noktası bulunmaması, kopuk graf, boş eşleşme
mesafesi, sıfır kenarlı yol, kaynak bozulması ve kapalı hedefi kapsar.

Kabul edilen final dizini:
`outputs/reports/dataset/priority_trace_v1/20261014T173742Z_1aef9e5e/`.
Önceki aynı sürüm dizinleri geliştirme çıktısıdır; bu finalin yerine kullanılmaz.

- `case_trace_summary.csv`: dokuz varyantın kenar, süre ve kaynak bağlamı.
- `first_to_anchor_paths.csv`: bütün ilk noktalar için bağlantı yolları.
- `pairwise_membership_comparison.csv`: ortak ve ayrılan tespit kimliği sayıları.
- `detection_source_context.csv`: 100 farklı tespit ve ayrı kaynak tanıları.
- `case_timelines.png`: görsel olarak kontrol edilmiş üç panel; turuncu ilk
  tespit, mavi mevcut üyeler. Yangın yayılım haritası değildir.
- `readback.json` SHA-256:
  `4a09cc30034d94cf6e94b5436543e31e4c48416f262268d8906beace0940be74`.
- `completion_readback.json` SHA-256:
  `6c2531204a0bcfbc3cb93359e05f681f427ca3cb4ed15dfd25294ce71507c4ba`.

Beş çıktı ve 34 giriş kapanış kontrolünden geçti; önceki üç karar çıktısı
ve 22 donmuş bulut girdisi aynı hash'te. Kaynak/geolocation paketleri ve
mevcut etiket kapısı değişmedi. 2024/2025 erişimi, model eğitimi, 0/1
etiket ve nihai olay kimliği kabulü yok; `model_ready=false` korunur.
