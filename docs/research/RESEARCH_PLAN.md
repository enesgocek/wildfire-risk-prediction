# Araştırma çerçevesi

Kayıt tarihi: 9 Ekim 2026. Durum: bitirme çalışmasının araştırma çerçevesi;
4 Kasım 2026 güncellemesiyle TÜBİTAK başvurusu artık planlanmıyor.
Araştırma kabul ölçütleri ve akademik dürüstlük koşulları korunur;
önceki başvuru niyeti tarihsel kayıttır.

## Amaç ve kapsam

Antalya, Muğla, İzmir ve Mersin'de, uygun bitki örtüsüne sahip hücreler için
sonraki 24 saat içinde yeni bir olayın ilk aktif yangın tespitinin görülme
olasılığını araştırıyorum. Tahmin birimi mevcut 5 km projeksiyon grididir.
2.899 coğrafi hücrenin tamamının modellemeye uygunluğu henüz kesinleşmemiştir.

Bağlayıcı zaman, etiket ve veri ayrımı sözleşmesi [proje rehberindedir](../PROJECT.md).
Modelleme dönemi 2018–2023 eğitim, 2024 doğrulama, 2025 kapalı final testtir.
Gözlenen ilk tespit, gerçek tutuşma zamanının yerine kullanılan belirsiz bir göstergedir.

## Araştırma sorusu ve sınanacak iddialar

Ana soru: Uydu gözlem eksikliklerinin etiketleme sırasında dikkate alınması ve
meteoroloji, bitki örtüsü ve arazi bilgilerinin birlikte kullanılması, yeni olay
tahmininde yanlış alarm yükünü ve olasılık hatasını azaltabilir mi?

Bu soru bir sonuç veya özgünlük kanıtı değildir. Literatür karşılaştırması
ve yöntem/sonuç değerlendirmeleriyle bitirme araştırmasında sınanacaktır.

| Deney sorusu | Karşılaştırma | Önceden kaydedilecek değerlendirme |
|---|---|---|
| Ek özelliklerin katkısı var mı? | Meteoroloji temeli / bitki örtüsü ve arazi eklenen model | Aynı değerlendirme kayıtlarında PR-AUC ve kalibrasyon |
| Gözlem belirsizliği sonuçları etkiliyor mu? | Gerekçelendirilmiş gözlem politikaları ve bağımsız incelenmiş örnekler | Dahil edilen/dışlanan alan ve dönemler, seçim yanlılığı, etiket duyarlılığı |
| Uyarı listesi karar desteği sağlayabilir mi? | Geçmiş bölgesel/mevsimsel risk / öğrenilmiş model | Sabit günlük inceleme kapasitesinde olay yakalama ve yanlış alarm |

Belirsiz günlere otomatik sıfır atayan bir üretim veri seti oluşturulmaz. Gözlem
politikaları yalnız geçerli etiket tanımlarıyla karşılaştırılır. Hedef pencereye ait
uydu gözlem bilgisi etiket denetiminde kullanılabilir; tahmin anında mevcut değilse
model girdisi olamaz.

## Araştırma aşamaları ve kabul ölçütleri

22 Kasım plan değerlendirmesi: 26–29 Kasım ilk aşama karar hedefi
korundu; takvim ilerlemesi bilimsel kabul sayılmadı. Tamamlanan X ve
yardımcı modeller teknik ilerleme sağladı; üç geçiş kapısı açık.
Kota/erişim bekleyişi, toplu kararlar, checkpoint'ten devam ve
24–31 Aralık teslim payı ayrıca gösterildi. Yeni deney veya hedef/
kapsam değişikliği yok; tahmini 1 Ocak için garanti verilmedi.
[İlerleme ve kesinti paylı plan](../DELIVERY_PLAN_REVIEW_2026-11-22.md).

21 Kasım sonraki açık A seçimiyle ayrı Mersin takvimi tamamlandı:
2.383 X, 318 eski X/QA eşit, 79 tam kaynak günü, dokuz sabit model
ve 2.329 aynı-hücre/ay çifti. Yardımcı AUC 0,522542–0,540575;
yakın 1–3 gün çiftlerinde 0,450000–0,465909. Güçlü gerçek yangın
aktarımı kabul edilmedi. Daha fazla model aramak yerine plandaki
FWI/resmî tehlike referansının küçük metadata/edinim hazırlığı
yapıldı; standart FWI mevcut özetlerden uydurulmadı. Portal giriş/
lisans adımı kullanıcıda; FWI veya yeni etiket/fit henüz yok.
[Farklı kaynak sonucu](../CROSS_SOURCE_CALENDAR_RESULTS_2026-11-21.md) ·
[Referansın uygulanabilirlik adımı](../FWI_REFERENCE_PILOT_2026-11-21.md).

21 Kasım açık A yönü uygulandı: 15 dinamik alanda dokuz doğrusal
gün-çifti modeli tamamlandı. Yardımcı AUC 0,585685–0,595230,
yakın 1–3 gün çiftlerinde 0,520107–0,541187. Dokuz model,
ölçekleme, çift kimlikleri ve 36 ölçü ayrı doğrulandı. Bu sonuç
günlük gerçek yangın hedefini kabul ettirmiyor; daha çok ayar
deneyerek sonuç kovalanmıyor. Gözlenen devam tanısı tamamlandı,
source/gözlem ve gerçek hedef aktarımı belirsizliği korundu.
Mevcut Mersin kaynağında aynı-yer/ay desteği iki çift; ayrı
2.383 günlük takvim ve sabit-model sınaması için somut öneri hazır.
Yeni kaynak örneklemi yönü, yeni X/skor/fit veya final merge kabulü
olarak kaydedilmedi.
[Pilot sonucu](../TEMPORAL_PAIRWISE_RESULTS_2026-11-21.md) ·
[Farklı kaynak için kapsam](../CROSS_SOURCE_CALENDAR_PROPOSAL_2026-11-21.md).

21 Kasım sabit RF takvim tanısı tamamlandı: aynı hücre–yıl–ayda
tam model yardımcı çift AUC'si 0,568463–0,587403, statik model
0,5. İl kesitleri günlük ayrımın her yerde kurulmadığını gösteriyor.
27 eski model, 162 ayrı ölçü kontrolü; yeni fit yok. Özerk devam
talimatı yalnız somut tanı kapsamına bağlandı. Bu sonuç gerçek
yangın AP'si, risk rengi veya birinci aşama bilimsel kabulü değil.
Geniş takvimin zaman/grafik bağı tamamlandı: ortak gözlenen blok 0;
fiziksel olay bağımsızlığı doğrulanmadı. Tam günlük alanlarla olası
çift desteği sayıldı; aynı yerde günleri karşılaştıran doğrusal
kayıp için somut öneri hazır. Yeni öğrenme yönü henüz seçilmedi.
[Destek ve yöntem seçimi](../TEMPORAL_PAIRWISE_PROPOSAL_2026-11-21.md).
[Tanı ve açık kapı](../SOURCE_CALENDAR_DIAGNOSTIC_2026-11-21.md).

21 Kasım X hazırlığı kapandı: 44.082 anahtar, 41.358 tam/2.724
eksik; 1.689 önceki X/QA birebir aynı. Ayrı zaman/anahtar/ay ve
eksiklik kontrolü geçti. Bu, etiketli eğitim veri seti değil.
2022'nin 6.573 takvim gününde önceki sabit RF'lerin günlük davranışını
yeni fit yapmadan inceleme önerisi hazır; yeni puanlama/kaynak
göstergesi yönü soruldu. Gerçek Y/L, bilimsel kabul, kapalı yıllar
ve nihai birleştirme koşulları değişmedi.
[Tam hazırlık ve sonraki somut öneri](../SOURCE_CALENDAR_FEATURE_PREPARATION_2026-11-21.md#tamamlanan-x-ve-eksiklik-sonucu).

21 Kasım sonraki devam talimatı, ayrı kaynak koşullu takvim
kontrolünün yalnız yerel X/zaman/eksiklik hazırlığına bağlandı.
44.082 anahtar aylık değişmez checkpoint'lerle işleniyor; tamamlanmış
inceleme makbuzu henüz yok. Yeni U örneklemi, S/Y/L, eğitim veya
nihai birleştirme kabulü değil. İlk 24 ay/14.584 satır mühürlendi;
42 ilgili test geçti. Önceki öneri kaydı tarihsel olarak korunuyor.
[Devam ve kapsam kaydı](../SOURCE_CALENDAR_FEATURE_PREPARATION_2026-11-21.md).

21 Kasım devamında 20 Kasım'da tamamlanan 18 meteoroloji/statik RF
ve ayrı tanı doğrulandı; yeniden fit yapılmadı. Statik aday ayrımı
güçlü, aynı hücre+aynı ay desteği yalnız üç çift. Bu, günlük gerçek
yangın sıralaması kabulü değil. Kaynak koşullu ayrı takvim kontrolü
için 44.082 anahtarlık metadata kapsamı somutlaştırıldı; 42.393 ek
X incelemesi gerekir. Bu yeni yöntem yönü seçilmedi; özgün U,
gerçek Y, kapalı yıllar ve son birleştirme kapıları korunuyor.
[Somut sonuç ve sonraki yöntem kararı](../SATELLITE_PU_ABLATION_RESULTS_2026-11-21.md).

20 Kasım yeni yardımcı fit A kararıyla dokuz ayarda 27 küçük model
tamamlandı. Ayrı model/fit-istatistiği/çift hesabı ve bağlam tanısı
hazır; sonuçlar gerçek yangın AP'si veya risk olasılığı sayılmıyor.
Sıra benzerliği yüksek olsa da ilk 40 U listesi ayarlara duyarlı.
Statik bağlam ile günlük hava katkısını ayıracak 18 ek RF ablation
önerisi hazır; yeni karar olmadan çalıştırılmadı. Birinci aşama
kabulü, hedefe aktarım ve değerlendirme dayanağı açık kalıyor.
[Tamamlanan deney ve sonraki sınırlı soru](../SATELLITE_PU_PILOT_RESULTS_2026-11-20.md).

20 Kasım dört il uydu PU A hazırlığı yürütüldü: aynı fit kaynağında
dokuz kronolojik geçmiş/üç prefix ve iki haritada ilk merkez bağlamı
hazır. Geçmiş koruması fiziksel yeni yangın kabulü değil. Sonraki A
kararıyla 2017 ana/2018 yardımcı örtü bağlamı ve 1.670 olası öneri
hazırlandı; özgün 2.048 U ile 3.718 X anahtarı geri okundu. Dokuz
ayarda aynı 1.648/400 U, 2018–2021 fit / 2022 tanı ve en çok 27 sabit
yardımcı model için plan hazır; yeni fit kararı bekleniyor. Ana yöntem,
gerçek Y, kapalı 2023–2025 ve son birleştirme kapıları değişmedi.
[Uygulanan hazırlık ve açık sınır](../SATELLITE_PU_PROTOCOL_PREPARATION_2026-11-20.md).

20 Kasım ürün yönü sonrası hazırlık: özgün dört il U örnekleminin
2.048 anahtarında özellik/provenance hazır; 374 kaynak hipoteziyle
2.422 anahtarlık sınırlı inceleme paketi üretildi. Y'ler boş, gerçek
model verisi veya son birleştirme değil. Kalibre yüzde istemeyen
sıralama aritmetiği ayrı sentetik testlerle hazırlandı; ana AP ve
gerçek hedef kabulü korunuyor. Asistanın otomatik tarayıcı kontrolü
tamamlanmadı; sonraki araştırmacı bildirimi 2.422/503 sayımlarını
ve satır ayrıntılarının çalışmasını insan UI kontrolü olarak doğruladı.
[Hazırlık ve ilerleme sınırı](../PU_REVIEW_PACKAGE_2026-11-20.md).

20 Kasım sonraki ürün kararı: yüzde yerine göreli düşük/orta/yüksek
risk gösterimi yönü seçildi. Ana 24 saatlik yangın hedefi korunuyor;
kategori kesimleri veya yeni yöntem/eğitim kabul edilmedi. İlk ürün
için mutlak yüzde kalibrasyonu şart koşulmuyor; gerçek hedefle
sıralama ilişkisi ve uygun değerlendirme hâlâ gerekli. Brier/kalibrasyon
incelemesi, ileride gerçekten olasılık iddiası kurulursa uygulanır;
AP ana sıralama ölçütü ve mevcut zaman rolleri değişmedi.
[Sunum kararı, anlamı ve kapsam sınırı](../SOURCE_RANKING_COMPARABILITY_2026-11-20.md).

20 Kasım aynı gün sabit-skor devamı: 168 anahtardaki kaynak AUC'sinin
mevsim/örtü karşılaştırma desteğine duyarlılığı incelendi; yeni eğitim
yok. Bu tanı gerçek yangın veya karışım varsayımı doğrulaması değil.
Mevcut kanıtla desteklenen teslim iddiasını sınırlama ve asıl doğrulanmış
olasılık sonucunu tek kabul koşulu tutma seçenekleri araştırmacıya
sunuldu; yön henüz seçilmedi. Ana hedef veya kabul kapısı bu öneriyle
değişmedi.
[Tanı ve karar noktası](../SOURCE_RANKING_COMPARABILITY_2026-11-20.md).

20 Kasım sınırlı yöntem provası: araştırmacının açık A kararıyla,
2018–2021'in 708 anahtarında kaynak üyeliği S için lojistik ve küçük
Random Forest kuruldu; 2022'nin 168 anahtarında ve eksiklik kontrolünde
yardımcı ROC-AUC incelendi. Gerçek yangın hedefi Y boş, AP ana ölçütü
ve 2023/2024/2025 rolleri korunuyor. Kaynak/gerçek sınıf ilişkisi ve
karışım koşulları henüz kabul edilmedi; ilk yardımcı modelin kurulması
birinci aşamanın veya nihai etiketli veri setinin kabulü değildir.
[Birincil dayanak, kapsam ve tamamlanan pilot](../CONDITIONAL_PU_RANKING_2026-11-20.md).

| Aşama | Çıktı | Tamamlanma ölçütü |
|---|---|---|
| Olay ve gözlem doğrulaması | Sürümlü olay tanımı, gözlem/eksiklik kaydı | Kaynak eşleşmesi, tekrar gruplaması, kapsam ve belirsizlik gerekçeleri; açık sorunlar kayıtlı |
| Model veri seti | Veri sözlüğü, özellik ve split manifesti | Anahtar/tarih/erişilebilirlik/olay sızıntısı kontrolleri; eksik değer ve örnekleme politikası |
| Temel modeller | Tekrarlanabilir karşılaştırmalar | Aynı veri ve ayrım üzerinde FWI uygunluğu, RF/XGBoost ve basit referansların değerlendirilmesi |
| Hata analizi ve kalibrasyon | İl/mevsim sonuçları, olasılık değerlendirmesi | Seçim yalnız eğitim/doğrulama üzerinden; ölçüm tanımı ve belirsizlik raporu |
| Bağımsız final değerlendirme | Dondurulmuş model ve test raporu | 2025 erişiminden önce veri/model/parametre/eşik sürümleri kayıtlı |
| Karar destek prototipi | Günlük çıktı ve harita | Tahmin zamanı, geçerlilik süresi, veri güncelliği, eksik bilgi alanı ve model sınırları görünür |

PR-AUC ana ölçüttür. Olasılıklar için Brier skoru ve kalibrasyon grafikleri,
uygulama için olay yakalama ve yanlış alarm yükü raporlanır. Başarı eşikleri
pilot çalışmadan sonra, nihai test açılmadan önce kaydedilecektir. Henüz hedef
başarı yüzdesi veya olumlu deney sonucu ilan edilmemiştir.

16 Ekim ölçüt netleştirmesi: araştırmacı AP'yi ana, trapez PR-AUC'ı yardımcı
hesap olarak kabul etti. Yukarıdaki PR ailesi ifadesi bu güncellemede AP
ile somutlaştırılır. [Uygulama, sentetik sınama ve kabul sınırı](../EVALUATION_CORE_2026-10-16.md).

19 Kasım yöntem hazırlığı yönü: araştırmacı, sonraki grafik birleşmelerinde
önceki başlangıç hipotezlerinin korunacağı A izleme provasını seçti.
Salur üzerinde sınırlı prova yapıldı. Bu yön seçimi olay kimliği,
gruplama eşiği, gerçek pozitif etiket veya eğitim kabulü sağlamıyor.
[İzleme provası ve sınırları](../EVENT_LINEAGE_PROTOTYPE_2026-11-19.md).

16 Ekim ön işleme hazırlığı: öğrenilen medyan/ölçek parametreleri yalnız
eğitim içi her ayrımın eğitim kısmından hesaplanacak şekilde sınandı.
Gerçek doldurma/ölçekleme/boş sütun politikası seçilmedi; sentetik prova
gerçek eğitim veya etiket kabulü değildir.
[Sözleşme ve kontroller](../FOLD_PREPROCESSING_2026-10-16.md).

16 Ekim deney kaydı hazırlığı: mevcut dosya/kod/ayar kanıtları ile ayrı
sentetik ayrım ve ön işleme kayıtları değişiklik denetimli kimliklere
bağlandı. Gerçek model, örnekleme, kalibrasyon ve onay alanları beklemededir;
bu kayıtlar gerçek deneyin veya bilimsel kabulün yerine geçmez.
[Kayıt ve sınırlar](../EXPERIMENT_RECORD_2026-10-16.md).

16 Ekim sınıf ağırlığı/kalibrasyon taslağı: ağırlıksız ve fit bölümünden
balanced ağırlıklı temel modellerin ham/sigmoid/koşullu isotonic çıktıları
önerildi. Araştırmacı 2023 kalibrasyon/2024 karşılaştırma hazırlık yönünü
seçti; etiket/olay desteği doğrulanmadı. 12 Ekim önerisinin geçmişi korunur.
Gerçek sınıf oranı/yöntem seçilmedi; etiket/eğitim kapıları kapalıdır.
[Kaynaklar, öneriler ve sentetik kontroller](../IMBALANCE_CALIBRATION_PLAN_2026-10-16.md).

16 Ekim alt grup raporu: il/mevsim ve nominal destek paydaları aynı ana
kohortla uzlaştırıldı. Eksik hedef/tahminli grup sessiz alt küme skorlaması
yapmaz; boş ve tek sınıflı gruplar açık durumlarla gösterilir. Gerçek
156 amaçlı birim etiketsiz kaldı; skorlar yalnız ayrı sentetik provadadır.
İstatistiksel destek/güven aralığı ve gerçek model başarısı iddia edilmez.
[Şema, sayımlar ve sınırlar](../SUBGROUP_REPORT_2026-10-16.md).

16 Ekim envanteri: 72 aylık özellik adayı üretimi ile etiket/bilimsel kabul
ayrıldı. Güncel dosya varlığı/boyutu ve metadata kontrolü son parça kabulü
yerine konulmadı. Kurum yanıtı, alternatif referans ve araştırmacı yöntemi
kararı ayrı kanıt türleri olarak tutuldu; 15 açık iş bağımlılıklarla yazıldı.
[Güncel envanter ve kabul sırası](../PREPARATION_INVENTORY_2026-10-16.md).

## Açık bilimsel konular

8 Kasım kapsam kararı. Araştırmacı 24 saatlik gerçek yeni orman ve
çalılık yangını hedefini korudu. Mevcut inceleme paketi, bağımsız
olay ve değerlendirme kanıtı beklenirken araştırma çıktısı olarak
kullanılır. [İnceleme dosyaları ve devam koşulları](../RESEARCH_DATA_HANDOFF_2026-11-08.md).

4 Kasım yöntem yönü: araştırmacı, kurumsal talep açmadan PU öğrenmenin
uygulanabilirliğini araştırmayı seçti. Güvenilir pozitif tanımı, belirsiz
havuzun temsili, etiketlenme mekanizması, sınıf oranı ve değerlendirme
dayanağı incelenecek. OGM talebi bu yönün ilerleme koşulu değildir.
Araştırma tercihi, gerçek P/U eğitim tablosu veya yöntem kabulü sayılmaz.
[Karar ve uygulanabilirlik sınırları](../LABEL_PROTOCOL_DECISION_2026-11-04.md).

23 Ekim kapsam kararı: araştırmacı orman ve çalılığı ana araştırma yönü olarak
seçti. Tarım/yerleşim eşleşmeleri ayrı incelemede korunacak; noktaya veya
5 km hücreye uygulanacak nihai habitat filtresi henüz seçilmedi. Eski harita
merkeziyle tek başına yangın türü belirlenmeyecek. [Karar ve tamamlanan sınırlı
konum/komşu örtü tanısı](../HABITAT_SCOPE_DIRECTION_2026-10-23.md).

22 Ekim ilerleme yönü: araştırmacı üniversite üzerinden OGM talebini şimdilik
planlamıyor. OGM verisi zorunlu erişim koşulu yapılmadan açık kanıtlarla
ilerleme benimsendi; bilimsel hedef, gözlem veya etiket kabulü değiştirilmedi.
Dokuz mevcut kataloğun bütün ilk hücre-gün adaylarında 7.610 anahtarın
5.214'ü varlık/zaman/üyelikte eşit; 2.396'sı en az birinde duyarlı bulundu.
Bu eşitlik bağımsız gerçek yangın doğrulaması veya kabul edilmiş eğitim alt
kümesi değildir. [Kapsam, örnekler ve sonraki sınırlı iş](../EVENT_SENSITIVITY_2026-10-22.md).

21 Ekim kaynak yanıtı: NASA/FIRMS, CSV version=2'nin Collection 2 olduğunu
doğruladı. Destek yanıtı güncel VIIRS v4/MODIS v3 beyanı içeriyor; önceki
yerel indirmelerin aylık üretim sürümünü teyit etmiyor. Kaynak kabulü yerine
konulmadı. [Yanıt ve yeni teslimle karşılaştırma planı](NASA_FIRMS_REPLY_2026-10-21.md).

19 Ekim kurumsal erişim güncellemesi: araştırmacının paylaştığı CİMER yanıtı
ayrıntılı olay verisinin üniversite üzerinden resmî yazıyla istenmesi yolunu
belirtiyor. Olay verisi veya teknik alan açıklaması alınmadı; bilimsel kabul
açıkları kapanmadı. [Yanıtın sınırı ve gereken idari adım](OGM_UNIVERSITY_ROUTE_2026-10-19.md).

17 Ekim hazırlık sınırı: NASA/FIRMS ve OGM yanıtlarının etkileyebileceği
etiket kararları beklemede tutulur. Mevcut özelliklerin güncel içerik
denetimi, yanıt/karar dosyası ve üretim ön kontrolü ayrı hazırlıklardır;
etiket üreticisi veya nihai veri seti kabulü değildir. Yeni tanı çalışması
yalnız tanımlı bir kabul eksikliğini kapatıyorsa yürütülür.
[Üç hazırlık, somut insan incelemesi ve sonraki sıra](../RESPONSE_WAITING_PREPARATION_2026-10-17.md).

16 Ekim ilk hücre yönü: araştırmacı, aynı en erken kayıtlı zamanda bulunan
bütün hücrelerin ortak aday kimliği altında tutulmasını seçti (A).
`first_cell_candidates_v1` bu aday temsilini saklar; fiziksel olay kimliği,
gruplama yarıçapı/zamanı, 0/1 etiket veya eğitim kabulü sağlamaz.
[Örnekler, kapsam etkisi ve testler](../EVENT_FIRST_CELL_OPTIONS_2026-10-16.md).

- NASA/FIRMS yanıtı alındı; yerel teslimlerin aylık Type üretim sürümüne bağlanması açık.
- Yaklaşık gözlem alanı hesabının fiziksel yorumu ve günlük negatif etiket kuralı açık.
- 31 Aralık 2023 için iki yangın/geolocation işleme sürümü uyuşmazlığı çözülmedi.
- NOAA-20 erken dönem katalog eşleşmesi açık; eksik kaynak yangınsız gün sayılmaz.
- ERA5-Land geriye dönük araştırma verisidir; operasyonel tahmin anındaki
  erişilebilirlik ve geçmiş hava tahmini arşivinin uygunluğu ayrıca değerlendirilmelidir.
- Bağımsız olay doğrulama kaynağının erişimi ve uzman incelemesinin kapsamı kesinleşmedi.
- 15 Ekim kaynak sürekliliği güncellemesi: NOAA/NASA, S-NPP'nin yeni veri
  dağıtımının 2 Kasım 2026'da bitmesini planlıyor; tarihsel arşiv korunuyor.
  Canlı ürün için NOAA-20/21 gözlem kapsamı ve sensör uyumu ayrıca ölçülecek.
  Bu duyuru mevcut eğitim kaynağının iptali değildir.
  [Resmî kaynaklar ve araştırma yorumu](../OBSERVATION_CORE_CATALOGUE_2026-10-15.md).

16 Ekim gruplama araştırması: üç birincil yöntemdeki eşiklerin farklı
amaç/algoritma rollerinde olduğu doğrulandı; doğrudan aktarım yapılmadı.
19 duyarlı örnekte hedef gün sonrası tespitler çıkarıldığında ilk
zaman/hücre eşleşmesi değişmedi; bu sınırlı sonuç gruplama doğruluğu
sayılmaz. Sıradaki öneri adayların başlangıç ve birleşme geçmişlerini
ayrı karşılaştırmaktır; tek bir eşik veya gerçek etiket kabul edilmedi.
[Kaynaklar, tanı ve sınırlar](../EVENT_GROUPING_CONTEXT_2026-10-16.md).

16 Ekim geçmiş tanısı: aynı 181 bağlamda başlangıç/devam/birleşme
kayıtları korundu. Birleşme önceki başlangıcı silmez; tespitin alındığı
andaki çok başlangıçlı geçmiş tek fiziksel kök kabul edilmez. Fiziksel
bölünme uygulanmadı ve 171 aday eşleşmesi değişmedi. Öncelik iki somut
örneğin uygun dış kanıtla incelenmesidir; bu tanı gruplama/etiket kabulü
sağlamaz. [Yöntem ve kontroller](../EVENT_LINEAGE_2026-10-16.md).

## Ürün ve kapsam kararları

Ana hedef 24 saattir. 72 saat ve daha uzun ufuklar araştırma önerisidir; veri,
hedef tanımı ve ayrı doğrulama olmadan ana kapsamın tamamlanmış parçası sayılmaz.
Günlük tahmin güncellemesi, modelin her gün yeniden eğitilmesini gerektirmez.
Geçmiş dönemleri Power BI ile inceleme fikri ve günlük risk arayüzü danışmanla
değerlendirilecek ürün seçenekleridir. Henüz bu seçenekler için uygulama yapılmadı.

## Literatür sonrası araştırma yönü — 12 Ekim 2026

Danışmanın literatür karşılaştırması talebi üzerine
[yapılandırılmış inceleme](LITERATURE_REVIEW_2026-10-12.md), 34 seçilmiş
kaynak kaydı ve [deney protokolü](ARTICLE_RESEARCH_PROTOCOL_2026-10-12.md)
hazırlandı. Bu güncelleme 9 Ekim çerçevesini sonuç elde edilmiş gibi
değiştirmez; yeni öneri danışman değerlendirmesine açıktır.

Genel 24 saatlik uydu/meteoroloji/yapay zekâ yaklaşımı, Türkiye ürünleri,
ilk tespit çıkarımı, eksik etiket ve kalibrasyon literatürde vardır.
Özgünlük iddiası bu bileşenlerin ilk kullanımına bağlanmaz. Öncelik, dört
ilde olay/gözlem politikasının sonuç ve kapsama etkisini ortak incelenmiş
değerlendirme çekirdeğinde sınamaktır. Özellik grubu ablasyonu, kalibrasyon
ve sabit uyarı kapasitesinde olay yakalama/yanlış alarm bunu destekler.

Bağımsız/uzman olay referansı ve güvenilir negatifler en kritik kapıdır;
mevcut unknown/negative_label_permitted=false değişmez. AP ile trapez
PR-AUC'ın uygulama tanımı deneyden önce ayrılacaktır; eğitim/2024 seçimi
ve kapalı 2025 final düzeni korunur. FWI standart girdileri ve durum
devri doğrulanmadıkça hesaplanmış baseline sayılmaz. Retrospektif ERA5
araştırması, forecast arşivi olmadan operasyonel ürün kabulü değildir.

## Kayıt düzeni ve kanıt

Her deney veri/config/seed/kod/ortam sürümü ve çıktı konumuyla kaydedilir.
Önemli iddialar [kanıt dizininde](EVIDENCE_REGISTER.md) izlenir. Makine çıktıları
`outputs/` altında kalır; raporlar ilgili çıktının konumunu ve denetim sınırını belirtir.
Kabul edilmiş deney kayıtları metinsel düzenleme amacıyla değiştirilmez.
