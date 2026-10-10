# Veri seti kabul sözleşmesi taslağı — 10 Ekim 2026

Durum: yöntem ve teslim kabulü hazırlığı; nihai etiket/habitat politikası
onaylanmış veya bütün veri seti hazırlanmış değildir. Taslak, kayıtlı
24 saatlik hedefi ve veri ayrımını değiştirmez. Çalışan üretim paketleri
bu belge nedeniyle yeniden kurulmaz.

## Anahtar, zaman ve parça düzeni

Satır anahtarı `(grid_id, prediction_timestamp_utc)`, T=00:00 UTC'dir.
Günlük tablo anahtarları tekil olacak; bilinmeyen hücre ve çoğaltan/kaybettiren
eşleşme kabul edilmeyecek. Etiket penceresi `(T,T+24 saat]` olarak kalır.
Nihai olay kimliği hücre anahtarından ayrıdır; aynı olay farklı veri
ayrımlarına veya farklı değerlendirme foldlarına sızdırılmaz.

Tam coğrafi anahtar envanterinde beklenen aday satır sayıları:

| Dönem | Gün | Hücre-gün | Ayrı 30/60 gün bitki örtüsü uzun tablo satırı |
|---|---:|---:|---:|
| Eğitim 2018–2023 | 2.191 | 6.351.709 | 12.703.418 |
| Doğrulama 2024 | 366 | 1.061.034 | 2.122.068 |

Bu sayılar takvim × 2.899 hücre hesaplarıdır; kabul edilmiş etiket veya
model örneklem sayısı değildir. Habitat, gözlem ve dönem kenarı politikası
nihai model örneklemini değiştirebilir; her dışlama nedeni ayrıca tutulur.
2025 final testi hazırlanmış tabloya katılmaz; ayrı freeze/final erişim
aşamasını bekler. 2024 bitki örtüsü/gözlem eksikleri aynı dondurulmuş
politika için ayrı doğrulama hazırlığını gerektirir; mevcut bitki örtüsü
kuyruğu 2018–2023 içindir.

Tam dönem büyük tek CSV/DataFrame olarak bir defada belleğe alınmaz.
Aylık parçalar ve parçaların hash/anahtar sayısını tutan manifest tercih
edilir. [Dört günlük kayıt/okuyucu pilotu](FEATURE_PARTITION_PILOT_2026-10-10.md)
günlük CSV parçaları ve hash manifestiyle geri okundu; tam dönem fiziksel
üretimi ve nihai biçim/verim seçimi henüz yapılmadı. Feature,
kalite/provenance ve hedef tabloları aynı anahtarla
ayrı tutulur; [27 aday alan](FEATURE_JOIN_PILOT_2026-10-10.md) modelin son
özellik seçimi değildir.

## Eksik değer ve kalite sözleşmesi

- Eksik sürekli özellik NaN olarak korunur; yokluk ölçülmüş sıfır değildir.
- 30 ve 60 günlük bitki örtüsü pencereleri ayrı kalır. Günlük taşıma,
  kayıtlı geçmiş kesim ve görüntü yaşıyla açıklanır; gelecekten doldurma yoktur.
- Meteoroloji destek eksikliği, uydu yangın gözlem eksikliği ve habitat
  uygunluğu farklı kavramlardır; tek bir `eligible` sütununda birleştirilmez.
- Kıyı/alan desteği oranları otomatik kırpılmaz. Yalnız su, küçük alan,
  kısmi destek ve eski görüntü işaretleri karar kanıtıyla birlikte tutulur.
- Etiket denetimindeki hedef pencere gözlem durumu model girdisi olmaz.
  Özellik eksiklik işaretini deneyde kullanmak ayrıca sürümlü model kararıdır.
- İmputasyon uygulanacaksa yalnız ilgili training folduna fit edilir.
  Validation/test ortalaması, bütün dönem medyanı veya yangından sonraki
  görüntü kullanılamaz. Bir sütun training foldunun tamamında boşsa açık
  politika gerekir; otomatik sıfır üretilemez. Henüz imputasyon yapılmadı.
- Komşu meteoroloji veya alternatif ürün, ayrı kaynak/zaman/mekânsal
  yöntem denetimi olmadan mevcut eksikleri doldurmaz. Kaynak destek
  kaybının coğrafi/örtü etkisi [destek raporuyla](DECISION_REVIEW_2026-10-10.md) ölçülür.

## Etiket kabul kapıları

Mevcut [kapalı kabul denetimi](TARGET_ADMISSION_REVIEW_2026-10-10.md) 0/1
atamasını reddeder. Aşağıdaki kanıtlar kabul edilmeden bu kapı açılmaz:

| Alan | Kabul için gerekli kayıt | Şu an |
|---|---|---|
| Kaynak semantiği | Type/sürüm, seçilen tespit kapsamı ve açık kaynak istisnaları | Teknik teyit açık |
| Olay | Sürümlü gruplama, tekrar tespit ve zincir vakalarının gerekçesi | Keşif kataloğu mevcut |
| İlk hücre | İlk anda çok hücre ve konum belirsizliğine tutarlı kural | Karar açık |
| Habitat | Model kapsamı, sınır/su/odunsu tarım ve eski harita sınırlaması | Ön inceleme/vaka paketi mevcut |
| Negatif | Gerekçeli gözlem ölçütü, eksik kaynak ve belirsiz gün politikası | unknown; izin false |
| Dönem kenarı | Pencerenin dahil sağ ucu ve ortak olay için dışlama/embargo kararı | İşaretler ve testler mevcut; politika açık |

Pozitif 1, kabul edilen yeni olayın ilk tespitinin hedef penceresine ve
kabul edilen hedef hücresine ait olduğuna dayanmalıdır. Negatif 0 için
hem kabul edilmiş gözlem yeterliliği hem ilgili olay yokluğu gerekir.
Diğer durumlar bilinmeyen/hedefi atanmamış kalır. Az sayıda olumlu vaka
incelemesi bütün negatif günleri doğrulamış sayılmaz. Bilimsel kabulün
tarih, gerekçe, kanıt ve sürümü kaydedilir; kod testi uzman onayı yerine geçmez.

## Son kabul denetimleri

1. Her kaynak parçasının manifest/hash'i ve veri ayrımı eşleşir.
2. Anahtar sayıları takvim/grid envanteriyle eşleşir; kayıp/tekrar ve
   dışlamalar nedenleriyle açıklanır.
3. Dinamik özellik çekim/pencere tarihleri T'den sonrasını içermez.
   Tarihsel `available_at` bilinmiyorsa geriye dönük kullanım sınırı korunur;
   gerçek zaman ürününün erişilebilirliği kabul edilmiş sayılmaz.
4. Kaydedilen birleştirme kaynak sütunlarıyla ayrı geri okuma yolunda
   eşleşir; NaN yerleri ve destek alanları korunur.
5. Hedef için bilimsel kapılar kapanmış, bilinmeyen/0/1 sayıları ve
   kapsanan/dışlanan alan-dönem dağılımları ayrı raporlanmıştır.
6. Train/validation arasında aynı nihai olay yoktur; dönem penceresi
   sınırı incelemesi çözülmüştür. 2025 verisi kullanılmamıştır.
7. Feature listesi, etiket politikası, kaynak/kod/ortam sürümü ve parça
   hash'leri freeze manifestinde tutulur. Öğrenilen dönüşümler veri hazırlığı
   dosyasına gizlice fit edilmez; model foldunun içinde yürütülür.

Bu kabul tamamlandıktan sonra temel model karşılaştırmasına geçilir.
Hedef olay doğruluğu ve negatif gözlem politikası çözülmeden yüksek bir
model skoru veri setini veya operasyonel ürünü doğrulamaz.

## Beklemeden tamamlanan ve bekleyen işler

Tamamlanan hazırlık: dört gün özellik birleştirmesi, hedef zaman/split
kontrolleri, 15 habitat duyarlılık senaryosu, tam destek envanteri,
izlenebilir zor vaka paketi ve bu kabul taslağı.

Bekleyen kanıt: çalışan kuyrukların kalan kaynakları ve bağımsız sonuç
geri okuması; uzman/danışmanla habitat/olay vakalarının değerlendirmesi;
NASA teknik teyidi; gözlem/negatif politikasının bilimsel kabulü. Bekleyen
kanıtlar bu taslakta yapılmış gibi işaretlenmez.
