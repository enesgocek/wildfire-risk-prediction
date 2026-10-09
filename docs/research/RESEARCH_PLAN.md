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

## Açık bilimsel konular

- NASA FIRMS Type üretim sürümüne ilişkin teknik yanıt bekleniyor.
- Yaklaşık gözlem alanı hesabının fiziksel yorumu ve günlük negatif etiket kuralı açık.
- 31 Aralık 2023 için iki yangın/geolocation işleme sürümü uyuşmazlığı çözülmedi.
- NOAA-20 erken dönem katalog eşleşmesi açık; eksik kaynak yangınsız gün sayılmaz.
- ERA5-Land geriye dönük araştırma verisidir; operasyonel tahmin anındaki
  erişilebilirlik ve geçmiş hava tahmini arşivinin uygunluğu ayrıca değerlendirilmelidir.
- Bağımsız olay doğrulama kaynağının erişimi ve uzman incelemesinin kapsamı kesinleşmedi.

## Ürün ve kapsam kararları

Ana hedef 24 saattir. 72 saat ve daha uzun ufuklar araştırma önerisidir; veri,
hedef tanımı ve ayrı doğrulama olmadan ana kapsamın tamamlanmış parçası sayılmaz.
Günlük tahmin güncellemesi, modelin her gün yeniden eğitilmesini gerektirmez.
Geçmiş dönemleri Power BI ile inceleme fikri ve günlük risk arayüzü danışmanla
değerlendirilecek ürün seçenekleridir. Henüz bu seçenekler için uygulama yapılmadı.

## Kayıt düzeni

Her deney veri/config/seed/kod/ortam sürümü ve çıktı konumuyla kaydedilir.
Önemli iddialar [kanıt dizininde](EVIDENCE_REGISTER.md) izlenir. Makine çıktıları
`outputs/` altında kalır; raporlar ilgili çıktının konumunu ve denetim sınırını belirtir.
Kabul edilmiş deney kayıtları metinsel düzenleme amacıyla değiştirilmez.
