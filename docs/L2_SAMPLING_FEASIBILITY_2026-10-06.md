# Daha küçük uydu işleme kapsamı — 6 Ekim 2026

**Sonuç:** Eğitim tarihlerini örneklemek işlem yükünü belirgin azaltabiliyor.
Modelin bu kapsamla yeterli olacağı henüz kanıtlanmadı. Bu inceleme yerelde
yapıldı; VM başlatılmadı, yeni ham uydu verisi indirilmedi, etiket üretilmedi.
Daha küçük kapsamın yeterliliğini ölçmeyi ve gerektiğinde tam döneme dönmeyi planladım.

## Ölçtüğümüz seçenekler

2018–2023'ün **her yıl ve her ayında** 7/14/21 gün seçildi. Aylık başlangıç
günü sabit tohumla (20261006), yangın sonuçlarını hesaplamadan önce belirlendi.
Ay sonundan taşan blok aynı ayın başına sarılıyor; dolayısıyla her günün
seçilme olasılığı k/ayın gün sayısı. Sarma iki ayrı takvim parçası oluşturabilir.
7 günlük seçim 14'ün, 14 günlük seçim 21'in alt kümesi; genişlerken önceki
günler korunuyor. Her hedef gün dört ilin **2.899 hücresini** içerir.

Sınırdaki geçişler için kaynak planına önceki/sonraki gün eklendi. Bu ±1 gün
henüz doğrulanmış üretim/zaman sınırı kuralı değildir; maliyet tamponudur.
2017/2024'e taşan günler raporlandı, eğitim girdisi olarak okunmadı.
Tamamlanmış Temmuz 2023 çiftleri yeni işlem hesabından çıkarıldı.

| Eğitim seçeneği | Hedef gün | Kaynak günü, tamponla | Kalan çift | Yeni kaynak tahmini | Salt çift evresi | Çift yükünde azalma |
|---|---:|---:|---:|---:|---:|---:|
| Ayda 7 gün | 504 | 666 | 5.596 | 1.027 GB | 59,40 saat | %69,65 |
| Ayda 14 gün | 1.008 | 1.183 | 9.942 | 1.825 GB | 105,54 saat | %46,09 |
| Ayda 21 gün | 1.512 | 1.674 | 14.091 | 2.587 GB | 149,58 saat | %23,59 |
| Tam dönem | 2.191 | 2.191 | 18.441 | 3.386 GB | 195,76 saat | — |

GB ondalıktır; bunlar **bulutta aktarılacak ham kaynaklar**, yerel/Drive'da
kalıcı arşiv değildir. Katalog boyutları tahmindir. Süreler altı yaz çiftinin
iki işçiyle ölçülen hızından hesaplandı; günlük geometri birleşimi, Drive,
retry, geliştirme, 2024 doğrulaması ve 2025 final değerlendirmesi dahil değil.
Tam dönem satırı eğitim dışı zaman sınırı eklerini de içermez. Maliyet tabanı
nominal çiftlerdir; seçilen kapsamlarda 84/157/221 eşleşmemiş kayıt ayrıca
korunuyor ve incelenmeden kullanılmıyor. Bütün katalogda bu sayı 283.

## Veri kaybını ve temsili nasıl ölçtük?

- 30.295 eğitim adayı tespitten 7/14/21 günlük seçeneklerde
  **7.951 / 11.271 / 14.414** kalıyor. Bunlar bağımsız yangın sayısı değildir.
- Dokuz mevcut, henüz kesinleştirilmemiş olay gruplama kuralında korunan ilk
  tespit sayıları sırasıyla **1.402–1.999 / 2.841–3.863 / 4.273–5.834**.
  Gruplama ayrı yangınları birleştirebilir; bu aralık gerçek yangın sayısı veya
  güven aralığı değildir. Tam FIRMS ve bütün gruplama dosyaları korunuyor.
- Tespit olan hedef günlerin tamamını tutmak 1.800 güne, dokuz kuralın bütün
  ilk tespit günlerini birlikte tutmak 1.773 güne çıkıyor. Kontrol/tampon günleri
  eklenmeden bile yükte yalnızca yaklaşık %17–18 azalma sağlıyor.
- Günlük uygun hücrelerin sıcaklık, rüzgâr, haftalık yağış ve toprak nemi
  bölge ortalamaları karşılaştırıldı. Örnekleme ağırlığıyla en büyük
  standartlaştırılmış ortalama farkı 7 günde **0,0963**, 14 günde **0,0200**.
  Bu yakınlık hücre düzeyinde veya model başarısında eşdeğerlik kanıtı değildir.
  Eğitim meteorolojisinin 2.191 dosyası kaynak SHA ile yeniden eşleşti.
- 2017 doğal bitki payına göre dört tanısal sınıfın hepsinde aday tespit kaldı.
  52 adet 50 km blokta başlangıçta aday bulunuyordu; 7 günde 4, 14/21 günde
  2 blokta seçilen günlere aday düşmedi. Bu alanlar veri kapsamından çıkarılmadı.
  7 günlük seçimde Şubat 2018'in adayları seçilen tarihlere düşmüyor;
  14/21 günlük seçimde aday bulunan bütün yıl-aylarda aday korunuyor.
- Tamamlanmış Temmuz üzerinde bulut alan payı ortalaması tam ayda %6,97,
  7 günde %7,39, 14 günde %13,31. Daha çok örnek her ölçümü otomatik olarak
  iyileştirmiyor. Bu tek ayın merkezi/alan/zaman tanılarıdır; güvenilir negatif
  etiket veya diğer yılların kapsam kanıtı değildir.
- 100 başka tohumla seçim duyarlılığı ölçüldü; öneri tohumu değiştirilmedi.
  7 günlük seçimlerde aday tespit sayısının %5/%95 tasarım yüzdelikleri
  yaklaşık 2.857/13.810: büyük yangın günleri sonucu güçlü etkiliyor.
  Bu yüzdelikler istatistiksel güven aralığı değildir.

Hedef `(T,T+24h]`: tam 00:00 UTC tespiti önceki hedef güne aittir. Bu nedenle
1.801 takvim tespit günü ile 1.800 hedef günü farklıdır. Kesin il bazında
sayım için il sınırları ayrıca gerekli; birleşik AOI'den il adı tahmin edilmedi.
Meteoroloji ve bitki örtüsü uygunluğu nihai negatif etiket değildir.

## Önerilen karar yolu

1. **7 günlük kapsamı küçük deneme, 14 günlük kapsamı genişleme seçeneği olarak
   tut.** Henüz bütün 504/1.008 günün üretimini başlatma. İlk yeni doğal ürün
   kontrolünü farklı eğitim yılları/mevsimlerinde sınırlı kapsamla yap; tam
   günün beklenen çiftlerini, zaman sınırlarını, bulut/eksik gözlemi denetle.
2. Olay/örtü/gözlem kullanım kurallarını ve NASA Type belirsizliğini çözüp
   sürümle. Bilinmeyen kayıtları negatif yapma. Seyrek yıl-ay/il/alanlardaki
   örnek kaybını ayrıca değerlendir; gerekiyorsa kapsamı açıkça genişlet.
3. Geçici karşılaştırmada 2018–2022 ile eğit, **aynı sabit 2023 holdout**
   üzerinde küçük ve büyük kapsamı karşılaştır. Olayların fold sınırlarını
   aşması için ayırma/purge kuralı gerekir; hücreleri rastgele bölme.
   Holdout tarihleri, kabul edilebilir performans farkı ve zaman/mekân
   gruplarına uygun belirsizlik hesabı sonuçlara bakmadan sabitlensin.
   PR başarısı, yangın yakalama ve olasılık kalibrasyonu birlikte incelensin.
   [Öğrenme eğrisi yöntemi](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.learning_curve.html).
4. Daha büyük kapsam anlamlı iyileşme sağlıyorsa 14 → 21 → tam döneme çık.
   Yetersizliğin nedenini ayır: veri sayısı, eksik gözlem, etiket veya model
   sorunu farklıdır; hepsi daha fazla indirmeyle çözülmez.
5. 2024 doğrulamasında sınıf oranını yapay şekilde dengeleme; ayrı ve mümkün
   olduğunca tam dönem planını koru. 2025 kapalı kalır. Tarih seçimi ağırlığı
   bulut/eksik veri yanlılığını kendiliğinden düzeltmez.

Hiçbir üretim kapsamı/VM süresi/ödeme ayarı bu incelemeyle değiştirilmedi.
Ücretsiz krediyi tamamen tüketmek hedef değildir; gerektiğinde
tam dönem seçeneğine dönülmesi benimsendi, ücretli yükseltme yasağı sürüyor.

## Dosyalar ve doğrulama

Üretilebilir inceleme: `scripts/cloud/assess_l2_sampling.py`.
Yerel JSON ve 11 CSV: `outputs/reports/observation_coverage/sampling_feasibility/`.
Kaynak/analiz/çıktı SHA'ları `assessment.json` içinde. Bağımsız geri okuma
tarih/olasılık/iç içe kapsam, kaynak dosyalarından boyut ve 27 ilk-tespit
sayımı ile meteoroloji ortalamalarını doğruladı: `independent_readback.json`.
15 koruyucu test geçti; Ruff kod/biçim kontrolü başarılı.
İlk inceleme ve tam yerel model yeterliliği farklı kapılardır; raporda
`model_sufficient=null`, `negative_label_permitted=false` kalır.
