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
