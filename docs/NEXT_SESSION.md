# Kısa devam kaydı

Güncelleme: 22 Kasım 2026. Bu dosya durum/kontrol sırasıdır;
yeni yetki, otomatik görev veya bilimsel kabul makbuzu değildir.
AGENTS.md, STATUS ve araştırma sözleşmeleri geçerli.

## İlk yapılacak iş

1. Mevcut tarih ile [kesinti paylı planı](DELIVERY_PLAN_REVIEW_2026-11-22.md)
   karşılaştır. 26–29 Kasım karar hedefi geçmişse yeni küçük model
   eklemekten önce karar/gecikme incelemesini sun. Mevcut
   [birinci aşama karar dosyası](STAGE_ONE_DECISION_PACKET_2026-11-22.md)
   hazır; bunu yeniden sıfırdan üretme. Üç bilimsel kapı açık.
2. `data/raw/external/cems_fwi_pilot_v1/` içindeki kullanıcı
   teslimini kontrol et. 22 Kasım'da klasör boştu; kullanıcı henüz
   indirmediğini, giriş/indirme adımını yapacağını bildirdi.
3. Özgün dosyayı değiştirmeden kimlik/boyut/türünü incele. Yalnız
   gerçek Haziran 2022 bölgesel `.nc` için
   `scripts/quality/inspect_fwi_reference_metadata.py --file <gerçek yerel dosya>`
   kullan. Üst sınır 32 MiB; ZIP veya başka tür doğrudan bu okuyucuya
   verilmez. Kısmi/yanlış dosya ve kaynak baytları korunur.
4. Başlık, değişken ve zaman tanımı uygun değilse değerleri açıp
   modele katma. Nominal zaman yayımlanma/edinim zamanı değildir.
   FWI referansı, gerçek yeni yangın etiketi veya olasılığı değildir.
5. Sonucu tarihli rapor, STATUS ve o günün Diary kaydına bağla.
   Yeni bilimsel yön veya insan değerlendirmesi gerekiyorsa somut
   bulgu ve gerekçeli seçenek sun. Nihai birleştirme kapısını koru.

Dosya yoksa yeni indirilmiş gibi ilerleme. Referans edinimini
beklemek, mevcut kanıtla birinci aşama karar dosyasının hazırlanmasını
engellemez; [plan incelemesindeki üç açık kapı](DELIVERY_PLAN_REVIEW_2026-11-22.md#birinci-aşamanın-üç-geçiş-koşulu)
esas alınır. Giriş/parola/anahtar dosyalarını tarama veya yazdırma.

## Tekrar yapılmayacak tamamlanmış işler

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
