# Makale yönü için önerilen deney protokolü

Tarih: 12 Ekim 2026. Durum: literatüre dayalı **öneri**; danışman tarafından
onaylanmış, uygulanmış veya başarılı olmuş deney değildir. Bilimsel veri
kabul kapılarını açmaz. Dayanak [literatür incelemesidir](LITERATURE_REVIEW_2026-10-12.md).

## Araştırma problemi ve hedef

Çalışma birimi uygun habitatı gerekçelendirilmiş 5 km hücre ve T=00:00 UTC'dir.
Hedef, `(T,T+24 saat]` içinde yeni bir olayın ilk aktif yangın tespitidir.
T öncesinde başlamış olayın yeni hotspot'ları yeni olay sayılmaz. İlk uydu
tespiti gerçek tutuşma zamanı değildir. Olasılık tahmininin hangi gözlenen
hedefe ve hangi kabul edilmiş örneklem evrenine ait olduğu açık yazılmalıdır.

Ana soru: Olay tanımı ve gözlem yeterliliği belirsizliği, aynı coğrafi/zamansal
çerçevede model değerlendirmesini ve günlük uyarı yükünü ne kadar değiştirir?
Soru, “etiket politikasını değiştirmek gerçek yangınları azaltır” biçiminde
nedensel iddia değildir. Mevcut kaynaklar yalnız gözlemsel araştırma sağlar.

## Hipotezler ve karşılaştırmalar

| Hipotez | Deney | Birincil sonuç | Reddedilme / sınırlama |
|---|---|---|---|
| H1: Arazi ve geçmiş bitki örtüsü, meteoroloji temelinden ek bilgi sağlar | Aynı kabul edilmiş kayıtlarda meteoroloji; +arazi/örtü; +NDVI/NDMI; gerekirse görüntü yaşının ayrı ablasyonu | AP farkı ve sabit uyarı kapasitesinde olay yakalama farkı | Etki belirsiz/negatifse üstünlük söylenmez; veri hazırlama maliyeti de kaydedilir |
| H2: Olay/gözlem politikaları ölçülen başarıyı ve kapsama alanını değiştirir | Gerekçeli olay sürümleri ve yalnız kabul edilebilir gözlem politikaları | Ortak incelenmiş çekirdekte ölçüt farkı; tüm evrende kapsama/exclusion farkı | Daha kolay kayıt seçimi iyileşme diye sunulmaz; aynı olay referansı kullanılır |
| H3: Kalibrasyon olasılık güvenilirliğini değiştirebilir | Ham ve doğrulama verisiyle kalibre edilmiş aynı model | Brier, log-loss ve güvenilirlik grafiği | Kalibrasyon her modelde iyileşmeyebilir; seçim/test bağımsızlığı gerekir |
| H4: Model günlük sınırlı inceleme kapasitesinde basit referanslardan yararlı olabilir | Aynı K ve uygun hücre evreninde mevsimsel/bölgesel referans, lojistik regresyon, RF, XGBoost | Tekil olay yakalama ve doğrulanmış yanlış uyarı yükü | Retrospektif sonuç gerçek saha müdahale etkisi değildir |

H1/H4 aynı doğrulanmış değerlendirme satırlarında ölçülür. H2 hem ortak
çekirdekte hem her politikanın ayrı kabul evreninde raporlanır; bu iki payda
birbirine karıştırılmaz. Politika/model seçiminin ölçütleri nihai testten
önce kaydedilir. Sıfır etki veya daha sade modelin yeterliliği raporlanabilir.

## Etiket denetimi: en kritik kabul kapısı

Mevcut FIRMS tespitlerinden keşif amaçlı olay gruplamaları vardır; hiçbiri
bu belgeyle doğru olay listesi ilan edilmez. Uzman inceleme formunda ardışık
tekrarlar, uzamsal zincirleme, ilk hücre belirsizliği, habitat sınırı, gün/yıl
geçişi ve sensörler arası fark ayrı kaydedilmelidir. Grup eşiği final
başarıya göre ayarlanamaz. Dönem sınırını aşan olayın tekrarları farklı
ayrımlara sızmamalıdır.

İki referans türü ayrılır:

- **Bağımsız olay dayanağı:** izinle alınabilirse müdahale/olay kayıtları veya
  bağımsız uzman incelemesi. Kayıtların kapsamı, konum/tarih belirsizliği ve
  kaçırdığı olaylar yazılır. Erişim elde edilmiş değildir.
- **Uydu kaynak kontrolü:** ham ürün/geolocation, EFFIS sınırı, başka uydu
  ürünü ve algoritma bilgisi. Aynı sensörden türeyen iki ürün bağımsız saha
  doğrulaması değildir. NASA teknik yanıtı algoritma sorusuna yardımcı
  olabilir; bütün etiketlerin doğruluğunu kanıtlamaz.

İnceleme örnekleri eğitim/2024 içinden, yıl/mevsim/il, tespit büyüklüğü,
sensör, eksiklik ve zor vakaya göre tabakalanmalıdır. Amaç kolay örneklerde
yüksek uyum üretmek değildir. Eşleştirme toleransı, incelemeci sayısı,
anlaşmazlık çözümü ve örnekleme olasılıkları önceden kaydedilir. Final 2025
görülerek politika tasarlanmaz; dondurulmuş protokol finalde uygulanır.

Gözlem alanı varlığı tek başına bulut/duman/algılama eşiği sorununu çözmez.
Negatif için gerekçeli algılama yeterliliği kuralı gerekir. Eksik gözlem
günü “yangınsız” yapılmaz. `daily_observation_status=unknown` ve
`negative_label_permitted=false`, ayrı doğrulanmış protokol olmadan korunur.
Belirsiz kayıtları otomatik sıfır yapan bir üretim/baseline veri seti kurulmaz.

Pozitif–etiketsiz öğrenme alternatif araştırma olabilir, ancak sınıf öncülü,
algılanma mekanizması ve tanımlanabilirlik varsayımları incelenmeden doğru
yangın olasılığı verdiği söylenmez. Bu alternatif mevcut etiket kapısını
atlayan kısa yol değildir; [R21–R23](literature_sources_2026-10-12.json)
tam yöntem incelemesi ve ayrı protokol gerektirir.

## Tahmin anında erişilebilirlik ve özellikler

Mevcut 27 aday: 11 meteoroloji, 7 örtü, 5 arazi ve 4 NDVI/NDMI özelliği.
H1 bunların katkısını ölçer; tüm adayların kullanılması zorunlu değildir.
Her kayıtta gözlem zamanı, erişilebilirlik, ürün/yöntem sürümü ve kaynak
hash'i izlenir. Imputasyon ve öğrenilen dönüşümler her fold'da yalnız
eğitim kısmına fit edilir. İleriye doğru dolgu ancak geçmişte mevcut veriyle
yapılabilir; gelecekteki değerle geriye doldurma uygulanamaz.

Tahmin sonrası uydu coverage bilgisi etiket denetiminde kullanılabilir,
model girdisi olamaz. Pozitiflerin kalite ölçüsü ile negatiflerin coverage
farkının hedefi dolaylı kodlayıp kodlamadığı ayrıca denetlenir. Geleceğe ait
yanmış alan, olayın nihai büyüklüğü ve hedef günün gerçekleşmiş meteorolojik
toplamı özellik olamaz. Statik örtü referans yılının geçmiş yangın izlerini
kodlama olasılığı değerlendirilir.

ERA5-Land geriye dönük yeniden analizdir. T öncesindeki gözlem penceresini
kullanmak yayın gecikmesini kendiliğinden çözmez. İlk aşama retrospektif
benchmark olarak sunulur; operasyonel kol için yayımlanma/issue zamanı
T'den önce olan hava tahmini arşivi ve hizmete giriş koşulları gerekir.
Tahmin valid time'ının T'den sonraya uzanması, issue time önceyse meşru
tahmin girdisidir; gerçekleşmiş gelecekteki hava ölçümüyle aynı şey değildir.

Yol/yerleşim/yıldırım veya insan faaliyeti özellikleri mevcut adaylar içinde
olmadıkça kullanılmış sayılmaz. Ancak mevcut modellerin sistematik hatası
gerekçe sağlarsa, kaynak lisansı ve geçmiş erişim yılıyla yeni öneri yapılır.
Uydu foundation model/Transformer, tabular temele ek değeri gerektirmeden
önceliklendirilmez. Yeni kaynak indirme bu belgeyle başlatılmaz.

## Veri ayrımı ve adil model seçimi

**2018–2023 eğitim, 2024 doğrulama, 2025 kapalı final test korunur.**

1. Eğitim yıllarında ileri zaman doğrulaması yapılır; sonraki yıl geçmiş
   yıllardan tahmin edilir. Tüm yılları rastgele karıştırmak ana kanıt değildir.
2. Eğitim içi bölgesel bloklar ve uygun olduğunda il dışarıda bırakma deneyi
   uygulanır. Yalnız dört il vardır; Türkiye çapında genelleme iddia edilmez.
   Buffer büyüklüğü eğitimdeki bağımlılık ve bilimsel gerekçeyle belirlenir.
3. Aynı olay farklı fold'a geçmez. Sınır olayları ve `(T,T+24h]` penceresi
   için dışlama/embargo sürümü önceden manifestlenir. Rastgele hücre ayrımı
   ancak açık bir duyarlılık deneyi olabilir, ana genelleme ölçümü değildir.
4. 2024'ün model seçimi, kalibrasyon ve kapasite/eşik seçimindeki rolleri
   önceden ayrılır. Zamansal alt bölme veya çapraz tahmin planı kaydedilir;
   aynı kayıt üstünde fit edilmiş kalibrasyonun başarısı bağımsız sonuç sayılmaz.
5. Final öncesinde model, özellikler, etiket/habitat politikası, kalibrasyon,
   K/eşik, seed, kod ve veri sürümleri dondurulur. 2025 bir kez değerlendirilen
   rapordur; sonuç görülerek yeni yöntem seçilip aynı test tekrar kullanılamaz.

Sınıf ağırlığı/undersampling yalnız eğitimde uygulanabilir. Değerlendirme
evreninde doğal kabul edilmiş sınıf oranı korunur. Örnekleme sonrası olasılık
çıktısının hangi dağılıma ait olduğu düzeltilmeden “%risk” sunulmaz. Alternatif
model ile aynı örnekleme/hiperparametre arama bütçesi veya farkın gerekçesi
kaydedilir. Karşılaştırma yalnız yüksek skorlu tek seed üzerinden seçilmez.

## Temel modeller ve FWI sınırı

| Referans | Amaç | Koşul |
|---|---|---|
| Bölgesel/mevsimsel geçmiş oran | Öğrenilmiş modelin basit tarihsel riske ek değerini ölçmek | Yalnız eğitim bilgisi; düşük olay sayısında yumuşatma önceden belirlenir |
| Düzenlileştirilmiş lojistik regresyon | Basit açıklanabilir olasılık temeli | Ölçekleme ve seçim fold içinde |
| Random Forest | Tabular doğrusal olmayan karşılaştırma | Aynı veri ve arama bütçesi |
| XGBoost | Güçlü tabular temel | Kalibrasyon/örnekleme etkisi ayrı |
| FWI / resmî hava tehlike ürünü | Meteorolojik tehlike karşılaştırması | Standart hesap, yerel öğlen, önceki nem durumu, arşiv/issue zamanı doğrulanmışsa |

FWI gerçek yeni yangın olasılığı değildir. Mevcut günlük 11 hava özetinden
standart FWI'ın otomatik hazır olduğu söylenmez. Yerel öğlen girdileri,
24 saat yağış aralığı, başlatma ve durum devri çözülmeden bu satır uygulanamaz.
Tam FWI yerine başka bir proxy kullanılırsa adı ve sınırı açıkça değiştirilir.
FWI gerekirse sıralama referansı olarak aynı hedefe karşı ölçülür; kendi
endeksini tahmin eden modelle olay olasılığı skorları karıştırılmaz.

## Ölçüt sözleşmesi

16 Ekim tarihli sonraki karar: araştırmacı AP ana/trapez PR-AUC yardımcı
seçeneğini kabul etti. Aşağıdaki 12 Ekim önerisi tarihsel kayıttır;
hesap tanımı artık [ayrı sürümlü değerlendirme yapılandırmasıyla](../EVALUATION_CORE_2026-10-16.md)
somutlaştırıldı. Bu araştırmacı kararı bağımsız doğrulama, danışman onayı
veya gerçek model deneyi değildir.

Ana PR ailesi korunur; uygulama başlamadan **Average Precision (AP)** ve
trapez integral PR-AUC farklı tanımlarla ayrı adlandırılır. Ana özet için
AP önerilir; mevcut “PR-AUC” ifadesinin hangi hesap olduğu danışmanla
dondurulacaktır. Araç sürümü, interpolasyon ve pozitif sınıf prevalansı
raporlanır. ROC-AUC ikincildir; accuracy tek başına başarı değildir.

- **Hücre-gün:** AP, uygun PR eğrisi, Brier, log-loss ve kalibrasyon grafiği.
  Naif prevalans tahminiyle Brier karşılaştırması; olasılık hatası il/mevsim
  kırılımı. Az olaylı gruplar için yorum sınırı gösterilir.
- **Olay:** K uyarı hücresinden birinin, o gün ilk tespiti gerçekleşen
  referans olayın kabul edilmiş ilk hücresini yakalaması. Aynı olay bir kez
  sayılır; çok hücreli ilk tespit için tie/konum toleransı önceden tanımlanır.
- **Uyarı yükü:** değerlendirmeye uygun 1.000 hücre-gün başına doğrulanmış
  yanlış uyarı, günlük uyarı hücresi sayısı ve gösterilen risk alanı. Belirsiz
  etiketli alarm “kesin yanlış” sayılmaz; ayrı doğrulanamayan alarm sayılır.
- **Kapsam:** toplam hedef evreni, etiketle değerlendirilebilir evren, ortak
  politika çekirdeği, dışlanan/bilinmeyen gün ve alan. Yalnız değerlendirilebilir
  kayıt başarısı, bütün ilin kapsandığı anlamına gelmez.

K için 5/10/20 gibi aday kapasite noktaları önceden değerlendirilebilir;
gerçek kullanıcı kapasitesi henüz belirlenmedi. Bunlar gerçekleşmiş saha
planı değildir. Eşit skor/tie kuralı, minimum score ve uygun hücre sayısı
K'den az olduğundaki davranış belirlenir. Bilinmeyen özellik/etiket alanı
haritada düşük riskle karıştırılmaz.

Farkların güven aralıkları, olayların bağımlılığını ve negatiflerin günlük/
mekânsal blok yapısını koruyan eşlenik tekrar örneklemeyle üretilir. Hücreleri
bağımsız sayan rastgele bootstrap ana yöntem olmaz. Tekrar sayısı ve
blok tanımı eğitim pilotu üzerinden önceden kaydedilir. Az olay/küme
varsa güven aralığı ve güç sınırlaması açık yazılır; varsayımsal olay sayısı
veya elde edilmemiş anlamlılık sonucu ilan edilmez.

## Yayın için kanıt ve uygulanabilirlik kapıları

| Kapı | Gerekli kanıt | Bugünkü durum |
|---|---|---|
| K1: Kaynak/etiket | Olay tanımı, gözlem yeterliliği, belirsizlik ve bağımsız/uzman referans | Açık; kuyruk tamamlanması çözüm değildir |
| K2: Zamansal veri | T öncesi pencere ve erişilebilirlik denetimi, habitat/split sözleşmesi | Aday altyapı var; operasyonel arşiv ayrı açık |
| K3: Adil benchmark | Aynı örneklem/ayrım üzerinde basit ve güçlü referanslar | Eğitim henüz yapılmadı |
| K4: Katkı | Etiket/özellik/kalibrasyon ablationları; coverage ve hata etkisi | Öneri; olumlu sonuç yok |
| K5: Sağlamlık | İl/mevsim/yıl kırılımı, bağımlılığı koruyan güven aralığı, final freeze | Öneri; 2025 kapalı |
| K6: Yeniden üretim | Veri/kod/seed/ortam/lisans manifesti ve güvenli paylaşım | Mevcut provenance geliştirilir; ham veri yayın izni varsayılmaz |

K1 çözülemezse sonuç kesin oluşma olasılığı olarak sunulmaz. Danışmanla
gözlenen tespit sıralaması/etiket belirsizliği araştırması olarak daraltma
veya ayrıca varsayımlı PU deneyi değerlendirilir. Yapay bir negatif çoğunluk
üretilip yüksek accuracy ile makale hedeflenmez.

## Uygulama sırası ve danışmanla açık kararlar

1. En yakın çalışmaların tam metin/ek erişim boşluklarını kapatmak ve bu
   hipotezlerin mevcut araştırmalara ek değerini danışmanla daraltmak.
2. Mevcut zor vaka/olay/habitat formlarıyla K1 denetim planını, erişilebilir
   bağımsız kaynak ve inceleme örneklemini belirlemek.
3. Kuyruklar tamamlandığında kaynak geri okuması ve eksik dönem envanteri;
   ardından etiket/zaman kapıları. Eksik Aralık günü saklanır, otomatik tamamlanmaz.
4. Yalnız K1–K2 geçerse eğitim adaylarını birleştirmek; training içi pilotla
   veri yeterliliği, model ve metrik sözleşmesini dondurmak.
5. H1–H4 ve 2024 seçimini uygulamak; önce sonuçları ve sınırları raporlamak.
6. 2025 final değerlendirmesi ve makale; operasyonel veri kolu ve web ürünü
   ayrıca doğrulanır. Başarı/yayın garantisi yoktur.

Danışmanla karara bağlanacak başlıklar: yeni olay tanımı; bağımsız kayıt
erişimi; uygun negatiflerin kanıtı; küçük/büyük yangın kapsamı; AP tanımı;
birincil hipotez ve kapasite; minimum örneklem/güç; makale kapsamı. Bunlar
danışmanın bugün onayladığı kararlar olarak kaydedilmemiştir.

Canlı bilimsel/bulut kodu, süre/Stop ayarları ve hash bağlı paketler bu
protokol hazırlığında değiştirilmedi. Bu belge yeni bulut işi yetkisi değildir.
