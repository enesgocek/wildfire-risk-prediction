# Araştırma çerçevesi

Kayıt tarihi: 9 Ekim 2026. Durum: bitirme çalışmasının araştırma çerçevesi;
2209-A başvurusu ve danışman değerlendirmesi henüz yapılmadı.

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

Bu soru bir sonuç veya özgünlük kanıtı değildir. Literatür karşılaştırması ve
danışman değerlendirmesiyle başvuru metnine dönüştürülecektir.

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

16 Ekim ilk hücre yönü: araştırmacı, aynı en erken kayıtlı zamanda bulunan
bütün hücrelerin ortak aday kimliği altında tutulmasını seçti (A).
`first_cell_candidates_v1` bu aday temsilini saklar; fiziksel olay kimliği,
gruplama yarıçapı/zamanı, 0/1 etiket veya eğitim kabulü sağlamaz.
[Örnekler, kapsam etkisi ve testler](../EVENT_FIRST_CELL_OPTIONS_2026-10-16.md).

- NASA FIRMS Type üretim sürümüne ilişkin teknik yanıt bekleniyor.
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
