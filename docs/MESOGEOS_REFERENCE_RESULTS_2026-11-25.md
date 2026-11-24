# Mesogeos yardımcı kaynak pilotu — 25 Kasım 2026

## Yapılan iş ve kapsam

Araştırmacının somut A önerisinden sonraki devam talimatıyla sınırlı yardımcı
kaynak incelemesi yürütüldü. Önceki [öneri](MESOGEOS_REFERENCE_PROPOSAL_2026-11-25.md)
değiştirilmedi; yürütme kapsamı ayrı
`configs/mesogeos_reference_pilot_execution_v1.json` kaydındadır.
Bu çalışma yeni S üyeliği, Y=1, kabul edilmiş L, yeni model veya nihai
etiketli birleştirme değildir. Mevcut özellikler ve modeller korundu.

Beş açık vektör dosyası toplam **159.822.559 bayt** olarak alındı. İlk
çalışmanın başlangıcından geometri devamının tamamlanmasına kadar **468,906
saniye** geçti; 900 saniyelik sınır aşılmadı. HTTP çalışanı SHP isteğinde
Google indirme uyarısı görünce durdu ve kısmi çıktısını korudu. Asistan,
yetkilendirilmiş aynı açık dosyayı normal tarayıcı indirmesiyle tamamladı;
bu adım araştırmacının elle yaptığı iş olarak sunulmaz. Ayrı devam kaydı,
tamamlanmış dosyanın boyut/hash kontrolüyle üretildi. İlk durma makbuzu
başarılı indirme makbuzu olarak değiştirilmedi. İndirme sağlayıcısından
bağımsız bir checksum doğrulaması yapılmış sayılmaz.

## Ölçülen bulgular

DBF başlığında 23.225 kayıt ve 34 alan var. Önce yalnız yıl alanı okunarak
13.325 kapsam dışı/uygun yıl taşımayan kaydın bilimsel alanları açılmadı.
İzinli 2018–2022 yıllarından 9.900 genel kayıt çözümlendi; dört il AOI'si
içindeki kaynak noktaları **92 kayıt** verdi. Kaynak kimlikleri farklıdır;
bu, bağımsız veya eksiksiz 92 gerçek yangın kanıtı değildir.

| Ham kaynak yılı | Dört ilde seçilen kayıt |
|---|---:|
| 2018 | 6 |
| 2019 | 14 |
| 2020 | 15 |
| 2021 | 40 |
| 2022 | 17 |
| Toplam | 92 |

Kaynak CRS'si EPSG:5643, karakter kodlaması ISO-8859-1. Kaynak WKT
noktası ile enlem/boylam alanları arasındaki geri dönüş mesafesi yaklaşık
0,00076–0,00091 metredir. Bu **dosya içi sayısal tutarlılık** kontrolüdür;
gerçek başlangıç konumunun hata payı değildir.

`IGNITION_D` ile `ACQ_DATE` ham takvim günü 92/92 kayıtta aynı; saat
biçimi 92/92 kayıtta çözümlenebilir. Saatin gerçek anlamı/onset doğruluğu
kabul edilmedi (`clock_semantics_accepted=false`). Yazarın hazır örnek
kodundaki eksi bir gün dönüşümü uygulanmadı. Ham tarihle mevcut takvimde
adres aramak hedef pencere eşleşmesini kanıtlamaz.

Yalnız seçilen 92 kaynak sırasının geometrileri açıldı; SHX/SHP sıra
eşliği ayrıca okundu. **92 geometri geçerli** ve AOI ile kesişiyor.
Nokta/son yanmış alan ilişkisi:

- 30 nokta alanın içinde veya sınırında.
- 62 nokta alanın dışında; tüm dış noktalar kaynak projeksiyonunda 1 km'den yakın.
- Bütün 92 kaydın nokta–alan mesafesi: en az 0 m, ortanca 207,36 m,
  en çok 943,07 m.

Bu örüntü yazar yöntemindeki 1 km arama çevresiyle uyumludur; gerçek
tutuşma yeri, aynı olay kimliği veya doğal orman/çalılık yangını olduğunu
doğrulamaz. Kaynak aktif yangın ürünleriyle ilişkilendirildiğinden,
FIRMS'ten tamamen bağımsız hedef doğrulaması olarak sunulamaz.
[Birincil yöntem yayını](https://proceedings.neurips.cc/paper_files/paper/2023/file/9ee3ed2dd656402f954ef9dc37e39f48-Paper-Datasets_and_Benchmarks.pdf).

## Mevcut S/U takvimine yalnız bağlam bağlantısı

Ham noktanın mevcut 5 km grid anahtarı ve değiştirilmemiş ham tarihiyle
44.082 kayıtlık donmuş üyelik tablosunda yalnız adres arandı. 92 farklı
hücre–gün, 81 farklı hücreye karşılık geliyor:

| Mevcut tablodaki durum | Kaynak kaydı |
|---|---:|
| Aynı ham gün/hücrede en az bir önceki S aday önerisi | 60 |
| Anahtar mevcut, S atanmamış U bağlamı | 5 |
| Anahtar önceki kaynak koşullu takvimde yok | 27 |

**32 farklı durum = 5 + 27**; 32 yeni yangın veya yeni S kabulü değildir.
Takvimde bulunmamak bölgenin mevcut ham özellik kaynaklarında bulunmadığı
anlamına gelmez. Eski S/U tablosuna satır eklenmedi; üyelikler değiştirilmedi.
Hedef ve kabul edilmiş L boş, gözlem durumu unknown, negatif izni false kaldı.
2023–2025 bilimsel değerleri açılmadı; yeni fit/tahmin ve renk sınıfı yok.

## Doğrulama ve kayıt bütünlüğü

Bu devamda **53 ilgili test** geçti: yeni yıl/alan/saat davranışları,
önceki referans hazırlığı ve nihai birleştirme kapısı. Ayrı denetim ham
DBF seçimlerini, 92 geometrinin sıra/CRS/geçerlik/mesafesini, değişmez
S/U tablosunu ve 60/5/27 bağlam sayımlarını geri okudu. Özet şeklin üç
paneli asistan tarafından görüntü olarak incelendi; insan yangın veya
örtü onayı değildir.

İlk çalışanın `child.log` hash'i son stdout satırından önce alınmıştı;
çalışan kapanınca yalnız bu akış dosyasının hash'i değişti. CSV/JSON ve ham
bilimsel dosyaların hash'leri eşleşti. İlk makbuz değiştirilmedi. Ayrı
geometri devamı, kapanmış logun ve launcher makbuzunun hash'ini kaydetti;
sonraki denetim bu kapanış anlık görüntüsünü doğruladı. Bu istisna bütün
ilk hash'lerin eşleştiği şeklinde sunulmaz.

Bütün aşağıdaki yollar `outputs/reports/dataset/` altındadır; UTC çalışma
kimlikleri 24 Kasım, yerel inceleme tarihi 25 Kasım'dır.

| Çıktı dizini | readback.json SHA-256 |
|---|---|
| `mesogeos_reference_pilot_run_v1/20261124T231948Z_e9a7e57e` | `4809a268855b573c7290e780fcef960ea37c178348b6fdb8a83acb30e1c45138` |
| `mesogeos_reference_geometry_review_v1/20261124T232735Z_136d2a12` | `60f4cdd519a58982dcffd0476f0758e0c03b59cb0159bffaa1d1346d3d4b3c1e` |
| `mesogeos_reference_pilot_audit_v1/20261124T233152Z_7d080df8` | `544f5fe7490ae72ec109bed48d6cd60be09404784bfd0baf540136e263ba1d44` |
| `mesogeos_reference_context_summary_v1/20261124T233320Z_8e214f1b` | `0cbc801c11c1336c13d4c03ef905eb6616dd1e3f411b23bd2891821b4ee3426e` |

Son özetin `point_perimeter_context.png` şekli nokta içeride/ortadaki
dış nokta/en uzak dış nokta seçimini gösterir. Mavi yanmış alan, siyah
kaynak noktası ve 1 km kesik çevre kullanılır; görüntü nokta çevresine
kırpılmıştır. Uydu fotoğrafı, temsilî örneklem veya risk haritası değildir.

## Sonraki yöntem seçimi

Yardımcı referans pilotu tamamlandı; aynı indirme tekrarlanmayacak.
Önerilen sonraki yön: 32 farklı durum için kaynak saati/hedef günü,
yeni olay ve yerel orman/çalılık şartlarını sınayan **ayrı hata içerebilen
S önerisi hazırlığı**. Bu, kaynağı öğrenme üyeliğine aday yapacağı için
önceki yalnız yardımcı inceleme kapsamından farklı bir yöntem tercihidir.
Alternatif, 92 kaydı yalnız yardımcı kanıt olarak tutup eski S/U ile devam
etmektir. İki durumda da gerçek Y/L kabulü ve yeni eğitim ayrıca gerekçelendirilir;
bu rapor nihai birleştirme onayı değildir.
