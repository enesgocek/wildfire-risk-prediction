# Mevcut Mersin kaynağıyla ayrı takvim sınaması önerisi

21 Kasım 2026. **Yalnız metadata hazırlığı tamamlandı; yeni günlük
X çıkarımı, skor veya fit yapılmadı.** Amaç, uydu adaylarıyla
öğrenilen günlük sıralamanın farklı bir kaynak tanımında da ne
gösterdiğini incelemek. Yeni kurum/yazar yazışması önerilmiyor.

[Dokuz doğrusal pilot](TEMPORAL_PAIRWISE_RESULTS_2026-11-21.md)
tamamlandı. 2022'de aynı-hücre/ay çift AUC 0,585685–0,595230;
1–3 gün aralıklı tarihlerde 0,520107–0,541187. Daha fazla modeli
aynı uydu göstergesinde deneyerek yüksek bir değer aramak yerine,
mevcut farklı kaynağa dayanıklılığı incelemek öneriliyor.

## Mevcut kaynak ne sağlıyor

Daha önce korunmuş Mersin arşivinin 2022 rolünde 81 kaynak-merkezi
hücre-günü ve 87 coğrafi U anahtarı var. Bunların 79/79'unda 15
dinamik alan tam. Aynı hücre–yıl–ay şartıyla yalnız **iki çift**,
yalnız iki kaynak anahtarına karşılık buluyor. Bu küçük desteğe
geniş bir başarı yorumu yüklenmeyecek.

81 kaynak günü 78 hücre–yıl–aya yayılıyor. Bu aylardaki bütün uygun
tarihleri koruyan takvim **2.383 anahtar** içerir. 318'inin X'i
mevcut inceleme snapshot'larında bulunuyor; **2.065 ek anahtarın**
yerel günlük dosyalardan hazırlanması gerekir. Kaynak günü
çıkarılmaz, diğer günlere yangın yok yazılmaz. Özgün 87 U ve
genel 2.048 U/ağırlıkları kendi kaynaklarında aynı kalır.
Korunan WF1538 hücre-günü yeniden kaynak grubuna alınmadı.

Bu veri, uydu kaynağından farklı kayıt kökenine sahiptir; ancak
koordinatın anlamı/hata sınırı, saat standardı, ilk-yeni-yangın ve
kayıt kapsamı belirsizlikleri çözülmüş değildir. Bağımsız gerçek
Y testi veya güvenilir negatifler elde edilmiş sayılmaz.
2022 daha önce görülmüş keşif yılıdır; 2023–2025 kapalı kalır.

## A — Ayrı kaynak takvimi ve sabit model tanısı

Önerilen A, 2.383 anahtar için geçmiş zaman/şema/eksiklik/X kontrolü,
ortak 318 anahtarda mevcut değerlerle eşitlik ve ayrı geri okuma
hazırlamak; sonra **aynı dokuz kayıtlı doğrusal modeli değiştirmeden**
2022'nin bu ayrı takviminde incelemektir. Yeni fit, ölçekleme
öğrenme, hiperparametre arama veya senaryo seçimi yok.

Aynı hücre–yıl–ayda Mersin kaynak üyeliği bulunan tarih ile diğer
tarih yalnız yardımcı kaynak-bağlamı göstergesiyle karşılaştırılır.
İki tarafta 15 alanın tamlığı ve eksik kesit desteği ayrıca yazılır.
Önce/sonra ve 1–3 gün aralığı, ana pilotla aynı tanımlarla raporlanır;
veri yetersizse boş kesit korunur. Model dosya/hash'leri
`temporal_pairwise_run_v1/20261121T174415Z_5a77b21e/readback.json`
makbuzuna bağlı kalır; yeni model oluşturulmaz. Günlük yerel iş
15 dakikalık üst sınır ve değişmez çıktı düzeniyle hazırlanır;
gerekirse aynı girdiyle devam eder, tamamlanmamış koşu kabul edilmez.
Bulut, yeni kullanıcı girişi veya yeniden indirme planlanmıyor.

Bu yeni değerlendirme örnekleminin ve kaynak göstergesinin
seçimidir; veri seti/gerçek etiket/nihai birleştirme kabulü değildir.
Sıralamanın iki kaynakta benzer görünmesi bile kaynak gürültüsü ve
yangın hedefi bağlantısını tek başına doğrulamaz.

## B — Mevcut küçük kaynak kesitiyle sınırlı kalmak

Alternatif, yeni 2.065 X anahtarını hazırlamadan mevcut 81/87 kayıt
ve iki aynı-yer/ay çiftiyle sınırlı bir inceleme yapmaktır. İş yükü
azalır; günlük sıralamanın farklı kaynağa taşınması için karşılaştırma
desteği çok dar kalır. İki çift yeterli doğrulama gibi sunulamaz.

## Metadata kimliği

`outputs/reports/dataset/cross_source_calendar_support_v1/20261121T175954Z_4ad955e7/readback.json`,
SHA-256 `07c0430bba04db18303767882fd5bdf9eae1f1233f7743977c90d48bd10dbfb7`.
Aynı klasörde `proposed_2022_source_calendar_keys.csv` var.
877 eski kaynak/U kaydı, eski rol sözleşmesi ve 44.082 takvim
snapshot'ının güncel hash'leri kontrol edildi; yeni ham günlük
dosya okunmadı. Bu belge araştırmacı yönü için somut öneridir;
henüz A kararı veya uygulama izni oluşturmaz.
