# Sabit kaynak skorlarının mevsim ve örtü karşılaştırılabilirliği — 20 Kasım 2026

## Aynı gün sonraki ürün kararı: yüzde yerine göreli risk

Araştırmacı, üründe kesin yangın ifadesi veya zorunlu yüzde yerine
kırmızı/sarı/yeşil risk kategorileri kullanılmasını önerdi. Bu yön
[ayrı karar kaydına](../configs/relative_risk_product_direction_v1.json)
işlendi. **Yangın riski araştırma amacı korunuyor.** Aşağıdaki A/B
teslim önerilerinden birinin kabul edildiği sonucu çıkarılmadı; kaynak
üyeliği araştırmasını nihai yangın ürünü diye yeniden adlandırma yok.

| Sunum | Anlam | Kabul edilmemiş yorum |
|---|---|---|
| Kırmızı | Sonraki 24 saatte göreli yüksek risk | Kesin yangın veya doğrulanmış yüzde |
| Sarı | Göreli orta risk | Sabit bir olasılık aralığı |
| Yeşil | Göreli düşük risk | Yangın çıkmaz / risk sıfır |
| Gri | Gelecekte kabul edilecek girdi politikası altında hesaplanamadı/veri yetersiz | Düşük risk |

Renkler için sayısal kesimler henüz seçilmedi. Örnekleri keyfî olarak
eşit üçe ayırıp bu grupların gerçek tehlike seviyeleri olduğu
söylenmeyecek. Eşik/kategori politikası eğitim–doğrulama rollerinde,
değerlendirme desteği ve kullanım amacıyla gerekçelendirilecek; 2025
kapalı final veri seçimi/eşik ayarına açılmayacak.

Yüzde gösterimini zorunlu tutmamak, ilk ürün için mutlak olasılık
kalibrasyonunu zorunlu teslim koşulu olmaktan ayırır. **Göreli
sıralamanın yangın hedefiyle ilişkisi ve değerlendirme dayanağı**
gerekmeye devam eder. Kaynak S ayrımı, yalnız renk verilerek gerçek
yangın riski sıralaması kabul edilmez. Mevsim/örtü tanısının 0,712
değeri ne bu yolu olanaksız ilan eder ne gerçek hedefte başarılı
olduğunu kanıtlar. İlerleme için her belirsiz örneğin gerçek negatif
veya bütün yangınların eksiksiz manuel doğrulanmış olması koşulu
getirilmiyor; uygulanacak PU varsayımları ve değerlendirme protokolü
açık/gerekçeli olmalı.

Araştırma sözleşmesi sonraki **24 saat** olarak korunuyor. Haftalık
görünümde her güne ait sonuç ve gerçek geçerlilik aralığı gösterilebilir;
bugün hesaplanan 24 saatlik skordan yedi günlük tahmin türetilmedi.
Yedi günlük hedef ayrıca yöntem/veri kararı gerektirir. 2023
kalibrasyon yönü, 2024 karşılaştırma ve 2025 final rolleri bu sunum
kararıyla değiştirilmedi. Yeni model, risk haritası veya etiket
üretilmedi; nihai birleştirme onayı verilmiş değil.

## Tamamlanan iş ve somut bulgu

İlk izinli yardımcı pilotun **aynı kaydedilmiş 2022 skorları** kullanıldı.
81 kaynak merkezi hipotezi ve 87 belirsiz U anahtarı dosyada korundu;
model, ön işleme, özellik, skor, etiket veya örneklem değiştirilmedi.
2023/2024/2025 değerleri açılmadı. Bu çalışma, daha önce görülen toplu
sonucun ardından yapılan **keşifsel tanıdır**; önceden kaydedilmiş kör
değerlendirme veya gerçek yangın başarımı değildir.

| Karşılaştırılan kaynak/U çiftleri | Çift sayısı | Lojistik S AUC | RF S AUC | Eksiklik kontrolü S AUC |
|---|---:|---:|---:|---:|
| Tümü | 7.047 | 0,820065 | 0,854264 | 0,534483 |
| Aynı takvim çeyreği | 1.737 | 0,767415 | 0,804260 | 0,512666 |
| Aynı takvim ayı | 606 | 0,759076 | 0,803630 | 0,499175 |
| Aynı geniş odunsu örtü bandı | 4.748 | 0,737574 | 0,789596 | 0,522325 |
| Aynı çeyrek ve örtü bandı | 1.136 | 0,649648 | 0,707746 | 0,501761 |
| Aynı ay ve örtü bandı | 399 | 0,639098 | 0,711779 | 0,494987 |

S, yayımlanmış kaynak grubuna üyelik; U'da S=0 gerçek yangın yokluğu
değil. **Y bütün satırlarda boş.** Buradaki ölçüler gerçek yangın AP,
AUC, yüzde doğruluk veya kalibrasyon sonucu değildir. Aynı hücre birden
fazla günde bulunabilir; çiftler bağımsız deney veya yangın sayısı değildir.

Somut örnek: 2022 Ocak'ta bir kaynak anahtarına karşı 13 U, Şubat'ta
sıfır kaynak anahtarına karşı beş U var. Eylül'de ise 15 kaynak ve 10 U
bulunuyor. Tüm çiftler hesabı, farklı mevsimleri de karşılaştırıyor.
Ay içi hesap Şubat'ın beş U satırını silmiyor; o ay karşı kaynak olmadığı
için bu beş satırdan ay içi kaynak/U karşılaştırması üretilemiyor.

Eski CGLS 2017 hücre özelliklerinde orman+çalı payı en az %50 olan
**80/81 kaynak** ve **59/87 U** anahtarı var. Düşük bantta yalnız bir
kaynak ve 28 U kalıyor. Bu ciddi destek dengesizliği, düşük örtü
alanında güvenilir performans veya dört ile genelleme iddiasına izin
vermez. Gerçek yangınların örtü dağılımı da farklı olabilir; bu sayım
tek başına kaynak seçilme yanlılığını veya PU varsayımlarının ihlalini
kanıtlamaz. Hücre örtüsü olay noktasının örtüsü yerine geçmez.

## Hesabın anlamı ve sınırları

- Çeyrekler Ocak–Mart, Nisan–Haziran, Temmuz–Eylül, Ekim–Aralık.
  Örtü bantları CGLS 2017 hücre orman+çalı payı `<0,5` ve `≥0,5`.
  %50 yalnız geniş karşılaştırma bandı; **kapsam eleme/etiket kuralı değil**.
  Araştırmacının 2.889 hücreyi koruma kararı değişmedi.
- Her kaynak/U anahtar çifti bir karşılaştırmadır. Kaynak skoru daha
  yüksekse 1, eşitse 0,5, daha düşükse 0 puan. Aynı-bant sonucu,
  katman AUC'lerinin basit ortalaması değil, tüm uygun çiftlerin
  puan toplamının uygun çift sayısına bölümüdür. Tek gruplu katman
  AUC'si `null`; sıfır veya 0,5 uydurulmaz.
- Her şemada aynı katman ve farklı katman çiftleri, toplam 7.047
  çiftin ve toplam puanın ayrık/tam parçalarıdır. Böylece hangi
  karşılaştırmaların hesaba girdiği denetlenebilir.
- Ay+örtü hesabında kaynakların 81'i ve U'nun 56'sı karşı gruptan
  aynı katmanda en az bir anahtar buluyor. 31 U dosyada korunuyor,
  bu dar karşılaştırmaya katkı yapamıyor. 23 gözlenen katmanın
  11'inde yalnız bir üyelik grubu var; sonuç yalnız 399 çifte dayanıyor.
- RF'nin 0,854'ten 0,712'ye değişmesi **düzeltilmiş gerçek yangın
  başarımı**, nedensel yanlılık payı veya istatistiksel anlamlılık
  değildir. Karşılaştırılan çiftlerin bileşimi/araştırılan nicelik
  değişiyor; tüm fark “mevsim/örtü hatası” diye açıklanamaz.
- Eski ve geniş örtü bandında eşleştirmek, aynı yerel habitat veya
  aynı hava koşulunu sağlamak değildir. Gerçek sınıfa koşullu
  dağılımlar, pozitifçe zenginlik, yeni/devam olayı ve konum/saat
  anlamı bu tanıyla doğrulanmadı. Eksiklik kontrolünün yaklaşık
  0,5 olması başka kaynak etkilerini dışlamaz.
- Beş şemanın ve üç modelin bütün sonuçları raporlandı. İyi çıkan
  katman seçilmedi; yeniden eğitim, model seçimi veya eşik araması yok.

## Birinci aşamaya etkisi ve gerçek karar noktası

**Kapanan teknik iş:** ilk yardımcı pilotun skorları, toplam başarı
izlenimine ek olarak karşılaştırılabilirlik ve yetersiz destek açısından
denetlendi. Küçük bir modelin çalıştığı ve farklı karşılaştırmalarda
kaynak ayrımının değiştiği gösterildi. Bu, eski sonucun bilimsel
sınırını somutlaştırıyor; gerçek yangın kanıtı eklemiyor.

**Üç açık bilimsel konu aynı:** (1) kaydın gerçek yeni orman/çalılık
olayına hangi konum/günle karşılık geldiği; (2) kaynak/U karışımı ve
ölçüm/seçilme mekanizmasının hedef sıralamasına aktarım dayanağı;
(3) gerçek AP/kalibrasyon için uygun referans. Daha büyük model,
mevsim eşleştirmesi veya örnek sayısı bu bilgi açıklarını kendiliğinden
kapatmaz. 26–29 Kasım karar hedefi bilimsel kabul garantisi değildir.

Mevcut kanıtla veri üretimine koşulsuz geçiş önerilmiyor. İnsan kararı
için iki somut teslim yönü hazırlanıyor; **henüz seçilmiş değiller**:

**A — Varsayımlı zayıf gözetim araştırmasını teslim odağı yapmak.**
Ana yangın riski amacı araştırma motivasyonu olarak korunur; mevcut
uygulamanın desteklenen iddiası kaynak koşullu sıralama/yöntem
uygulanabilirliğiyle sınırlandırılır. İncelenebilir veri sürümünde
gözlenen S, belirsiz U, boş gerçek Y, zaman/örtü/konum sınırları ve
provenance açıkça taşınır. Harita hazırlanırsa model skoru ve bu sınır
görünür; yüzde yangın olasılığı veya doğrulanmış yangın başarısı denmez.
Bu, asıl hedefe ulaşıldığı iddiası değil, deneyin/teslim iddiasının
sınırlandırılmasıdır. Yeni deneyler ve son birleştirme ayrıca yetki/kabul
gerektirir. Desteklenmeyen gerçek yangın AP/kalibrasyon bölümü açık
sınırlama ve gelecekteki doğrulama işi olarak yazılır.

**B — Doğrulanmış 24 saatlik yangın olasılığı teslimini tek kabul hedefi
olarak korumak.** Mevcut yardımcı pilot korunur, birinci aşama ve
etiketli veri üretimine geçiş açık kalır. Var olan kanıtın ötesinde
uygun referans/ölçüm dayanağı edinilmeden bu hedef için güvenilir
teslim tarihi verilemez. Bu yön otomatik olarak yeni yazışma veya
kurumsal talep başlatmaz.

Öneri A, teslimin ölçülen bulgulara dayanmasını sağlar; özgün yangın
olasılığı hedefinin tamamlandığı söylenemez. Projenin iddiasını
etkilediği için araştırmacının açık kararı gerekir. Genel devam talimatı
bu değişikliğin, birinci aşama bilimsel kabulünün veya son etiketli
birleştirmenin onayı sayılmadı. Karar gelene kadar yalnız bu tanı ve
karar hazırlığı tamamlandı; yeni veri etiketi/model/harita üretilmedi.

### Araştırmacının açıklama istemesi: yön değişmedi

Araştırmacı henüz A veya B'yi seçmedi; risk hesabından neden
vazgeçileceği ve veri yeterliliği ayrımının açıklanmasını istedi.
Bu yanıt kapsam daraltma, eğitim veya birleştirme onayı sayılmadı.
Önceki iki seçenek teslim iddiası önerileridir; mevcut ana amaç
değiştirilmiş değildir. Aşağıdaki ayrım ilerleme görüşmesinin temeli:

1. Meteoroloji/örtü/bitki/uydu kayıtlarının varlığı ve modelin skor
   hesaplayabilmesi teknik olarak gösterildi. 877 anahtarlık küçük
   inceleme, bütün veri arşivinin boyutu veya tamamlanma durumu değil.
2. Hedefteki yeni olay, doğru hücre/gün, orman/çalılık bağlamı ve
   kaynak seçilme/ölçülme koşulları ayrı bilimsel sorular. FIRMS'ın
   çok sayıda tespit içermesi bunları tek başına yanıtlamıyor.
3. PU her U satırını gerçek negatifle veya bütün satırları elle
   doğrulanmış Y ile değiştirmeyi gerektiren bir tercih olarak ele
   alınmıyor. Ancak projeye uygulanan karışım/seçilme varsayımları
   gerekçelendirilmeli; kaynak S başarısı gerçek hedef Y başarısına
   otomatik aktarılamaz. Ana risk hedefinin **gerekçeli varsayımlar
   altında sıralama araştırması**, **doğrulanmış olay sıralaması** ve
   **kalibre edilmiş 24 saatlik olasılık** düzeyleri ayrıdır.
4. Bugünkü destek, kaynak koşullu yardımcı sıralama provası düzeyinde.
   Gerçek olay sıralaması veya kalibre edilmiş yüzde risk kabul
   edilmiş değil. Bu sınırlama verilerin kullanılamaz olduğu ya da
   yangın riski amacının bırakıldığı anlamına gelmiyor; kaynağa göre
   üretilen skora doğru anlam vermeyi gerektiriyor.

Mevcut doğrulama boşluğuna eklenen bu açıklama yeni deney/iddia kabulü
değil. Veri/ara çıktı korunuyor; araştırmacı açıklamadan sonra yöntem
ve teslim yönü hakkında karar verebilir. Yeni daraltma uygulanmadı.

## Kontroller ve çıktı kimliği

15 yeni dahil **135 ilgili davranış testi** geçti: mevsim bileşimiyle oluşabilen yapay
ayrım, eşit skor, çift ağırlıkları, karşı grup bulunmayan katman,
değişen satır sırası, boş Y, yıl/saat sınırı, yinelenen/eksik anahtar
ve eksik/uygunsuz örtü korumaları sınandı. Standart kütüphane ile
bütün 7.047 çift her şema/model için ayrıca sayıldı; 168 anahtarın
özgün skorları, bant atamaları ve boş hedefleri geri okundu. Bunlar
otomatik teknik doğrulamalardır, bağımsız saha/insan doğrulaması değil.

- Üretici: `scripts/quality/audit_source_ranking_comparability.py`.
- Tanı ayarı: `configs/source_ranking_comparability_v1.json`.
- Çıktı: `outputs/reports/dataset/source_ranking_comparability_v1/20261119T234208Z_df9aa772/`.
  UTC 19 Kasım 23.42, Türkiye saatiyle 20 Kasım 02.42.
- `readback.json` SHA-256
  `192de41681419e92b6f48cf0a557687a5ca5d3bdeed8f534c96ad0c89ec7c224`.
- `separate_readback.json` SHA-256
  `d592000d0f346f34df561b31fcca11003606962970ea91f971fe3b6a47d24861`.
- Aynı klasörde 168 satırlık `fixed_score_strata.csv`, bütün katmanlar
  için `stratum_pair_statistics.csv` ve görüntüden kontrol edilmiş
  `comparability.png`; hash'leri makbuzda. Yerel ham/ara çıktılar Git'e
  eklenmez.
- Ana pilot, özellik incelemesi, ayar ve tüketilen iki CSV'nin güncel
  hash'leri başta/sonda ve ayrı geri okumada kontrol edildi. Kaydedilmiş
  modeller açılmadı/değiştirilmedi. Ana kapılar `unknown`/kapalı, nihai
  etiketli birleştirme yok. [Önceki izinli pilot](CONDITIONAL_PU_RANKING_2026-11-20.md).
