# Günlük kaynak-bağlam sıralaması model kartı

24 Kasım 2026. Mevcut dokuz sabit modelin araştırma kartı. Amaç, aynı
hücre ve ay içinde kaynak/aday bağlamlı günü diğer günlerden daha üstte
sıralamanın uygulanabilirliğini incelemektir. Skor yüzde yangın riski
değildir. Kalibre yangın olasılığı veya kabul edilmiş PU kestiricisi yoktur.

## Model ve girdiler

XGBoost 3.4.1 `rank:pairwise`: 100 ağaç, derinlik 3, öğrenme hızı 0,05,
`min_child_weight=5`, L2=1, tam satır/sütun kullanımı, CPU hist,
dört iş parçacığı, seed 20261123, `topk=31`, çift ve skor normalizasyonu
açık. Dokuz gruplama ayarının tamamı korunur; üretim ayarı seçilmemiştir.

Girdiler 11 meteoroloji ve dört geçmiş NDVI/NDMI alanıdır; alan sırası
paketin `models/dynamic_features.json` dosyasında sabittir. Kimlik,
tarih, koordinat ve statik örtü bu 15 alanlık girdide değildir. Tam
alan desteği ve eksiksiz dinamik alan şartı vardır; eksiklere sıfır atanmaz.

Öğrenme 2018–2021: ayara göre 23.280–29.140 satır, 777–967 hücre–ay
grubu. Gruplarda hem kaynak bağlamı hem atamasız gün bulunur. Kütüphane
uygunluk işareti 1/0, bilimsel yangın etiketi Y=1/Y=0 değildir. Yeni
hiperparametre taraması veya 2022 ile erken durdurma yapılmamıştır.

## Mevcut 2022 ölçümleri

Aynı hücre/ayda S-bağlamlı gün ile atamasız gün karşılaştırılır:
daha yüksek skor 1, eşitlik 0,5 kredi alır. Bu yardımcı ölçü gerçek
yangın AP'si değildir; ana AP / yardımcı trapez PR-AUC kararı korunur.
Çiftler bağımlıdır; karşılaştırma sayısı bağımsız vaka sayısı değildir.

| Takvim | Çift sayısı | Ana model yardımcı çift kredisi | Hücrelere eşit ağırlıkla |
|---|---:|---:|---:|
| Dört il / uydu-aday bağlamı | 4.702–5.287 | 0,567280–0,601843 | 0,565556–0,609538 |
| Ayrı Mersin kaynak takvimi | 1.921 | 0,528110–0,566892 | 0,527512–0,569478 |

Aralıklar dokuz ayar boyunca minimum/maksimumdur; güven aralığı değildir.
Dört ilde ölçüye katkı veren 165–186 kaynak günü / 135–143 hücre vardır.
Ayrı Mersin'de 65 kaynak günü / 56 hücre vardır. En yoğun hücrenin çift
payı dört ilde %2,65–3,06; Mersin'de %3,12'dir. Tek değerlendirme
hücresi çıkarılınca ana kredi farkı dört ilde −0,005608 ile +0,007794,
Mersin'de −0,013878 ile +0,014029 arasındadır. Bu çıkarma yeniden
öğrenme veya mekânsal çapraz doğrulama değildir; anlamlılık testi yoktur.

Eski geniş meteoroloji destekli XGBoost ve dondurulmuş doğrusal skor,
aynı ana değerlendirme çiftlerinde yardımcı karşılaştırma olarak vardır.
Farklı eğitim desteğine sahip oldukları için aynı model gibi sunulmaz.
FWI için önceki küçük Haziran kesiti bu dokuz ana modelle ortak ölçüm
değildir; yeni bir FWI üstünlüğü iddiası çıkarılmaz.

## Çıktı, kontroller ve sınırlar

Arayüzde görülen model puanı ile aynı hücre/ay içindeki sıra ayrı
anlamdadır. Farklı hücrelerin ham puanlarını kalibre olasılık gibi
karşılaştırmak veya keyfî kırmızı/sarı/yeşil eşikleri üretmek desteklenmez.
Yerel ekran kayıtlı geçmiş skorları okur; canlı model servisi değildir.
Dokuz modelin önceki yeniden yükleme/skor denetimi korunur. 24 Kasım
ek incelemesinde yeni model veya tahmin çağrısı yapılmadan 54 genel,
864 bağlam, 6.456 kaynak-gün/model ve 5.262 hücre-çıkarma satırı ayrı
ilişkisel çift hesabıyla eşleşmiştir.

Veri kaynakla seçilmiştir; etiket gürültüsü, gözlem eksikleri, gerçek
başlangıç/yerel örtü ve nüfusa aktarım açık kalır. Öğrenmede görülmüş
hücreler bulunur; mekânsal genelleme doğrulanmış değildir. 2022 daha
önce incelenmiştir; kör test değildir. Gelecek yıllara ve operasyonel
erişim zamanına dair kanıt yoktur. Ana araştırma hedefi korunur;
bu sonuçlar hedefin başarıyla tamamlandığı anlamına gelmez.

Model koşusu: `primary_weather_rank_run_v1/20261123T143258Z_35678270`;
makbuz SHA-256 `004f7d27d6b0f1825b2b00d7a2825b311e2483b5f2d73c7063cadd9b45b2946d`.
Kaynak/ay/hücre ayrıntıları ve bütün dokuz ayar yerel pakettedir.
