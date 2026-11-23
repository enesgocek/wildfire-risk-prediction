# Kısa devam kaydı

Güncelleme: 23 Kasım 2026. Bu dosya durum/kontrol sırasıdır;
yeni yetki, otomatik görev veya bilimsel kabul makbuzu değildir.
AGENTS.md, STATUS ve araştırma sözleşmeleri geçerli.

## İlk yapılacak iş

Öncelik: [sabit XGBoost günlük sıralama önerisi](NONLINEAR_RANK_PROPOSAL_2026-11-23.md)
araştırmacıya A/B olarak sunuldu; yanıtı kontrol et. Henüz yeni
eğitim veya kurulum izni yok. A seçilirse ayrı yürütme kararıyla
en fazla dokuz model, 2018–2021 öğrenme / mevcut iki 2022 incelemesi;
3.4.1 bağımlılık kurulumu ve uyum kontrolünden sonra 15 dakika
yerel CPU sınırı uygulanır. Öneri dosyasını geçmişe dönük izin
makbuzu olarak değiştirme; yeni yürütme kaydı kullan. B seçilirse
eğitim açmadan mevcut veri/sonuçlarla yöntem yazımı sürer.
Hazırlık makbuzu `nonlinear_rank_preparation_v1/20261123T131121Z_14674f77/readback.json`,
SHA `cda37ee7be3820cc1396e939f7eeef78799ae262f21103da3029edd4710454c9`.
Girdi desteği tamam; yeniden çıkarma. Kaynak koşullu sıra öğrenmesi
gerçek yangın PU riskinin bilimsel kabulü değildir.

0. Açık A ile deneysel paket ve kullanıcı ekran kontrolü tamam:
   [kullanım/denetim/kapanış kaydı](EXPERIMENTAL_SU_PACKAGE_2026-11-23.md).
   Paket dizini `experimental_SU_inspection_v2/20261123T102954Z_6d6e52c1`:
   44.082 satır, yıl 2022 filtresi 6.573, ayrıca S grubu 242 (ayar: tümü).
   Araştırmacı doğru v2 sayfasındaki kontrolleri doğruladı; tekrar
   aynı ekran onayını isteme. Tarayıcı aracının file protokol reddini
   alternatif yüzey/dolaylı yürütmeyle aşma.
   Bu ekran yanıtı bilimsel/etiket/final merge onayı değildir.
   Dosyaları yeniden üretme; gerekirse yeni düzeltme sürümü kullan.
1. Mevcut tarih ile [kesinti paylı planı](DELIVERY_PLAN_REVIEW_2026-11-22.md)
   karşılaştır. 26–29 Kasım karar hedefi geçmişse yeni küçük model
   eklemekten önce karar/gecikme incelemesini sun. Mevcut
   [birinci aşama karar dosyası](STAGE_ONE_DECISION_PACKET_2026-11-22.md)
   hazır; bunu yeniden sıfırdan üretme. Üç bilimsel kapı açık.
2. NetCDF ve GRIB teslimi/kontrolü tamam; yeniden indirme veya aynı
   kalite koşularını tekrarlama. [23 Kasım zaman ve eşitlik incelemesi](FWI_LOCAL_TIME_REVIEW_2026-11-23.md)
   güncel kayıttır. Genel GDAL geçerli zaman 0 ve ilk 00–21 enumerasyonu
   bilimsel zaman kanıtı değildir. Artım düzeltme makbuzu esas alınır.
3. Araştırmacının sonraki devam talimatıyla önerilen sınırlı FWI
   kıyası tamamlandı. [Sonuç ve bağımsız kontrol](FWI_REFERENCE_RESULTS_2026-11-23.md):
   203 sonlu anahtar, 196 çift, FWI 0,637755; dokuz eski skor
   0,612245–0,642857. Gerçek yangın veya operasyonel kabul değil.
   Aynı işi yeniden çalıştırma veya yeni veri isteme.
4. [Sonraki kapsam dosyasında](STAGE_ONE_NEXT_SCOPE_2026-11-23.md)
   açık A seçimiyle deneysel S/U hazırlığı tamamlandı. Ana hedef
   araştırma sorusu olarak korundu; gerçek yangın veri kabulü veya
   final merge olmadı. Üç bilimsel boşluk ve yeni eğitim/deney
   kapsamı ayrı değerlendirilir; yeni yetki çıkarma.
5. Sonucu tarihli rapor, STATUS ve o günün Diary kaydına bağla.
   Yeni bilimsel yön veya insan değerlendirmesi gerekiyorsa somut
   bulgu ve gerekçeli seçenek sun. Nihai birleştirme kapısını koru.

Referans incelemesinin bitmesi, ana yöntemin bilimsel geçişi değildir;
[plan incelemesindeki üç açık kapı](DELIVERY_PLAN_REVIEW_2026-11-22.md#birinci-aşamanın-üç-geçiş-koşulu)
esas alınır. Giriş/parola/anahtar dosyalarını tarama veya yazdırma.

## Tekrar yapılmayacak tamamlanmış işler

- Deneysel paket: 44.082 anahtar/27 özellik ve dokuz mevcut öneri.
  Paket SHA `86270dea5d9d12a1764ead780dcfa79166bed60a0977bf712e3df497d84bc366`;
  ayrı veri/arşiv audit SHA `85fb7ac20f5d3e0564fe2ec66a5e4801f469d5c860cd5933b6a17e5be6c74356`.
  Tam dizinler raporda. Kullanıcı ekran kontrolü alındı; kapanış SHA
  `8dbadb81ebfd4537f620d8a571a46523c5e593cbd49ac6d68ec5665379978d06`.
- FWI 203 satır / 196 çift kıyası, ayrı örnek/çift/50 özet/70 hücre
  denetimi ve yerel MLflow kapanışı tamam. Sonuç makbuzu
  `fwi_reference_comparison_run_v1/20261123T101431Z_805e6449/readback.json`,
  SHA `5e5a7bd7a920b15d1288c7969b9841c62ac9948af5e74255c901ff6eb5a4d40c`.
  Audit ve kapanış hash'leri raporda; yerel run
  `08392c8a196648e29a09574452ccb21d`. Bir nominal gün kaydırması
  yalnız bu karşılaştırma için kullanıldı; operasyonel model girdisi değil.
- GRIB/NetCDF 1 Haziran: 873 sonlu değer ve 156 eksik maske birebir.
  Güncel zaman yorumu `fwi_increment_interpretation_v1/20261123T002508Z_5c7204e9/readback.json`,
  SHA `befa8ecc8e7da5dbc580aa379530ba3ea0426879f2b5411c74a525b86e236ea3`.
  İlk saat enumerasyonu kabul edilmedi; yayımlanma saati bilinmiyor.
  Karşılaştırma planı `fwi_reference_comparison_plan_v1/20261123T002128Z_66578e13/readback.json`,
  SHA `d8326d3bd0b54a5b95cdf66e5309b6e6138e7b49f6a06574ba8c37f26b67bdbf`.
- Haziran 2022 NetCDF: 30 bant/49 × 21, 26.190 sonlu ve 4.680 eksik
  nokta-gün; negatif/maskelenmemiş NaN/sonsuz 0. Özgün dosya SHA-256
  `e6b57e8ecbd5836f141eb6d0cbd17dc283d6569bb194c5496861d4ba8e5f5a8e`.
  `fwi_received_quality_v1/20261122T165059Z_42a37e1b/readback.json`
  SHA-256 `a66cdd0f6cdcdd74e1d195a6285eb73d003f775a2e59c6de7667a93ac476bc13`.
  Başlık makbuzu ve 36 testin kapsamı raporda. Nominal zaman kabulü açık;
  gerçek GRIB kontrolü veya FWI model karşılaştırması henüz yapılmadı.
- 44.082 anahtarlık kaynak koşullu X/QA incelemesi tamam.
  `source_calendar_feature_review_v1/20261121T164603Z_741c2896/readback.json`
  SHA-256: `b718ed5d7ff492ddaf6d5217e7f88b3f62a6024a9d2138f4225154b3e3576040`.
- Dokuz gün-farkı doğrusal model ve ayrı denetimleri tamam.
  `temporal_pairwise_run_v1/20261121T174415Z_5a77b21e/readback.json`
  SHA-256: `b8e847f8d510721ce84b788161ae40ac5f3bfa098154b0e56a013fc380f83d82`.
- Ayrı Mersin takvimindeki 2.383 X ve dokuz sabit-model sınaması tamam.
  `cross_source_fixed_model_run_v1/20261121T181438Z_bc972c9e/readback.json`
  SHA-256: `a4fb83beea02226eca149c5ca8a0383326a1db0143b2ca395adbc50a1e6ab6f9`.
- Ayrıntılı sonuç/denetim/MLflow kimlikleri ilgili raporlarda;
  yukarıdaki üç temel makbuz 22 Kasım'da yeniden hash ile eşleşti.
- Günlük ve farklı-kaynak sıralama zayıflığı açık. Yeni denemeler,
  yalnız yüksek bir sayı aramak amacıyla otomatik çoğaltılmaz.
- 22 Kasım metadata envanteri: hazır özellik aday dizinindeki 2.191
  gün/4.382 dosya yerinde ve kayıtlı boyutta. 2024/2025 bu dizinde
  yok; bütün disk/sağlayıcı envanteri veya içerik hash kontrolü değil.
  `delivery_readiness_metadata_v1/20261122T111335Z_6aba3549/readback.json`
  SHA-256: `ee92667192b0ec173b2f7f20f601f636f2d54b485e82d9a3b050dddc5ba5d919`.

Yollar `outputs/reports/dataset/` altındadır. Girdi/kod değişikliği
görülürse eski tamamlanmayı yeni sürüme taşımadan önce farkı incele.
Makbuzlar ve eski sonuç CSV/JSON'ları elle düzeltilmez.

## Sabit sınırlar

Ana hedef dört ilde 5 km hücre için sonraki 24 saatlik yeni orman/
çalılık yangını ilk tespit riski. `daily_observation_status=unknown`,
`negative_label_permitted=false`; gerçek Y ve kabul edilmiş L açık.
2023/2024/2025 bilimsel değerlerini açmaya yeni izin bu dosyadan
doğmaz. Yeni fit, üretim ayarı/risk rengi, ücretli bulut veya yeni
yazışma başlatma. Son parça raporuna bağlı nihai birleştirme onayı yok.
