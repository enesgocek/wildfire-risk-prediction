# Teslim planının ilerleme ve kesinti değerlendirmesi

22 Kasım 2026. [19 Kasım koşullu planı](DATASET_STAGE_TIMELINE_2026-11-19.md)
ile 21 Kasım'a kadar tamamlanan işler karşılaştırıldı. Araştırmacı,
haftalık GPT kotası ve her gün erişememesi nedeniyle sürekli aktif
çalışma varsayımının uygun olmadığını bildirdi. Aşağıdaki düzen bir
planlama önerisidir; yöntem/etiket kabulü, yeni eğitim veya nihai
birleştirme izni değildir. Eski tarihli plan değiştirilmedi.

## Yetişme değerlendirmesi

Planlama için kullanılan 1 Ocak 2027 tarihi hâlâ tahmini; resmî
kesin teslim tarihi olarak teyit edilmedi. 22 Kasım'dan bu tarihe
**40 takvim günü** var. Bitirme teslimi olasılığı korunuyor; ancak
güvenilir 24 saatlik risk veri seti ve doğrulanmış modelin bu tarihe
hazır olacağını mevcut kanıtla garanti etmek mümkün değil.

İki farklı durum birlikte görülmeli: teknik hazırlık belirgin
ilerledi; kritik bilimsel geçiş henüz açılmadı. Mevcut esas belirsizlik
yalnız çalışma kotası değil, hedef/etiket ile değerlendirme dayanağı.
Daha uzun çalışmak veya daha çok küçük model kurmak, eksik olay
kanıtını kendiliğinden sağlamaz. Aynı zamanda model/eğitim, uygun
değerlendirme, harita ve rapor da otomatik kolay kabul edilmeyecek.

19 Kasım planı zaten aktif çalışma, erişim ve bilimsel kabule
bağlıydı. Ancak aktif gün tahminini takvim gününe çevirmek için
kullanılabilecek güvenilir oturum kapasitesi ölçülmemişti. Kota ve
karar bekleyişi bundan sonra ayrı bağımlılık olarak gösterilecek;
her gün yeni prompt geldiği varsayılmayacak.

## Eski plana göre gerçekten ne kadar ilerledik

İlk planın birinci aşama inceleme/karar hedefi 26–29 Kasım'dı.
Bugün bu aralığa 4–7 gün var; karar tarihi henüz kaçırılmadı.
Bu durum bilimsel geçişin zamanında kabul edileceği anlamına gelmez.

| Planın ihtiyacı | 22 Kasım'da kayıtlı ilerleme | Henüz kapanmayan konu |
|---|---|---|
| Günlük karşılaştırma desteği | 44.082 anahtarlık yerel X/QA incelemesi; önceki değerler ve zamanlar denetlendi | Kaynak koşullu takvim, dört ilin bütün günlerini temsil eden nihai eğitim verisi değil |
| Günlük dinamiklerin ayrımı | Dokuz gün-farkı doğrusal model; aynı-hücre/ay uydu adayı çift AUC'si 0,585685–0,595230 | Gerçek yangın AP'si ve yakın günlerde güçlü ayrım gösterilmedi |
| Farklı kaynakta değerlendirme | Mersin için 2.383 günlük ayrı takvim ve dokuz sabit model; 2.329 çift | Kaynak anlamı/kapsamı belirsiz; yardımcı AUC 0,522542–0,540575, güçlü aktarım gösterilmedi |
| Tekrarlanabilirlik ve kesinti sonrası devam | Hash'li makbuzlar, aylık değişmez X checkpoint'leri, yerel deney kayıtları ve GitHub sürümleri | Bunlar bilimsel kabul veya kullanıcının nihai birleştirme onayı yerine geçmez |
| Planlı meteorolojik referans | Küçük FWI örneğinin seçimleri ve metadata okuyucusu hazır | Sağlayıcı dosyası henüz gelmedi; zaman/ızgara/veri uygunluğu açık |

44.082 ve 2.383 tablolarının ortak anahtarları var; sayılar toplanıp
tekil veri büyüklüğü yapılmadı. Teknik ilerleme, bilimsel hedefin
tamamlanma yüzdesine çevrilmedi. Deneylerin zayıf sonuç vermesi de
önemli bir bulgu: yüksek görünen kaynak ayrımını gerçek günlük yangın
becerisi sanarak ana üretime geçilmesi önlendi. Ancak bu bulgu tek
başına veri setini kabul ettirmez.

## Birinci aşamanın üç geçiş koşulu

| Koşul | Mevcut değerlendirme | Karar dosyasında yapılacak ayrım |
|---|---|---|
| Yeni orman/çalılık olayının pozitif kabulü | İlk zaman/hücre geçmişi ve örtü tanıları var; gerçek olay/konum/zaman belirsizliği sürüyor | Doğrulanmış bilgi, koşullu kaynak üyeliği ve çözülememiş nokta ayrı tutulacak |
| Uygulanabilir PU/gürültü dayanağı | Sınırlı yardımcı modeller çalıştı; hedefe aktarım varsayımları doğrulanmış değil | Varsayım veya kullanıcı tercihi bağımsız bilimsel kanıt diye yazılmayacak |
| Sonucu değerlendirebilecek referans | Farklı Mersin kaynağıyla takvim sınaması tamam; güçlü günlük aktarım yok | Yardımcı kaynak ölçütü, gerçek Y/AP ve kör testten ayrı raporlanacak |

Bu üç kapı açık. FWI, fiziksel meteorolojik referans olabilir;
olay kimliği veya bilinmeyen günlerin negatif etiketi sorununu çözmez.
FWI dosyası gelmese de 26–29 Kasım karar incelemesi mevcut kanıtla
hazırlanabilir; tek bir indirme nedeniyle aynı açıkların çevresinde
süresiz yeni denemeler eklenmeyecek.

## Kota ve aralara uygun uygulama düzeni

- Her küçük teknik adımdan sonra genel devam yanıtı beklenmeyecek.
  Yetkili bağımsız işler, kullanılabilen oturum içinde birlikte yürütülecek.
- İnsan kararı gerektiren konular, somut dosya/bulgu ve öneriyle
  mümkün olduğunca birlikte sunulacak. Bilimsel kapsam/yöntem ve
  rapora bağlı nihai birleştirme kararları otomatik verilmeyecek.
- Bir iş bittiğinde makbuz ve güncel durum yazılacak. Uzun yerel X
  işleri aylık değişmez parçalarla, aynı girdi/kod kimliğiyle devam
  edebilecek. Başarısız/kısmi çıktı tamamlanmış sayılmayacak.
- Kota/erişim olmayan günlerde yeni analiz ve karar yapılacağını
  varsayan bir teslim hesabı kullanılmayacak. Başlatılmış yerel bir
  işin çalışması, bütün araştırmanın kendi başına ilerlemesi değildir.
- [Kısa devam kaydı](NEXT_SESSION.md), oturum başında yapılacak ilk
  işi ve tekrar çalıştırılmayacak tamamlanmış işleri gösterecek.
  Kota reseti veya gelecekte otomatik çalışma için görev kurulmadı.
- Yöntem, veri ve sonuç yazımı eldeki doğrulanmış kısımlardan paralel
  ilerletilebilir. Nihai başarı ifadeleri sonuç gelmeden yazılmayacak.

## Korunan karar tarihleri ve koşullu sonrası

| Hedef | Çıktı | Durma/yeniden planlama koşulu |
|---|---|---|
| 22–26 Kasım | Küçük FWI dosyası gelirse başlık/zaman uygunluğu; birinci aşamanın desteklenen/varsayılan/açık yönlerini içeren karar dosyası | Dosya/erişim yoksa açık durum korunur; aynı tür yardımcı modeller çoğaltılmaz |
| 26 Kasım ilk değerlendirme, 29 Kasım karar hedefi | Gerekçeli geçiş önerisi veya geçilemediğinin açık raporu ve araştırmacıya somut yöntem/kapsam seçenekleri | Takvim dolduğu için aşama başarılı kabul edilmez; araştırmacı kararı bekliyorsa onay varsayılmaz |
| Ancak kabul sonrası | Hedef/P-U model satırları, güncel parça denetimi, rapora bağlı onay ve incelenebilir paket | Eski 2–4 aktif gün tahmini garanti değil; kota, yeni kaynak ve büyük uyuşmazlıklar ayrıca süre ekler |
| Aralık ilk yarısı, önceki kapılar açılırsa | Temel modeller, uygun değerlendirme, hata analizi; dayanak varsa kalibrasyon | 2024 girdileri ve değerlendirme dayanağı hazır varsayılmaz; 2025 kapısı korunur |
| 17–23 Aralık hedefi | Desteklenen sonuçlarla harita/prototip, yöntem/sonuç metni ve sunum | Temel hedef, bilimsel iddia veya kapsam kendiliğinden değiştirilmez |
| 24–31 Aralık | Tekrarlanabilirlik, son düzeltme ve teslim payı | Bu sekiz gün önceden yeni araştırma işleriyle doldurulmaz |

Bu tarihler otomatik görev veya erişim garantisi değildir. Bir sonraki
aktif oturumda tarih kontrol edilir; karar hedefi geçmişse yeni küçük
bir iş eklemekten önce gecikme ve kritik açıklar açıklanır. Ay sonuna
kadar geçiş dayanağı oluşmazsa tam risk sistemi teslimi yüksek riskli
kalır; tarihleri sessizce ileri kaydırmak yerine araştırmacıyla açık
karar gerekir. Bu değerlendirme peşinen hedef değişikliği seçmez.

## Bugün yapılan kontrol ve sıradaki iş

22 Kasım'da üç mevcut temel makbuzun içerik hash'i kayıtlı kimlikle
karşılaştırıldı ve eşleşti. Bilimsel üretim/model yeniden çalıştırılmadı;
21 Kasım'ın 57 testi bugünün yeni test sonucu gibi sayılmadı.
FWI'nin hazırlanan giriş klasörü boş; araştırmacı henüz indirmediğini
ve giriş/indirme adımını yapacağını bildirdi. İlk edinim bağımlılığı bu.

Dosya geldiğinde ilk iş mevcut sınırlı NetCDF başlık okuyucusuyla
kimlik, boyut, zaman ve ızgara metadata'sını incelemek. Dosya
incelemesinin geçmesi otomatik olarak günlük FWI değeri kullanma,
yeni model veya nihai birleştirme izni olmayacak.

Kanıt: [X hazırlığı](SOURCE_CALENDAR_FEATURE_PREPARATION_2026-11-21.md),
[gün çiftleri](TEMPORAL_PAIRWISE_RESULTS_2026-11-21.md),
[farklı kaynak sonucu](CROSS_SOURCE_CALENDAR_RESULTS_2026-11-21.md),
[FWI edinim hazırlığı](FWI_REFERENCE_PILOT_2026-11-21.md).
