# Tamamlanan gözlem yöntem pilotunun sonuçları

Tarih: 15 Ekim 2026. Kapsam, hesap öncesinde sabitlenen **12 eğitim günü,
156 amaçlı hücre-gün**, dört il ve 2018/2021/2023 yıllarıdır. Ana eğitim
özelliklerinin 72 aylık kapsamıyla karıştırılmaz. Bu çalışma günlük gözlem
veya negatif etiket kabulü değildir.

## Gerçek çalışma sonucu

Özel girişli devam:
`outputs/reports/dataset/observation_pilot_run_v1/20261015T134047Z_b6b84ca8/`.
Readback SHA-256:
`51e9f504ad2a6c6334ec37f5d5080b70185d1e35d9c4177c7906fa4032d65885`.
Durum `planned_pairs_processed_method_pilot_only`; başlatıcı `child_completed`.

Gerekli **98/98 çift**, **196 ham dosya**, toplam **17.995.454.761 bayt**
mevcuttur; eksik çift ve kayıtlı hata yoktur. Önceden tamamlanan 86 çift
yeniden kullanıldı, son 12 çift işlendi. Son oturumda yeni aktarım
**2.210.136.100 bayt** olarak kayıtlıdır. Önceki kesintinin tüm ağ trafiği
ölçülmediği için bu değer bütün denemelerin toplam trafiği diye sunulmaz.
Korunan yarım dosya kabul edilen 196 tam dosyadan ayrı tutulur.

292 çiftlik komşu gün referansında kalan 194 çiftin bütün taramaları,
önceki tam native zaman tanığında hedef penceresi dışında doğrulanmıştır.
Yeni ham geometri işinde yalnız gerekli 98 çift işlenmiştir; 194 çiftin
ham dosyalarının burada yeniden açıldığı iddia edilmez.

156 birimin tamamında **planlanan kaynaklar** tamamdır. Bunun anlamı
uygun gün envanterinin karşılanmasıdır; 24 saat kesintisiz görme, bağımsız
yangın yokluğu doğrulaması veya tespit kaçırma olasılığının ölçümü değildir.

## Yerel teknik kapanış

`scripts/quality/review_completed_observation_pilot.py` ağ engelli olarak
çalıştırıldı. 196 ham dosyanın tam boyut/tarihsel SHA ve varsa sağlayıcı
checksum'u, her çiftin tam ham kaynak izi, 98 çiftin makbuz ve çıktı hash'leri
yeniden kontrol edildi. Saklanmış tarama geometrileri yeniden okunarak günlük
özet hesaplandı; önceki 156 satırlık CSV'nin hash'i birebir aynı üretildi:
`12d281f8486ce8202738a48e1838e79189e877f27b99491d9525d71c5e092242`.
Ham piksel geometrisi yeniden hesaplanmadı veya kaynak yeniden indirilmedi.

Sabit kohort/metadata, gün bazında çift sayıları, tam kaynak durumu, boş
hedef, sonlu ve negatif olmayan değerler, tamsayı sayımlar, tarama zaman
sınıflarının korunumu, hücre/sınıf alan sınırları ve 12h ⊆ 6h ⊆ 1h ⊆
nominal kara alanı eşitsizlikleri kontrol edildi. Buradaki ikinci üretim,
aynı yöntemin saklanmış geometri üzerinden tekrarıdır; bağımsız fiziksel
alan doğrulaması değildir.

Yeni çıktı:
`outputs/reports/dataset/observation_pilot_review_v1/20261015T141509Z_6f7a885a/`.

- `unit_diagnostics.csv`: 156 satırda alan payları ve korunan belirsizlikler.
- `source_checks.csv`: 196 ham kaynağın yeniden kontrolü.
- `descriptive_area_cuts.csv`: beş alan kesimi × dört destek ölçüsü;
  tümünde `accepted_label_rule=false`.
- `human_review_examples.csv`: aşağıdaki beş amaçlı açıklama örneği;
  araştırmacı kararı boş.
- `support_diagnostics.png`: kara/tekrar ve kara/bulut ilişkileri;
  grafik araçla okunabilirlik açısından incelendi, insan etiket onayı değil.
- `input_manifest.json`: kapanışta **1.531 girdi dosyası** aynı hash ile.
- `pilot_partial_summary.csv`: önceki özetin aynı hash'li yeniden üretimi.

Readback SHA-256:
`8cd0e4730da5d539996f9e00f8984003c549aa2bb7e0edd9b91879eba3fdd116`.
Kapanış SHA-256:
`eac9060ce8fa75ebdf18c7385b273d9ea4605803b9a7ce5229f1f4071b6c2265`.
**12 yeni davranış vakası dahil 59 ilgili test** geçti; Deprecation/Future
uyarıları hata sayıldı. İki yeni Python dosyasında lint/format geçti.
Bu sayı bütün proje testlerinin yeniden çalıştırıldığı anlamına gelmez.
Denetim sıfır ağ baytı, sıfır bulut işi ve kapalı bilimsel kabul bayraklarıyla
tamamlandı. Yeni kod önceki planın hash ile bağlı bilimsel girdilerini değiştirmedi.

## Gözlem desteği ne gösteriyor?

Payda her satırda EPSG:6933'te AOI ile kesilmiş hücre alanıdır. Paylar,
merkezler arası köşe yaklaşımı ve tarama içi alan rekonstrüksiyonuna
dayanır; fiziksel piksel köşeleri veya bitki örtüsüne özel görünürlük değildir.
Kesin pencere içindeki taramalar ayrı birleşir; sınır taramaları kesin
destek hesabına alınmaz. Farklı sensör/yörüngelerdeki alan örtüşmesi ve
tarama zaman zarfları arasındaki en az 1/6/12 saat ayrım ayrıca hesaplanır.
Bu ayrımlar kabul edilmiş etiket kuralları değildir.

| Tanı | Bu sabit pilotta sonuç | Yorum sınırı |
|---|---:|---|
| Yeniden kurulmuş pencere içi geometrik alan | 156/156 satırda hücre alanına yaklaşık eşit | Kalite veya bulutsuzluk garantisi değil |
| Nominal yangın olmayan kara desteği sıfır | 7/156 | Otomatik negatif etiket verilemez |
| En az 12 saat ayrımlı nominal kara tekrar alanı sıfır | 17/156 | Tek günlük birleşim tekrar desteğini kanıtlamaz |
| Nominal kara alanı hücrenin en az %95'i | 131/156 | Tanısal alan kesimi; seçilmiş etiket eşiği değil |
| En az 12 saat ayrımlı tekrar alanı hücrenin en az %95'i | 100/156 | Aynı %95 kesimin farklı kapsamı; hata oranı değil |
| Zaman sınırında tarama kaydı bulunan hücre-gün | 41/156 | Sınırdaki geometri kesin iç desteğe eklenmez |

Toplam **261.890 tarama/hücre satırı** vardır; bu bağımsız geçiş veya
yangın sayısı değildir. 41 satır `boundary_unknown`, 5.427 satır `outside`
sınıfındadır; kalan 256.422 satır kesin pencere içindedir. Boş alanlı
taramalar bu sayımlarda korunur.

Günlük bulut birleşimi ile nominal kara birleşimi farklı geçişlerde aynı
yeri kapsayabilir. Bu yüzden bu iki payın toplamının biri aşması tek başına
hata değildir; toplamları net gözlenen alan olarak kullanılmaz. İkisi de
kendi içinde aynı sınıfın geometrik birleşimi olarak hesaplanır.

96 satır nominal üründe seçilmiş termal merkez bulunmayan, 60 satır termal
merkez bulunan tanı grubundadır. Bunlar doğrulanmış negatif/pozitif sınıflar
değildir. Mevcut 36 boş seçim kontenjanı doldurulmadı; gün veya hücreler
sonuca göre değiştirilmedi. Amaçlı örneklemden bütün dönem için hata,
duyarlılık veya güvenilir negatif oranı çıkarılmaz.

## İnsan gözüyle bakılacak somut örnekler

Aşağıdaki oranlar AOI ile kesilmiş hücre alanına göre yaklaşık yüzdelerdir.
Amaç etiket seçmek değil, alan/zaman kanıtının neyi desteklediğini incelemektir.
Otomatik seçim ve teknik görsel kontrol, araştırmacı incelemesi sayılmaz;
`researcher_decision` alanları boş bırakılır.

| Hücre / hedef gün | Nominal kara / ≥12 saat tekrar / bulut | Bakılacak nokta |
|---|---|---|
| `C653_R879` / 2018-02-15, Mersin | %0 / %0 / %100 | Kaynaklar tam olsa bile bulutsuz kara kanıtı yok; yangın yokluğu çıkarılamaz |
| `C677_R879` / 2018-11-15, Mersin | %100 / %0 / %100 | Günlük kara birleşimi tamken 12 saat ayrımlı tekrar yok; tek alan oranı yetersiz |
| `C635_R877` / 2018-11-15, Mersin | %100 / %0 / %100 | Bulut/kara farklı geçişlerde aynı alanı kaplar; toplam %200 fiziksel anlık görünürlük değildir |
| `C518_R902` / 2021-05-15, İzmir | %99,16 / %87,19 / %100 | Yaklaşık 9.397.802 m² sınır zamanı kara alanı ayrı tutulur; kesin iç desteğe eklenmez |
| `C655_R884` / 2021-08-15, Mersin | %100 / %100 / %0 | Yüksek destek yöntemin olumlu örneğidir; bağımsız yangın yokluğu doğrulaması değildir |

Tam grid kimliklerinin öneki `E6933_5K_V1_`'dir. İncelemede her satır için
alan ve zaman ayrımının anlaşılır olup olmadığı, hangi ek kanıtın gerekli
olduğu ve gözlem yetersizliğinin korunup korunmadığı not edilir. Yalnız
bu tabloya bakılarak gerçek pozitif/negatif veya başarı oranı onaylanmaz.

## Sonraki bilimsel adım

Bu pilotun teknik kapanışı, gözlem kanıtını daha geniş ve çeşitlendirilmiş
örneklerde kurabildiğimizi sınar. Sıradaki iş, zayıf destek ve tekrar farkı
gösteren somut örnekleri incelemek, yaklaşımın belirsizliklerini kaydetmek
ve bağımsız olay referansıyla sınanabilecek gözlem protokolünü hazırlamaktır.
Yalnız daha çok satır tutmak amacıyla bir alan yüzdesi seçilmez.

`daily_observation_status=unknown`, `negative_label_permitted=false`, boş
hedefler ve kapalı model kapısı korunur. Nihai etiketli birleştirme öncesi
parça kontrolü ve rapor kimliğine bağlı kullanıcı onayı gereksinimi sürer.
