# Kaynak koşullu takvim kontrolünün özellik hazırlığı

21 Kasım 2026. Araştırmacının önerilen hazırlık sonrası devam
talimatıyla, [ayrı takvim kontrolünün](SATELLITE_PU_ABLATION_RESULTS_2026-11-21.md)
yerel özellik/zaman/eksiklik hazırlığı başlatıldı. Kayıt bu devam
talimatına dayanıyor; yeni yardımcı model, S üyeliği, gerçek Y/L
veya nihai birleştirme onayı değildir.

## Sabit kapsam

Dokuz ayarın olası adaylarının bulunduğu 1.443 hücre–yıl–aydaki
bütün uygun günler korunuyor: 44.082 anahtar; 37.509 fit-rolü /
6.573 adet 2022 inceleme-rolü. Bu rol adları eğitim izni değil.
Tahmin zamanı 00:00 UTC ve hedef pencere (T,T+24 saat]; dönem
sonuna taşan 31 Aralık 2021/2022 günleri kullanılmıyor.
2018–2022 dışındaki günlük bilimsel değerler açılmıyor.

Aday günü çıkarılmıyor. Aday olmayan gün yangın yok yapılmıyor;
gerçek hedef ve kabul edilmiş L boş, günlük gözlem durumu unknown.
Özgün 2.048 U ve edinim ağırlıkları değişmeden kendi kaynaklarında
korunuyor. Havuz kaynak koşullu olduğundan dört ilin bütün hücre/
günlerini temsil eden veya operasyonel/kör değerlendirme sayılmaz.

## Kontrol ve devam düzeni

1.824 günün 3.648 özellik/provenance dosyası güncel hash ile okunuyor.
27 X sütunu, tam anahtar evreni, statik kaynak eşitliği, meteoroloji
ve bitki örtüsünün geçmiş pencere/eksiklik kuralları denetleniyor.
Kaynakların yayın erişim zamanı belirsizliği korunuyor; ERA5 yeniden
analizi anlık operasyonel veri diye sunulmuyor. Yeni doldurma veya
imputasyon yapılmıyor.

Her ayın X ve provenance CSV'si ayrıca geri okunup hash'li makbuzla
korunuyor. Ay makbuzları ve tamamlanmış dosyalar değiştirilmiyor.
Geçici çalışma durumu atomik kaydediliyor. Devamda aynı kod/ayar/
girdi kimliği ve tamamlanmış aylar doğrulanıyor. Kesintide eksik
ay yeniden okunabilir; tamamlanmış aylar tekrar hesaplanmıyor.
Son X/QA/metadata dosyaları sürümlü bir snapshot klasörüne yazılacak;
bu inceleme snapshot'ı nihai etiketli veri seti değildir.

İlk koşu kimliği:
`outputs/reports/dataset/source_calendar_feature_review_v1/20261121T164603Z_741c2896`.
Üretici `scripts/quality/prepare_source_calendar_features.py`, karar
`configs/source_calendar_feature_preparation_v1.json`. Tek yerel
parça 15 dakika sınırında duraklayabilir; tamamlanan aylarla aynı
oturum içinde devam edilebilir. Bu zamanlanmış iş veya bulut görevi değil.

Özellik hazırlığı tamamlandıktan sonra
`scripts/quality/verify_source_calendar_features.py` ayrı snapshot,
geçmiş zaman, ay/gün/anahtar korunumu ve önceki 1.689 X/QA kaydının
birebir eşitliğini kontrol edecek. Aynı hücre/ay içinde değişen
meteoroloji bilgisi ve eksiklik desteği sayılacak. Aday bağlamı ile
başka gün eşleşmeleri gerçek karşıt yangın etiketi çifti sayılmayacak.

## Başlangıç kontrolü

Hazırlık ve ayrı okuyucu için 42 ilgili test geçti; 8 hazırlık ve
5 ayrı okuyucu davranışı dahil. Ay makbuzu/CSV bozulması, eksik/çift
anahtar, atomik geçici durum ile bilimsel makbuz ayrımı, boş hedef
CSV türleri, statik değişmezlik ve yanlış eğitim/etiket izinleri
sınandı. Sonuç dosyası henüz kapanmadı; tam kabul makbuzu oluşmadan
44.082 anahtar hazır ilan edilmeyecek.

2018–2019 için ilk 24 ay, beklenen 14.584 satırla mühürlendi.
Bu ara durum nihai sonuç değildir; kalan aylar işleniyor.
