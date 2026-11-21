# Kaynak koşullu takvim kontrolünün özellik hazırlığı

21 Kasım 2026. Araştırmacının önerilen hazırlık sonrası devam
talimatıyla, [ayrı takvim kontrolünün](SATELLITE_PU_ABLATION_RESULTS_2026-11-21.md)
yerel özellik/zaman/eksiklik hazırlığı başlatıldı. Kayıt bu devam
talimatına dayanıyor; yeni yardımcı model, S üyeliği, gerçek Y/L
veya nihai birleştirme onayı değildir. **44.082 anahtarın özellik
hazırlığı ve ayrı geri okuması tamamlandı.** Bu, kaynak koşullu
inceleme X tablosudur; nihai etiketli eğitim veri seti değildir.

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

1.824 günün 3.648 özellik/provenance dosyası güncel hash ile okundu.
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
Son X/QA/metadata dosyaları sürümlü bir snapshot klasörüne yazıldı;
bu inceleme snapshot'ı nihai etiketli veri seti değildir.

İlk koşu kimliği:
`outputs/reports/dataset/source_calendar_feature_review_v1/20261121T164603Z_741c2896`.
Üretici `scripts/quality/prepare_source_calendar_features.py`, karar
`configs/source_calendar_feature_preparation_v1.json`. Tek yerel
parça 15 dakika sınırında duraklayabilir; tamamlanan aylarla aynı
oturum içinde devam edilebilir. Bu zamanlanmış iş veya bulut görevi değil.

`scripts/quality/verify_source_calendar_features.py` ayrı snapshot,
geçmiş zaman, ay/gün/anahtar korunumu ve önceki 1.689 X/QA kaydının
birebir eşitliğini kontrol etti. Aynı hücre/ay içinde değişen
meteoroloji bilgisi ve eksiklik desteği sayıldı. Aday bağlamı ile
başka gün eşleşmeleri gerçek karşıt yangın etiketi çifti sayılmayacak.

## Başlangıç kontrolü

Hazırlık ve ayrı okuyucu için 42 ilgili test geçti; 8 hazırlık ve
5 ayrı okuyucu davranışı dahil. Ay makbuzu/CSV bozulması, eksik/çift
anahtar, atomik geçici durum ile bilimsel makbuz ayrımı, boş hedef
CSV türleri, statik değişmezlik ve yanlış eğitim/etiket izinleri
sınandı. İlk kontrol anında sonuç henüz kapanmamıştı; yalnız ay
checkpoint'leri kabul ediliyor, tam makbuz bekleniyordu.

2018–2019 için ilk 24 ay, beklenen 14.584 satırla mühürlendi.
Bu ara durumun ardından kalan 36 ay da tamamlandı; aşağıdaki kapanış
ilk durumun yerine yeni sonuç olarak kaydediliyor.

## Tamamlanan X ve eksiklik sonucu

| İnceleme rolü | Satır | 27 özellik tam | En az bir özellik eksik | Meteoroloji tam |
|---|---:|---:|---:|---:|
| 2018–2021 fit-rolü | 37.509 | 35.376 | 2.133 | 36.501 |
| 2022 tanı-rolü | 6.573 | 5.982 | 591 | 6.207 |
| Toplam | 44.082 | 41.358 | 2.724 | 42.708 |

Bu rol adları yeni model eğitimi izni veya kör değerlendirme değil.
Eksik 2.724 satır silinmedi/doldurulmadı. Meteorolojinin eksik olduğu
1.374 satır, 45 hücre–yıl–ay grubunda bulunuyor; bu gruplarda bütün
ay boyunca tam hava vektörü yok. Diğer 1.398 grupta tarih boyunca
farklı hava vektörleri var. Eksik hava günleri günlük risk hesabına
uygun kabul edilmedi; burada yalnız inceleme kaydı olarak korunuyor.
Statik alanlar aynı hücre–ay içinde değişmiyor.

Bütün 60 ayın CSV/makbuzları, 1.824 gün ve 44.082 anahtarın korunumu
ayrı okuyucuyla kontrol edildi. Önceki incelemenin ortak **1.689
anahtarında hem X hem provenance birebir aynı**. Özgün 2.048 U ve
ağırlıkları kendi kaynaklarında aynı kaldı. Günlük veri üreticileri,
gözlem/etiket protokolü veya 2023–2025 bilimsel değerleri değişmedi.

Kaynak/örtü/gözlem/yayın erişimi belirsizlikleri korunuyor. Geçmiş
uydu/meteoroloji edinim zamanının T'den önce olması, ilgili ürünün
o gün operasyonel olarak erişilebilir olduğunu kanıtlamıyor.
Bu hazırlık gerçek yangın etiketini veya PU varsayımlarını doğrulamıyor.

## Zaman karşılaştırması için artık hangi bağlam var

2018–2021'de 1.227, 2022'de 216 hücre–yıl–ay grubu var. Her olası
aday bağlamını aynı gruptaki diğer tarihlerle eşleştiren sayım fit
rolünde 42.276, 2022'de **7.124 tarih bağlamı çifti** veriyor. İki
tarihte de hava vektörü tam olan karşılıklar 41.271 ve 6.741.

Bu sayılar **gerçek karşıt yangın etiketi veya yeni kaynak-S/U
eğitim çiftleri değil**. Diğer tarihler başka aday günlerini de
içerebilir. Önceki üç aday–U çiftiyle aynı tanım olmadığından
"başarım/örnek desteği şu kat arttı" sonucu çıkarılmadı. Şimdilik
yalnız günlük bağlamın mevcut X ve eksiklik desteği hazır.

## Somut sonraki tanı önerisi

Öneri, 2018–2021'de daha önce kurulmuş dokuz ayardaki tam/hava/statik
RF'leri **yeniden eğitmeden** 2022'nin aynı 6.573 takvim anahtarına
uygulamak. 27 sabit modelin dosya/hash'leri somut plana bağlandı.
Mevcut ayar-proposal varlığı yalnız yardımcı kaynak göstergesiyle
incelenecek; karşı günler gerçek negatif yapılmayacak. Eksik hava
366 gün korunup yeterli hava girdisi olan kesit ayrıca raporlanacak.

Bu, kaynak koşullu ve önceden görülmüş yıl için tanıdır; nüfusu
temsil eden/kör yangın başarımı, model seçimi veya risk rengi değil.
Hazırlık talimatı puanlama ve yeni yardımcı gösterge kullanımını
kendiliğinden açmadı. Araştırmacıya A olarak bu sabit-model günlük
tanısı, B olarak önce tabloyu görüşme seçeneği sunuldu; henüz
puanlama, yeni S kodu veya ek fit yapılmadı. Nihai birleştirme
onayı ve birinci aşamanın bilimsel kabulü hâlâ açık.

## Tam sonuç kimlikleri

- X inceleme makbuzu:
  `source_calendar_feature_review_v1/20261121T164603Z_741c2896/readback.json`,
  SHA-256 `b718ed5d7ff492ddaf6d5217e7f88b3f62a6024a9d2138f4225154b3e3576040`.
  Aynı klasörün `snapshot_8914be77/` altında `features.csv`,
  `provenance.csv`, `review_roles.csv` bulunuyor. X CSV 27 özellik
  içerir; boş Y/L ve gözlem/rol alanları ayrı metadata CSV'sindedir.
- Ayrı geri okuma:
  `source_calendar_feature_audit_v1/20261121T165526Z_5c6a7598/readback.json`,
  SHA-256 `3475b7108e9848a28007afee8908681412847c56c7ac4524423e5bb29e659180`.
  Standart ISO tarih okuyucusu, bağımsız anahtar/rol eşitliği, önceki
  1.689 değer ve bütün ay makbuzları kontrol edildi. Bu ikinci
  kontrolde ham günlük büyük dosyalar yeniden hash edilmedi;
  üretim koşusu 3.648 dosyayı güncel içerik hash'iyle doğrulamıştı.
- Seçilmemiş sabit-model tanı önerisi:
  `source_calendar_fixed_model_plan_v1/20261121T165748Z_848be12d/readback.json`,
  SHA-256 `9bdbbee2d4398fd2ae95e0ec1b27fdd286f589133d52a50b2b89873abe01271f`.
  `configs/source_calendar_fixed_model_diagnostic_v1.json` içinde
  puanlama, gösterge kodlama, yeni eğitim/etiket ve final merge izinleri kapalı.

Birleşik ilgili koşuda **42 test** geçti; son ay-makbuzu eşitlik
kontrolü sonrasında beş ayrı okuyucu testi tekrar geçti. Üç
betik/iki test dosyası (beş
Python dosyası) kod/biçim kontrolü geçti. Yeni tanı planı 27 modelin
güncel dosya hash'leri ve tüm giriş kimlikleriyle üretildi; yeni
çıktı skoru/modeli oluşturulmadı. İlk hazırlık kodu ve ara durum
`0679960` kaydıyla korunuyor; tamamlanan bilimsel sonuç ayrı makbuzdur.
