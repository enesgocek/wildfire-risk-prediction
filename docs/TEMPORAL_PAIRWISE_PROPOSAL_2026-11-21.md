# Günlük değişimi öğrenmek için somut yöntem seçenekleri

21 Kasım 2026. **Araştırmacı kararı için hazırlık; yeni model
eğitilmedi.** [Sabit-model takvim kontrolü](SOURCE_CALENDAR_DIAGNOSTIC_2026-11-21.md)
aynı yerde günlük kaynak-bağlamı ayrımının sınırlı kaldığını gösterdi.
Mevcut RF'ler genişletilmiş takvim veya aynı-yer gün çiftleriyle
eğitilmiş değildi. Bu nedenle bir sonraki denemede öğrenme
hedefinin günlük değişime uyarlanması öneriliyor. Yangın riski
amacından vazgeçilmiyor; bu denemenin yardımcı kaynağı ile gerçek
yangın arasındaki açık varsayımlar da başarı gibi sunulmayacak.

## Hazır veri ve zaman kontrolü

44.082 özgün X inceleme satırı aynı; özgün U yeniden örneklenmedi.
Geniş takvimde 2.306 anahtarda gözlenen tespit grafik bağlamı var.
En geniş incelenen 2 km/72 saat grafiğinde, 2018–2021 ve 2022
takvim rolleri arasında ortak grafik bloğu **0**. Önceki modellerin
fit anahtarlarıyla yeni 2022 bağlamı arasında da dokuz ayarda **0**.
Bu sonuç gerçek fiziksel olay bağımsızlığı veya gözlenmeyen
bağlantıların yokluğu değildir; sonraki yöntem farklı bir grafik
kullanırsa kontrol yenilenir. Yıl sınırına taşan hedef günler kapalı.

Yalnız 11 hava ve dört geçmiş bitki örtüsü alanı tam olan tarihler
sayılırsa dokuz ayarda olası destek:

| İnceleme rolü | Aday-bağlamı satırı | Diğer tarih satırı | Aynı hücre–yıl–ay çifti | İki bağlamı bulunan grup |
|---|---:|---:|---:|---:|
| 2018–2021 | 974–1.356 | 34.020–34.402 | 28.081–39.014 | 938–1.160 |
| 2022 | 201–225 | 5.757–5.781 | 5.733–6.406 | 189–200 |

Diğer tarih satır sayısı, karşı aday bulunmayan grupları da kapsar;
hepsi çift oluşturmaz. Bunlar gerçek pozitif/negatif veya bağımsız
olay sayıları değil. Eksik satırlar ana tablodan silinmez; sadece bu
olası tam-girdi denemesinin dışında sayılır. Eksiklik seçiminin
sonuca etkisi ayrıca sınırlama olarak raporlanır. Henüz yeni çift
matrisi veya eğitim göstergesi üretilmedi.

Zaman/destek makbuzu, `outputs/reports/dataset/` altında:
`source_calendar_temporal_split_audit_v1/20261121T173542Z_11d5b339/readback.json`,
SHA-256 `7634d30483c7e6bc5dcb3c7315631242f7109001776afc244bdfdced86bd7920`.
İlk denetim tekrarlanan tek-satır erişimi nedeniyle uzadı ve sonuç
makbuzu üretmeden durduruldu. Özgün üretici
`interrupted_lookup_attempt/producer.py` olarak korundu; tam-girdi
maskesi bir kez hesaplanarak aynı sayım yeni koşuda tamamlandı.
Seçim/eksiklik/rol ve mutasyon davranışı için bir test geçti.
Kaynak X, metadata, grafik ve önceki sonuçlar değiştirilmedi.

## A — Aynı yerdeki günleri doğrudan karşılaştıran doğrusal pilot

Önerilen yön A'dır. Örneğin aynı hücrenin aynı Temmuz ayındaki
aday-bağlamlı bir günü ve diğer bir günü için, yalnız geçmişten
erişilen hava/bitki örtüsü vektörlerinin farkı öğrenilir. Yer
kimliği, statik örtü, koordinat ve takvim metadata'sı model girdisi
olmaz. Amaç aday-bağlamlı günün daha yüksek puan alıp almadığıdır;
diğer güne gerçek yangın yok etiketi yazılmaz.

Somut sınır: dokuz mevcut gruplama ayarının her birinde bir küçük
doğrusal model; en fazla dokuz yeni fit, yerelde toplam 15 dakika,
bulut yok. 2018–2021'deki tam 15 alanlı benzersiz satırlardan
yalnız fit ölçeklemesi hesaplanır. Aynı hücre–yıl–ay çiftlerinin
ölçekli farkı ve ters işaretlisi, yardımcı sıralama yönünü öğrenmek
için birlikte kullanılır. Sabit L2 lojistik kayıp, C=1, sabit terim
yok, en fazla 1.000 iterasyon ve seed=20261121 öneriliyor.
Hiperparametre/ayar araması ve sonuçtan sonra senaryo seçimi yok.
Çiftler eşit ağırlıklı; bir tarihin birden fazla çiftte bulunması
etkin örneklem büyüklüğü sayılmayacak.

2022'de tam 15 alanlı aynı çiftler üzerinde, sabit mevcut RF'ler ve
yeni doğrusal skor karşılaştırılır. Tam örnek anahtarları ve eksik
dışında kalan sayımlar ayrı korunur. Bu karşılaştırma hem öğrenme
örneklemini hem model ailesini değiştirdiği için olası fark yalnız
"çift kaybının nedensel kazancı" diye sunulmaz. 2022 artık keşif
yılıdır; değişken/ayar seçimi veya kör final testi yapılmaz.

Doğrusal skor, yalnız göreli günlük kaynak-bağlamı puanıdır.
Hücreler arası taban yangın riskini, yüzde olasılığı veya renk
eşiklerini kendiliğinden vermez. Kayıp yönündeki yardımcı 0/1
kodları gerçek Y veya kabul edilmiş L değildir. Yanlış pozitif ve
gözlenmeyen yangınların sıralamayı koruyan gürültü koşulları
doğrulanmış sayılmayacak. Bütün ayarlar ve başarısız/boş sonuçlar
raporlanır; yardımcı iyileşme ana yangın hedefinin kabulü olmaz.

## B — Gün çiftleri yerine günlük kayıtlarla dinamik RF

Alternatif, aynı 15 dinamik alanla geniş takvimde aday-bağlamı ve
diğer tarih kayıtlarını ayıran dokuz küçük RF kurmaktır. Eski model
ailesi korunur; yeni kayıt seçimi ve yardımcı gösterge yine ayrı
bir deney olur. Aynı hücre–ayda karşılaştırma yalnız değerlendirmede
uygulanır; öğrenme kaybı bu eşleştirmeyi doğrudan zorlamaz.
Aynı zaman, eksiklik, bulut, kapalı yıl ve gerçek etiket sınırları
B için de geçerlidir. İki yol aynı anda açılmış sayılmaz.

## Birincil yöntem dayanağı ve aktarım sınırı

Burges ve çalışma arkadaşlarının 2005 ICML makalesi, iki skorun
farkı üzerinden lojistik çift olasılığı ve çapraz-entropi kaybı
tanımlar. Resmî Microsoft Research bibliyografik kaydı ve tam PDF'nin
başlığı, yazarları ve yöntem bölümü kontrol edildi:
[resmî yayın kaydı](https://www.microsoft.com/en-us/research/publication/learning-to-rank-using-gradient-descent/),
[tam metin, bölüm 3–4](https://www.microsoft.com/en-us/research/wp-content/uploads/2005/08/icml_ranking.pdf).
DOI: `10.1145/1102351.1102363`. Yayınevi DOI tam sayfa erişimi
başarılı olmadığından ikinci bağımsız tam-metin doğrulaması iddiası yok.

Özgün çalışma web sıralaması ve RankNet sinir ağıdır; burada önerilen
doğrusal aynı-hücre/ay uyarlaması projeye ait öneridir. Makale
orman yangını, PU veri setimiz veya yanlış pozitif koşullarımız için
başarı kanıtı sağlamaz. Önceden incelenen
[Menon vd. 2015](https://proceedings.mlr.press/v37/menon15.html)
gürültülü sıralama sonuçları da kendi karışım/gürültü varsayımlarına
bağlıdır; bu varsayımlar yerel kaynakta doğrulanmış değildir.

Nihai yöntemin, etiketli veri setinin ve birleştirmenin kabulü açık.
Bu belge hazırlık ve gerekçeli seçenek sunumudur; yeni model,
karar makbuzu veya yeni iletişim yetkisi üretmez.
