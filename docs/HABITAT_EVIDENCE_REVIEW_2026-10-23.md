# Orman/çalılık ve yönetilen arazi ayrımı: inceleme kaydı

23 Ekim 2026. Kullanıcının orman yangınlarına odaklanma vurgusu, önceki
orman+çalılık kapsam yönü korunarak ele alındı. Çalılık kapsamdan çıkarılmadı.
Bu çalışma kabul edilmiş nihai habitat filtresi veya yangın etiketi değildir.

## Somut bulgu ve kapsam

25 eğitim tespitinin eski örtü haritası, yaklaşık native piksel desteği,
yerel görüntü kalite sayımı, önceki üç araştırmacı notu ve olay adaylarına
bağlantısı tek inceleme paketinde toplandı. 25 nokta, 21 hücre-gün adayı
ve 207 farklı senaryo–küme–nokta ilişkisi vardır. 207 ilişki bağımsız
yangın sayısı değildir. 21 adayın 15'i gruplama senaryolarında varlık,
zaman ve üyelik açısından eşit; dördü varlık, ikisi zaman/üyelik duyarlıdır.

| Eski harita üzerinden inceleme sırası | Nokta | Anlamı |
|---|---:|---|
| Merkezi orman/çalı | 4 | Doğal odunsu örtü ile yönetilen odunsu tarım ayrıca ayrılmalı |
| Merkezi başka sınıf, yaklaşık alanda orman/çalı kesişimi var | 9 | Karışık alan/konum belirsizliği incelenmeli |
| Yaklaşık alanda eski haritaya göre orman/çalı kesişimi yok | 12 | Diğer örtü bağlamı incelenmeli; otomatik dışlama yok |

Bu 4/9/12 dağılımı yeni ölçümle bir orman kabulü değildir; korunmuş 2017
harita ölçümlerini inceleme kuyruğuna ayırır. Amaçlı 25 örnek bütün eğitim
adaylarını temsil etmez. 25 noktanın tamamı korundu; hedefler boş kaldı.

## Harita neden tek başına yetmiyor?

Kullanılan Copernicus ürününün sınıf açıklaması, çok yıllık odunsu tarım
bitkilerinin uygun orman veya çalı sınıfında yer alabileceğini açıklar.
Dolayısıyla haritada orman/çalı görülmesi doğal orman yangını kapsamını
tek başına doğrulamaz. Ayrıca referans harita 2017 yılına aittir.
[Birincil katalog açıklaması, sınıf 40](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_Landcover_100m_Proba-V-C3_Global)
(23 Ekim 2026 erişimi). Görsel yeşillik ve SCL bitki sınıfı da bu ayrımı
tek başına yapmaz. Bu genel sınırlama belirli noktanın kesin meyve bahçesi
veya kesin yanlış haritalanmış olduğu iddiası değildir.

## Araştırmacıya sunulan dört örnek

[D/E/F ve önceki C görseli](../outputs/reports/dataset/habitat_evidence_review_v1/20261023T155415Z_9d1f8433/forest_shrub_focus.png).
Görsellerdeki oranlar eski haritadaki sınıf alanıdır; ağaç taç örtüsü veya
güncel doğal orman yüzdesi değildir. Sarı alan yaklaşık tespit desteğidir.

| Kod / nokta | Görüntü tarihi | Eski harita orman+çalı payı | Asistanın yeni ön yorumu |
|---|---|---:|---|
| D / N20_815590_159856 | 2021-10-08 | %66,71 | Ağaçlık, parseller, yol ve yapılaşma bağlamı karışık |
| E / N20_815590_196908 | 2022-12-19 | %95,92 | Düzenli parsel/şerit görünümü ve odunsu çevre birlikte; doğal örtü ayrımı belirsiz |
| F / N20_815590_33762 | 2018-11-06 | %87,44 | Parseller, yapılar ve odunsu şeritler birlikte; doğal örtü ayrımı belirsiz |
| C / SNPP_815579_146808 | 2021-07-20 | %100,00 | Önceki araştırmacı orman/çalılık ön notu korunuyor |

Üç yeni ön yorum kullanıcıya somut görselle sunuldu; bu kaydın üretiminde
yeni araştırmacı teyidi yoktur. Görüntüdeki parsel görünümü tek başına tarım
veya kapsam dışılık kabulü değildir. Eski A/B/C notları değiştirilmedi.

## Önerilen inceleme protokolü — üretim kabulü değil

1. **Konum ve ölçek:** Tespit merkezi, yaklaşık piksel alanı ve 5 km hücre
   ayrı tutulur. Hücrenin başka köşesinde orman bulunması tespiti ormana
   atfetmez. Yaklaşık köşeler ve residual bowtie gibi sınırlamalar korunur.
2. **Zaman ve görünürlük:** T öncesi görüntü tarihi, eski harita yaşı,
   bulut/gölge/parlak yüzey belirsizliği kaydedilir. Görünmeyen alanın
   sınıfı tahmin edilerek kesinleştirilmez. Yeniden işlenmiş ürünün geçmişte
   erişilebilirliği ayrıca doğrulanmadan model girdisi kabul edilmez.
3. **Doğal ve yönetilen örtü:** Doğal odunsu alan görünümü, düzenli
   parsel/sıra görünümü, yapılar ve karışık alan ayrı sorulur. Her soruda
   evet/hayır/belirsiz mümkün olmalı; neden ve bağlı görsel kimliği yazılmalı.
   Bu alanların yeni şablondaki başlangıç değeri boştur, otomatik doldurulmaz.
4. **Kapsam yorumu:** Orman, çalı, yönetilen odunsu tarım, diğer tarım,
   yapılaşma/tesis, diğer doğal örtü ve karışık/belirsiz birbirine
   indirgenmez. Bu aşamada minimum pay veya alan eşiği seçilmedi.
5. **Olayı ayrı değerlendirme:** Orman/çalılık bağlamı bulunması gerçek
   yangın kimliği, yeni olay veya yeterli gözlem kanıtı değildir. Tesis
   görünümü de tek başına termal kaynağın nedeni veya olayın dışlanması
   değildir. Birden çok ilk hücre ortak olay adayı bağını korur.
6. **Kayıt ve karar:** Araştırmacı notu, asistan yorumu, otomatik harita ve
   bağımsız olay kanıtı ayrı tutulur. Belirsiz örneğe 0/1 atanmadan
   inceleme gerekçesi korunur. Üretim filtresi bu taslakla açılmaz.

Sonraki adım D/E/F inceleme notlarının alınması ve karışık/odunsu tarım
şüphesinde hangi ek kanıtın gerekli olduğunun örnek bazında belirlenmesidir.
10 m görüntüyle ayrım yapılamayan örnekler için daha yüksek ayrıntılı,
uygun tarihli bir kaynak veya belgelenmiş arazi kullanım bilgisi gerekir;
bu erişimin mevcut olduğu iddia edilmez. Tüm veri için yeni indirme
kuyruğu açılmadı. Nihai parça kontrolü ve birleştirme onayı ayrıca gereklidir.

## Çıktı ve kontroller

`outputs/reports/dataset/habitat_evidence_review_v1/20261023T155415Z_9d1f8433/`:

- `point_evidence.csv`: 25 nokta, ayrı kanıt alanları ve kabul edilmemiş kapsam.
- `point_case_relations.csv`: 207 ilişki; senaryo üyelikleri birleştirilip kaybedilmez.
- `review_index.md`: 25 eski kartın bağlantıları ve önceki araştırmacı notları.
- `new_review_template.json`: 25 boş yeni gözlem şablonu; eski notların yerine geçmez.
- `forest_shrub_focus.png` ve `focus_order.json`: D/E/F/C inceleme sayfası.
- `input_manifest.json` ve `readback.json`: kaynak ve çıktı kimlikleri.

Readback SHA-256: `abbd061abb08013da6fdf9583c175c4072b041c76abb22819e2d0bdda5b5ca3f`.
Görsel SHA-256: `312825129ab22e084fe8965d21bb5cfd8c3b2be566ddba2ff8795d7fdd69ccc6`.
166 girdi/7 çıktı hash'i yeniden doğrulandı. İki CSV tam geri okundu;
None/NaN boş değer gösterimi eşdeğerliği hakkında pandas gelecek sürüm
uyarısı verdi, mevcut içerik kontrolü geçti. 25 şablonda yeni insan
değerlendirmesi boş, 25 hedef boş, eski üç not korunmuş durumdadır.
Dokuz yeni davranış vakası dahil 37 ilgili test ve üç dosyada lint/format
kontrolü geçti. Ağ kapalıydı; bulut işi, 2024/2025 erişimi, eğitim, etiket,
otomatik silme ve nihai birleştirme yapılmadı.

## Görsel sunumu sonrası araştırmacı değerlendirmesi — 23 Ekim

Araştırmacı C'nin önceki orman/çalılık ön yorumunu yeniden teyit etti.
D'de ağaçlık alan bulunduğunu, ancak görünen payın yaklaşık %66'dan daha
az göründüğünü belirtti. Bu ifade yeni bir sayısal ölçüm değildir: görselde
yazılı %66,71, 2017 sınıf haritasının yaklaşık destek içindeki orman+çalı
alan payıdır; 2021 görüntüsündeki ağaç taç örtüsü yüzdesi değildir.
İki miktar eşdeğer kabul edilmedi ve eski oran değiştirilmedi.

E ve F için araştırmacının ön yorumu tarla benzeri, yeşil fakat orman gibi
görünmeyen alanlardır. Asistan yorumu da düzenli parsel görünümünün tarımsal
kullanım olasılığını desteklediği yönündedir. Kesin tarım türü, doğal odunsu
örtü yokluğu veya yanlış sınıflama kanıtlanmadı. E/F doğal orman olarak
kabul edilmedi; D karışık/belirsiz tutuldu. Hiçbir kayıt silinmedi veya
negatif yangın etiketi almadı.

Yeni makbuz: `outputs/reports/dataset/habitat_researcher_notes_v1/20261023T160518Z_3166f1d9/readback.json`.
SHA-256: `d3e71111b30cc6686eee9319165d9b86b25f9d6c1f2811c4dcbca3ab3e1495fb`.
Beş kaynak hash'i ve yeni JSON geri okuması doğrulandı. Önceki şablonlar ve
notlar değişmedi. Üç yeni nokta ve C'nin tekrar teyidiyle toplam **6/25**
noktada araştırmacı ön notu var; **19/25** noktada yok. Bu, kör/bağımsız
uzman değerlendirmesi veya altı kabul edilmiş habitat örneği değildir.
Kod değişmediği için bilimsel kuyruk veya test paketi yeniden çalıştırılmadı.

Sonraki incelemede E/F'nin tarımsal parsel bağlamı, D'nin alan içi karışımı
ve diğer 19 noktanın örtüsü aynı ölçütlerle ele alınmalı. Bu altı amaçlı
örnekten genel otomatik filtre eşiği çıkarılmamalıdır.

## Kalan 19 noktanın asistan ön incelemesi — 23 Ekim

Altı araştırmacı ön notu korunarak diğer 19 nokta dört görsel sayfada
toplandı. Yeni görüntü indirilmedi; mevcut ilk tarih kesitleri ve bu
noktalardan beşinin mevcut üç tarihli kartları incelendi. Bu aşama
asistan görsel yorumudur; yeni araştırmacı/uzman doğrulaması değildir.

| Ön yorum grubu | Nokta sayısı | Görsel kodları |
| --- | ---: | --- |
| Yapı/tesis benzeri bağlam | 6 | R01, R04, R05, R12, R13, R14 |
| Düzenli parsel bağlamı | 4 | R02, R06, R17, R18 |
| Karışık örtü; doğal/yönetilen ayrımı açık | 6 | R03, R07, R11, R15, R16, R19 |
| Açık/kuru yüzey ve seyrek, niteliği belirsiz örtü | 3 | R08, R09, R10 |

Sayılar amaçlı seçilmiş 25 eğitim noktasının henüz araştırmacı notu
olmayan 19'una aittir. Genel veri dağılımı, yangın sınıfı veya otomatik
eleme kuralı çıkarılamaz. Yaklaşık alanların örtüşmesi nedeniyle bu
noktalar bağımsız arazi örnekleri de sayılmadı.

Somut bulgular ve açık sorular:

- R03'ün ilk görüntüsünde görüşü bulut kapatıyor. Mevcut 3 Nisan ve
  1 Mayıs 2023 alternatiflerinde düzenli parlak/sera benzeri örtüler,
  parseller ve yeşil parçalar birlikte görülüyor. Doğal odunsu örtü
  ile yönetilen bitki örtüsü ayrımı henüz doğrulanmadı.
- R11'de yakın çevrede odunsu görünümlü doku var; yaklaşık alanın
  merkezindeki açık yüzey ve sınırdaki karışım ayrıca ele alınmalı.
  Görselin dış çevresi, sarı sınırın içindeki örtüyle aynı sayılmadı.
- R15/R16'da yeşil koridor ile sera benzeri yapılar yan yana. R15'in
  önceki residual bow-tie belirsizliği korunuyor; bu görüntü onu çözmez.
- R12'de kıyı, iskele benzeri uzantılar ve dairesel tesis yapıları
  üç tarihte görülüyor. Tesis kimliği ve tespit edilen sıcaklığın
  nedeni belirlenmedi; endüstriyel kaynak veya yanlış yangın kaydı
  olduğu sonucuna varılmadı.
- R08/R09/R10 için kuru görünüm, doğal çalılık yokluğu anlamına gelmez.
  Mevcut çözünürlükle bitki türü ve kullanım ayrımı belirsiz kaldı.

Görsel dizini:

- [R01–R05](../outputs/reports/dataset/remaining_cover_review_v1/20261023T162553Z_e9d8f8dd/sheet_1.png)
- [R06–R10](../outputs/reports/dataset/remaining_cover_review_v1/20261023T162553Z_e9d8f8dd/sheet_2.png)
- [R11–R15](../outputs/reports/dataset/remaining_cover_review_v1/20261023T162553Z_e9d8f8dd/sheet_3.png)
- [R16–R19](../outputs/reports/dataset/remaining_cover_review_v1/20261023T162553Z_e9d8f8dd/sheet_4.png)
- [R03 üç tarih karşılaştırması](../outputs/reports/dataset/preevent_date_comparison_v1/20261023T154219Z_144befb7/N20_815590_200133.png)

Görsel makbuz SHA-256:
`af1cc416aac93dffa2ed9e0a40589675f7b8b4bb74a3e0cc0988baad6f0f5ad7`.
Asistan notları ayrı kayıtta:
`outputs/reports/dataset/remaining_cover_assistant_notes_v1/20261023T162753Z_e27e3f04/readback.json`;
SHA-256 `7cdaf55d02672447304c7ac2182368f2ff4fa744558edfe899be3a70cf6bae9c`.

140 kaynak hash'i ve altı çıktı hash'i doğrulandı. Notların bağlı olduğu
10 görsel/makbuz hash'i ve 19 tekil kimliğin geri okuması kontrol edildi.
Dört sayfa ve beş alternatif kart görsel olarak asistan tarafından incelendi.
Bu değişiklik yalnız sunum/not üretimidir; bilimsel üretim yeniden
çalıştırılmadı. Yeni betiğin lint/format kontrolü geçti.

Toplam insan ön notu hâlâ 6/25, yeni asistan ön notu 19/19'dur.
Araştırmacı değerlendirmesi, habitat kabulü, olay kanıtı ve gözlem yeterliliği
ayrı tutuldu. Yeni etiket, dışlama, nihai birleştirme ve bulut işi yoktur.
Sonraki adım görsel kodlarına bağlı araştırmacı notlarının alınması ve
belirsiz kalan örtü için gereken ek kanıtın belirlenmesidir. Araştırmacı
bir alanı bu görüntüden ayıramıyorsa belirsizlik korunur; zorunlu bir
orman/tarım seçimi yaptırılmaz.
