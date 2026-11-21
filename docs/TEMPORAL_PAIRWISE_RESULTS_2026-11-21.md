# Gün farklarını öğrenen dokuz doğrusal pilotun sonucu

21 Kasım 2026. Araştırmacı, [somut yöntem önerisindeki](TEMPORAL_PAIRWISE_PROPOSAL_2026-11-21.md)
**A yönünü açıkça seçti**. Dokuz küçük doğrusal model yerelde,
15 dakikalık toplam üst sınır içinde tamamlandı. Ayrı model,
ölçekleme, çift kimliği ve skor denetimi geçti. Bu bir yardımcı
kaynak-bağlamı sıralama deneyidir; gerçek yangın olasılığı veya
günlük risk ürününün doğrulanması değildir.

## Yapılan işlem

2018–2021'in 35.376 tam-girdili benzersiz takvim satırında 11 hava
ve dört geçmiş bitki örtüsü alanının ölçeklemesi öğrenildi.
Dokuz ayarda aynı hücre–yıl–ay içindeki aday-bağlamlı gün ve diğer
tarih arasındaki farklar ile tersleri kullanıldı: ayara göre
28.081–39.014 asıl çift. Ters çiftler yeni bağımsız gözlem değildir.
Sabit C=1, L2, sabit terimsiz lojistik kayıp, lbfgs, 1.000 iterasyon
üst sınırı ve seed=20261121 kullanıldı. Yakınsama 21–30 iterasyonda
sağlandı; hiperparametre veya üretim ayarı aranmadı/seçilmedi.

2022'de aynı 6.573 tarih korundu; 5.982'sinin 15 alanı tam,
591'i bu tam-girdi karşılaştırmasının dışında ve dosyada mevcut.
Bu kesit 5.733–6.406 aynı-yer/ay çifti sağlıyor. Diğer günler
yangın negatifi yapılmadı; gerçek Y/kabul edilmiş L boş, günlük
gözlem unknown kaldı. Özgün U/ağırlıkları ve 2023–2025 korundu.
Doğrusal skor sigmoid yüzdeye veya risk rengine çevrilmedi.

## Aynı tam-girdi çiftlerindeki ölçüm

| Ayar | Gün çifti doğrusal | Önceki tam RF | Önceki hava RF | Statik RF |
|---|---:|---:|---:|---:|
| 500 m / 24 saat | 0,589603 | 0,572276 | 0,568373 | 0,500000 |
| 500 m / 48 saat | 0,587863 | 0,585493 | 0,574273 | 0,500000 |
| 500 m / 72 saat | 0,585685 | 0,588793 | 0,572453 | 0,500000 |
| 1.000 m / 24 saat | 0,595230 | 0,584313 | 0,568357 | 0,500000 |
| 1.000 m / 48 saat | 0,594873 | 0,583741 | 0,582054 | 0,500000 |
| 1.000 m / 72 saat | 0,592441 | 0,590654 | 0,574396 | 0,500000 |
| 2.000 m / 24 saat | 0,591578 | 0,584902 | 0,564704 | 0,500000 |
| 2.000 m / 48 saat | 0,588963 | 0,573148 | 0,554753 | 0,500000 |
| 2.000 m / 72 saat | 0,587127 | 0,577708 | 0,549799 | 0,500000 |

Ölçü, aday-bağlamlı günün daha yüksek skor almasına bir, eşitliğe
yarım kredi veren yardımcı çift AUC'sidir. Gerçek yangın AP'si veya
yüzde doğruluk değildir. Yeni model tam RF'den sekiz ayarda yüksek;
fark küçük, fiziksel olay bağımsızlığı/güven aralığı kurulmuş değil.
Hem öğrenme örneklemi hem model/kayıp değiştiği için fark yalnız
çift kaybının nedensel katkısına atfedilmez. Önceki bütün-satır
takvim tanısından farklı olarak burada iki tarafta 15 alan tam;
eski aralıklarla doğrudan performans artış oranı hesaplanmadı.

## En önemli sınırlama: yakın günlerde ayrım zayıf

Model yeniden eğitilmeden aynı 2022 skorları ayrıldı:

| Karşılaştırma | Doğrusal çift AUC aralığı | Ayara göre çift |
|---|---:|---:|
| Diğer tarih aday tarihinden önce | 0,627107–0,641142 | 2.757–3.074 |
| Diğer tarih aday tarihinden sonra | 0,544355–0,553630 | 2.976–3.332 |
| İki tarih 1–3 gün aralıklı | 0,520107–0,541187 | 1.103–1.222 |
| İki tarih 4–30 gün aralıklı | 0,596332–0,610268 | 4.630–5.184 |

Örnek: aynı yerdeki aday günü ile iki gün önceki/sonraki bir günü
ayırt etmek, ayın uzak tarihlerini ayırt etmekten daha zor.
Bu, günlük uyarı iddiası için önemli bir açık. Ay içi hava eğilimi,
geçmiş yangının devamı, gözlem seçimi ve bitki örtüsünün olay
sonrası etkileri olası açıklamalardır; bu tanı bunlardan hangisinin
neden olduğunu kanıtlamaz. Hedef 24 saat olarak korunuyor;
sonuca bakılarak haftalık hedefe geçilmedi.

## Düzeltilmiş il desteği

| Alan kodu | Doğrusal AUC aralığı | Çift |
|---|---:|---:|
| Antalya | 0,603940–0,614667 | 1.472–1.612 |
| İzmir | 0,539026–0,598841 | 1.381–1.499 |
| Mersin | 0,577036–0,588378 | 2.009–2.150 |
| Muğla | 0,577731–0,630308 | 900–1.201 |

Sınır hücreleri birden fazla ile destek verebilir; toplamlar
bağımsız olay sayısı değildir. İlk ek `context_slices.csv` dosyası,
kaynak ASCII `Izmir/Mugla` kodlarını Türkçe görünen adla karşılaştırdığı
için iki ilde yanlış boş kesit üretmişti. Genel 36 ölçü, modeller
ve tarih-yönü sonuçları etkilenmedi. İlk dosya/üretici korundu;
ayrı düzeltme makbuzu 36 il–ayar birleşiminin hepsinde dolu destek
ve 144 ölçü sağlıyor. İl yorumunda yalnız düzeltilmiş dosya geçerli.
Kaynak kodu/ekran adı ayrımı ve sınır üyeliği testi eklendi.

## Denetim, kayıt ve kimlikler

Ayrı okuyucu dokuz modelin fit satırlarını, yalnız fit ortalama/
ölçeklerini, doğrusal matris skorlarını, fit/2022 çift kimliklerini
ve 36 skaler ölçüyü doğruladı. Model yeniden kurulmadı; dosya ve
bellek durumları değişmedi. Yerel SQLite önce yedeklendi; dokuz
onaylı modelin dosyaları ve 36 ölçü yerel MLflow'a kaydedildi.
Ölçü adları/değerleri birebir geri okundu. Registry/bulut yok.
MLflow run kimliği `814e5d656429480f92d5c4536e5d89ce`.

`outputs/reports/dataset/` altındaki değişmez makbuzlar:

| İş | Yol ve SHA-256 |
|---|---|
| Dokuz fit | `temporal_pairwise_run_v1/20261121T174415Z_5a77b21e/readback.json` — `b8e847f8d510721ce84b788161ae40ac5f3bfa098154b0e56a013fc380f83d82` |
| Ayrı denetim | `temporal_pairwise_audit_v1/20261121T174613Z_2feb2bbd/readback.json` — `7faff2ad4721a8984b3a4e34aae3ebdbe8c61dde3c5568477bd257ed3d68d086` |
| Tarih kesitleri ve yerel kayıt | `temporal_pairwise_closure_v1/20261121T175009Z_0d5f3e3d/readback.json` — `b4b4ce4c14d191296204812eb22c0eeecbb61192db3aceed0c0f7add68cee257` |
| İl düzeltmesi | `temporal_pairwise_province_correction_v1/20261121T175232Z_67a7c851/readback.json` — `c57bb215ed79bfb3f36ad5d9c5f1257faa80f5364a779693891bf9034bb769f3` |

İlk makbuzun durum adı ayrı denetim beklediğini söyler; özgün
dosya değişmedi. Sonraki denetim/kapanış makbuzları tamamlanmayı
bağlar. Kapanışın ilk girişimi lint uyarısında durduruldu; kısmi
klasör ve üretici korundu, bu girişimde MLflow run/backup oluşmadığı
kontrol edildi. Tarih dizi hizalaması ve il kodu davranışları ayrıca
test edildi. Teknik hesap kontrolü insan/saha doğrulaması değildir.

## Projedeki yeri

Onaylı pilot tamamlandı. Günlük dinamiklerle ölçülebilen yardımcı
bir sıralama elde edildi; yakın tarihlerde güçlü ve doğrulanmış
24 saatlik yangın ayrımı kurulmadı. Katsayılar standardize ve
birbirleriyle ilişkili girdiler üzerindedir; örneğin yağışın eksi
işareti veya toprak neminin artı işareti fiziksel nedensel etki
olarak açıklanamaz. Yeni fit veya kapalı yıla bakarak sonuç
kovalanmayacak. Bundan sonraki öncelik, ilk-yeni-olay ile devam eden
tespit/gözlem seçimi etkisini mevcut kayıtlarla ayıran değerlendirme
provasıdır; yeni model araması değildir.

Bu devam kontrolü de tamamlandı: diğer tarihin hedefinde korunmuş
tespit bulunan 48–54 çiftte doğrusal AUC 0,431373–0,500000;
bulunmayan (gözlem durumu unknown) 5.682–6.358 çiftte
0,586589–0,596206. Kaynakla aynı gözlenen 2 km/72 saat grafik
bağını paylaşan yalnız 22–27 çift var. İki tarihin önceki yedi
gününde korunmuş tespit bulunmayan kesitte AUC
0,593772–0,607460 (3.941–4.175 çift). Yedi gün yangın sessizlik
kuralı yapılmadı, hiçbir satır/çift silinmedi. Bu nedenle yalnız
gözlenen devam bağını ayırmak günlük hedef sorununu çözmüş sayılmaz.
Makbuz: `temporal_observed_context_audit_v1/20261121T175622Z_468e8f44/readback.json`,
SHA-256 `952d71ce93eb17bb727a34d88b762fda4f23d0634714cac8952bf91ca9301afb`.

Mevcut Mersin kaynağının farklı bir kaynağa dayanıklılık sınamasını
desteklemesi için yalnız metadata kontrolü yapıldı. Eski kesitte
aynı-yer/ay desteği iki çift. 78 kaynak hücre–ayı için 2.383 günlük
ayrı takvim önerisi ve 2.065 ek yerel X ihtiyacı somutlaştırıldı;
yeni X veya skor oluşturulmadı.
[Gerekçeli sonraki A/B değerlendirme yönü](CROSS_SOURCE_CALENDAR_PROPOSAL_2026-11-21.md).

Ana risk hedefi, gerçek Y/L belirsizliği ve nihai parça kontrolü /
araştırmacı birleştirme onayı koşulu korunur. Bu sonuç birinci aşama
bilimsel kabulünün veya nihai eğitim veri setinin tamamı sayılmadı.

Son ilgili birleşik koşu: **36 test** geçti. Sabit-model, günlük
çift, ek bağlam ve yeni metadata hazırlığı dahil **18 Python dosyası**
kod/biçim kontrolü geçti. Eski 26/27/34 sayımları ara koşulara aittir.
