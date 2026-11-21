# Aynı hücre ve ay içinde sabit model kontrolü

21 Kasım 2026. **Önceden kurulmuş 27 RF'nin takvim tanısı ve ayrı
geri okuması tamamlandı; yeni model eğitilmedi.** Amaç, aday bulunan
yerleri ayırt etmenin yanında aynı yerdeki farklı günlerin ayrılıp
ayrılmadığını sınamaktı. Sonuç, gerçek yangın doğruluğu veya olasılığı
olarak yorumlanamaz. Ana 24 saatlik yangın araştırma hedefi korunuyor.

## Yetki ve kapsam

Araştırmacının insan müdahalesi gerekmedikçe ilerleme talimatı,
önceden somutlaştırılmış sabit-model tanısının uygulanmasına bağlandı.
A seçeneği formda ayrıca işaretlenmiş gibi kaydedilmedi. Özgün öneri
değiştirilmedi; yürütme kapsamı ayrı
`configs/source_calendar_fixed_model_execution_v1.json` dosyasında.
Bu kapsam yeni fit, gerçek Y/kabul edilmiş L, ayar seçimi, kapalı
yıl erişimi, risk rengi veya nihai birleştirme izni vermiyor.

[Önceki X hazırlığının](SOURCE_CALENDAR_FEATURE_PREPARATION_2026-11-21.md)
2022 kesitindeki aynı 6.573 hücre-gün, dokuz ayarda değerlendirildi.
Tam 27 özellikli, yalnız meteorolojili ve yalnız statik örtü/arazili
RF'lerin kayıtlı 27 dosyası kullanıldı. Model/girdi hash'leri ve
bellekteki model durumu puanlamadan önce/sonra aynı kaldı.
Yalnız mevcut ayarın aday önerisinin o anahtarda bulunması yardımcı
gösterge yapıldı. Diğer takvim günleri gerçek yangın negatifi değildir;
özgün 2.048 U örneklemi ve ağırlıkları değiştirilmedi.

## Günlük ayrım sonucu

Somut karşılaştırma: aynı 5 km hücrede, aynı yıl ve ay içinde aday
önerisi bulunan günün skoru, diğer tarihin skorundan yüksek mi?
Yüksekse bir, eşitse yarım kredi verildi. Aşağıdaki AUC çift-kredisi
ortalamasıdır; yüzde yangın doğruluğu, AP veya kalibrasyon değildir.
Bir gün birden fazla çiftte bulunabilir; çiftler bağımsız olay değildir.

| Dokuz ayardaki aralık | Tam RF | Yalnız meteoroloji | Yalnız örtü/arazi |
|---|---:|---:|---:|
| Aynı hücre–yıl–ay, bütün satırlar | 0,568463–0,587403 | 0,553183–0,581686 | 0,500000 |
| İki tarihte meteoroloji tam | 0,576583–0,594518 | 0,555778–0,585940 | 0,500000 |

Bütün satırlarda ayara göre 6.299–7.060, meteorolojisi tam kesitte
6.006–6.679 kaynak-bağlamı çifti var. İlgili aday anahtarları
215–242; meteorolojisi tam karşılık bulanlar 205–229. Eksik hava
vektörlü 366 tarih dosyalardan çıkarılmadı. Modellerin önceki fit
medyanları kullanıldı; bu tanıda yeniden doldurma/öğrenme yapılmadı.

Yalnız statik modelin aynı hücrede bütün günlere aynı skoru vermesi
beklenen davranış; eşitlikler nedeniyle tam 0,5 elde edildi. Günlük
ayrım için coğrafi/örtü ayrımından daha zor bir sınama sağlandı.
Önceki daha yüksek genel AUC ile bu sayılar farklı karşılaştırma
evrenlerine ait: performansın şu oranda düştüğü veya coğrafyanın
nedensel etkisinin ölçüldüğü iddia edilmiyor.

## İl bağlamı

Aynı hücre–ay ve iki tarafta tam hava vektörü şartında:

| Alan desteği | Tam RF aralığı | Meteoroloji aralığı | Çift sayısı aralığı |
|---|---:|---:|---:|
| Antalya | 0,569142–0,609155 | 0,566493–0,605137 | 1.534–1.674 |
| İzmir | 0,593789–0,672587 | 0,561491–0,623995 | 1.492–1.610 |
| Mersin | 0,534233–0,578296 | 0,547734–0,569972 | 2.045–2.186 |
| Muğla | 0,529046–0,592885 | 0,491701–0,582492 | 964–1.265 |

İl üyeliği hücrenin alan kesişimidir; sınır hücresi birden fazla
ile destek verebilir. Bu sayılar toplanarak tekil olay sayısı
üretilmez. Muğla'da bazı ayarlarda hava modelinin tesadüfi
sıralamaya yakın olması, bütün iller için günlük risk başarısının
gösterilmiş olmadığını somutlaştırıyor. Güven aralığı ve gerçek
olay bağımsızlığı bu tanıyla kurulmuş değil.

## Doğrulama ve deney kaydı

Ayrı okuyucu 27 kayıtlı modelin tahminlerini birebir karşılaştırdı.
162 ölçü; genel çiftlerde ortalama-sıra toplamı, aynı hücre–ayda
ayrı skaler çift döngüsüyle yeniden hesaplandı. Eksik veri kesitleri,
eşit skor ve boş karşılaştırma davranışları kontrol edildi.
Güncel ilgili koşuda **26 test** geçti; altı Python dosyası kod ve
biçim kontrolü geçti. Bu teknik geri okuma bağımsız insan/saha
doğrulaması değildir.

Yerel SQLite veritabanı önce yedeklendi; 162 tanı ölçüsü yerel
MLflow'a kaydedilip okundu. Yeni model/registry kaydı ve bulut yok.

| Yerel makbuz | SHA-256 |
|---|---|
| `source_calendar_fixed_model_run_v1/20261121T171148Z_91ab9c78/readback.json` | `ff51e4790f92eeca51b1db107c38c876a5a2b6ea34d54d4a3451d32754e28f4f` |
| `source_calendar_fixed_model_audit_v1/20261121T171907Z_77821dec/readback.json` | `bd451bd1d8e93eeb81f1123004fb2de92aecbfa2c511522fff1486a5fc5f9e6f` |

Bütün bu yollar `outputs/reports/dataset/` altındadır. İlk klasörde
dokuz `*_calendar_scores.csv` ve `comparison_summary.csv`; ikinci
klasörde `province_within_calendar_support.csv` ve
`within_calendar_comparison.png` bulunur. Yerel MLflow run kimliği
`5e2d24d3683e447496ad704f6cae2738`;
`mlflow_record.json` kayıt ve önceki veritabanı yedeği kimliğini korur.

## Veri seti hazırlığına katkı ve açık konu

44.082 satırlık X inceleme tablosu korunuyor. Bu çalışma, güçlü
görünen yer ayrımını günlük yangın becerisiyle karıştırmayı önledi
ve hangi günlük karşılaştırmanın gerçekten mevcut olduğunu ölçtü.
Mevcut modeller bu takvim hedefiyle eğitilmiş değildi; sonuç bütün
model ailelerinin başarısız olduğunu göstermez. Kaynak seçimi,
yanlış pozitifler, gözlenmeyen olaylar ve gerçek hedefle sıralama
ilişkisi açık. 2022 daha önce incelenmiş yıl; kör final test değildir.
Gerçek Y ve kabul edilmiş L boş, günlük gözlem unknown kalıyor.
Birinci aşamanın bilimsel kabulü ve nihai birleştirme tamamlanmadı.

Sonraki yöntem kararına hazırlık olarak genişleyen takvimin zaman
rolleri arasındaki grafik bağı ve günlük özellik desteği ayrıca
tamamlandı: 2 km/72 saat gözlenen grafikte ortak dönem bloğu 0;
gerçek fiziksel olay bağımsızlığı kanıtı değil. Tam 15 günlük alanla
2018–2021'de 28.081–39.014, 2022'de 5.733–6.406 olası aynı-hücre/ay
çifti var. Yeni çift matrisi veya model kurulmadı.
[Makbuz, kaynak kontrolü ve somut A/B yöntem önerisi](TEMPORAL_PAIRWISE_PROPOSAL_2026-11-21.md).

Son birleşik doğrulamada yedi Python dosyasının kod/biçim kontrolü
ve zaman-destek testi dahil **27 ilgili test** geçti. Önceki
26-test sayımı bu ek denetim öncesine aittir.
