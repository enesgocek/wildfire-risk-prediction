# Birinci aşama karar dosyası — mevcut kanıt ve teslim bağımlılıkları

22 Kasım 2026. Bu dosya [18 Kasım kabul incelemesini](STAGE_ONE_ACCEPTANCE_REVIEW_2026-11-18.md)
sonraki onaylı pilotlarla birlikte değerlendirir; eski sonuçları
değiştirmez. **Karar dosyası hazır, birinci aşamanın bilimsel geçişi
kabul edilmiş değil.** Yeni eğitim, hedef/etiket üretimi, renk seçimi
veya nihai birleştirme yapılmadı.

## Karar için kısa sonuç

**23 Kasım sonraki kanıt notu:** FWI kıyası, 44.082 satırlık
incelenebilir deneysel paketin teknik/kullanıcı kontrolü ve sabit
dokuz XGBoost karşılaştırması artık tamamlandı. Bunlar aşağıdaki
22 Kasım durumunun sonrasıdır; tarihsel sonuçlar değiştirilmedi.
XGBoost ayrı Mersin'de dokuz ayarda, dört il genelinde üç ayarda
eski doğrusal skoru geçti; yakın gün/yön sınırları ve üç bilimsel
koşul devam ediyor. [Yeni deney ve denetim](NONLINEAR_RANK_RESULTS_2026-11-23.md),
[mevcut veriye dayalı yöntem taslağı](research/DATASET_METHODS_DRAFT_2026-11-23.md)
karar için hazır. Sırf daha yüksek skor bulmak için yeni modeller
eklemek yerine bu kanıtla kapsam/varsayım değerlendirmesi yapılmalı.
Teknik inceleme sürümü hazır; bu not bilimsel geçiş onayı değildir.

Özellik hazırlığı, zaman/anahtar denetimleri ve sınırlı yardımcı
deneyler mevcut. Ana 24 saatlik yeni orman/çalılık yangını riskini
değerlendirecek kaynak/PU dayanağı hâlâ açık. Bugünkü öneri bu
çıktıları doğrulanmış yangın riski diye yayımlamamak, FWI edinimi
gelirse yalnız referansın uygunluğunu incelemek ve 26–29 Kasım'da
bu üç açık konu için gerekçeli geçiş/kapsam kararını sunmaktır.

Bu, bütün kayıtların kusursuz olması gerektiği anlamına gelmez.
İlk uydu tespitinin gerçek tutuşma zamanı olması istenmiyor;
mevcut gözlenebilir proxy hedefi korunuyor. Gürültülü pozitifler
ve belirsiz koordinatlar gerekçeli bir protokolle araştırılabilir.
Eksik olan, hangi varsayımlarla hangi sonucun savunulabildiğinin
ve nasıl değerlendirilebildiğinin kabul edilmiş sözleşmesidir.

## Üç bilimsel geçiş konusu

| Konu | Desteklenen hazırlık | Varsayılan veya açık kalan | Bugünkü durum |
|---|---|---|---|
| Yeni olay, ilk hücre/gün ve orman/çalılık üyeliği | Başlangıç geçmişini koruyan izleme; dokuz ayar; iki tarihsel örtü haritası; sınırlı ham/görsel kaynak kontrolleri | Fiziksel olay kimliği, kaynak koordinatı/saatinin anlamı ve hata sınırı; karma yerel örtünün kabul kuralı | Geniş kaynak kümesine gerçek Y veya kabul edilmiş L atama açık |
| Hata içerebilen pozitiflerle PU hedefe aktarımı | Somut protokol ve 15 dinamik alanla sınırlı sıralama pilotları | Pozitif seçimi/gürültü koşullarının gerçek hedef sıralamasını koruması; oran veya gerekçeli belirsizlik sınırları | Ana araştırma yöntemi kabul edilmedi |
| Gerçek hedefin değerlendirme dayanağı | Ayrı Mersin kaynağıyla 2.329 tam-girdi aynı-hücre/ay çifti; ayrı hesaplar | Kaynağın kapsamı ve hedef anlamı; güçlü aktarım yok, 2022 daha önce görülmüş yıl | Gerçek yangın AP'si veya kör final başarımı kurulmadı |

Düşük yardımcı AUC tek başına PU yaklaşımını matematiksel olarak
çürütmez, kaynağın yanlışlığını kanıtlamaz veya otomatik bir durma
eşiği değildir. Buna karşılık yüksek yardımcı AUC de bu üç konuyu
kendiliğinden kabul ettirmez. Önceden kabul edilmiş böyle bir sayısal
geçiş eşiği yok; burada yeni eşik icat edilmedi.

## Sonraki pilotların verdiği ölçülebilir bilgi

- [44.082 anahtarlık X/QA hazırlığı](SOURCE_CALENDAR_FEATURE_PREPARATION_2026-11-21.md)
  tamamlandı; bu, kaynak koşullu özel inceleme tablosudur.
- [Dokuz günlük doğrusal pilotta](TEMPORAL_PAIRWISE_RESULTS_2026-11-21.md)
  yardımcı aynı-hücre/ay AUC 0,585685–0,595230; 1–3 gün aralığında
  0,520107–0,541187. Değerlendirme çiftleri bağımsız yangın değildir.
- [Ayrı Mersin takviminde](CROSS_SOURCE_CALENDAR_RESULTS_2026-11-21.md)
  aynı dokuz model değişmeden 2.383 tarihte incelendi; 2.329 çiftte
  0,522542–0,540575, yakın tarihlerde 0,450000–0,465909. Kaynak
  anlamı belirsizken bunu gerçek yangın doğruluğuna çeviremeyiz.
- Korunmuş tespit geçmişine göre kesitler, düşük günlük ayrımın
  yalnız gözlenen devam kayıtlarından kaynaklandığını göstermedi.
  Yedi gün sessizlik veya kayıt yokluğundan gerçek negatif üretilmedi.

Bu sayılar önceki sabit deneylerin sonuçları; 22 Kasım'da modeller
yeniden çalıştırılmadı. Kırmızı/sarı/yeşil sunum yönü seçilmiş olsa
da [kayıtlı ürün kararı](../configs/relative_risk_product_direction_v1.json)
doğrulanmamış kaynak skorunu gerçek yangın riski diye yayımlamaya
izin vermiyor.

## Bugün yapılan ayrı teknik iş: özellik dosyası metadata envanteri

Kabul edilmiş `waiting_features_v1` dosya dizini hash ile doğrulandı.
Yalnız kayıtlı gün, tür, yol, boyut ve dosya varlığı incelendi.
Günlük özellik/provenance içerikleri veya 2023–2025 bilimsel
değerleri okunmadı; günlük içerik hash'leri yeniden hesaplanmadı.

| Bu doğrulanmış dizindeki yıl | Gün | Özellik CSV | Provenance CSV | Eksik dosya / boyut uyuşmazlığı |
|---|---:|---:|---:|---:|
| 2018 | 365 | 365 | 365 | 0 / 0 |
| 2019 | 365 | 365 | 365 | 0 / 0 |
| 2020 | 366 | 366 | 366 | 0 / 0 |
| 2021 | 365 | 365 | 365 | 0 / 0 |
| 2022 | 365 | 365 | 365 | 0 / 0 |
| 2023 | 365 | 365 | 365 | 0 / 0 |
| 2024 | Bu dizinde yok | — | — | Bu dizin kapsamında değil |
| 2025 | Bu dizinde yok | — | — | Bu dizin kapsamında değil |

Toplam **2.191 gün / 4.382 dosya** mevcut ve kayıtlı boyutla uyumlu.
Aynı boyuttaki bir dosyanın içeriği değişmiş olabilir; boyut kontrolü
güncel içerik hash'i yerine geçmez. Bu sonuç son parça kabulü değildir.
2024/2025 satırları diskin veya dış sağlayıcıların eksiksiz envanteri
değil; **mevcut hazır dizinin bu yılları kapsamadığını** gösterir.
Dosya adında 2024 bulunan bir FIRMS arşivi de meteoroloji/bitki örtüsü/
gözlem/etiket parçalarının birlikte hazır olduğunu kanıtlamaz.

Teslim planında 2024 değerlendirme girdilerinin, gerekiyorsa ayrıca
hazırlanmasının maliyeti görünür tutulmalı. 2025'in kayıtlı final
erişim koşulları korunur; bu envanter final testi açmadı. 2023'ün
dosyalarının varlığını görmek, kalibrasyon değerlerini açma izni değil.

## İkinci aşamaya ve birleştirmeye geçmeden önce

1. Ana araştırmada kullanılacak üyelik/PU ve değerlendirme protokolü
   gerekçeli biçimde karara bağlanmalı. Kullanıcı tercihi bağımsız
   doğrulama sayılmayacak; varsayımlar açık yazılacak.
2. Ancak bu protokolle hedef/model satırlarının kapsamı ve mevcut
   özellik parçaları hazırlanabilir. İnceleme amaçlı X bağları nihai
   etiketli birleştirme olarak sunulmayacak.
3. Meteoroloji, arazi/örtü, bitki örtüsü, gözlem ve hedef parçaları
   güncel hash/anahtar/şema/eksiklik/zaman/split denetimiyle ayrı
   incelenecek. Bugünkü metadata sayımı bu kontrolün yerine geçmez.
4. Son kontrol raporunun kimliğine bağlı açık kullanıcı onayından
   sonra aynı parçalar birleştirilebilir. Mevcut nihai birleştirme
   politikası ve `require_final_merge_approval` koruması değişmedi.

## FWI beklenirken ne yapılabilir, neyi çözmez

Karar dosyasının bu sürümü FWI'ye bağlı olmadan tamamlandı.
Kullanıcı henüz dosyayı indirmediğini ve edinim adımını yapacağını
bildirdi; hazırlanmış giriş klasörü bu kontrolde de boştu.
Dosya gelince [hazır başlık okuyucusu](FWI_REFERENCE_PILOT_2026-11-21.md)
ile sınırlı inceleme yapılabilir. FWI; olay etiketi, kayıt kapsamı,
gerçek yeni yangın AP'si veya operasyonel tahmin erişimi kanıtı değildir.

26–29 Kasım karar incelemesinde olası yöntem/teslim seçenekleri,
ana hedefi koruyarak hangi varsayımlarla ilerlenebildiği ve hangi
iddiaların desteklenemediği üzerinden araştırmacıya sunulacak.
Yeni kurumsal yazışma, hedef değişikliği veya koşullu bir teslim
yönü burada kendiliğinden seçilmedi. Aynı tür küçük modeller sırf
daha yüksek sonuç aramak için çoğaltılmayacak.

## Tekrarlanabilirlik ve sınır

- Üretici: `scripts/quality/audit_delivery_readiness_metadata.py`.
- Yeni yerel makbuz:
  `outputs/reports/dataset/delivery_readiness_metadata_v1/20261122T111335Z_6aba3549/readback.json`.
  SHA-256 `ee92667192b0ec173b2f7f20f601f636f2d54b485e82d9a3b050dddc5ba5d919`.
- Aynı klasörde `verified_feature_index_by_year.csv` ve
  `daily_artifact_stat_inventory.csv` bulunuyor; kaynak dosyalar
  değiştirilmedi. Eski makbuzların hash'i doğrulandı; onların bütün
  bilimsel girdileri yeniden denetlenmiş sayılmadı.
- İçerik okumayan envanter, eksik dosyanın açık raporlanması,
  yinelenen kayıt ve dizin dışı yol reddi için üç yeni test geçti.
  Bunlar gerçek etiket/insan veya saha doğrulaması değildir.

Sonuç: metadata/kabul karar hazırlığı tamam; bilimsel geçiş, ana
risk başarımı ve nihai veri seti kabulü hâlâ açık.
