# Olay öncesi görüntü kesitleri ve araştırmacı incelemesi — 23 Ekim 2026

## Gerçekleştirilen iş

Önceki katalog envanterinin aynı 25 eğitim noktası için ilk inceleme
sırasındaki Sentinel-2 görüntüsünden iki küçük raster pencere okundu:
10 m gerçek renkli TCI ve 20 m otomatik sahne sınıflandırması SCL.
Seçim, önceki raporun sahne bulut oranı/tarih sırasıdır; yerel kalite
sonucuna göre sessizce farklı görüntü seçilmedi. 2018, 2021 ve 2023
örnekleri amaçlıdır; bütün olayların kalite oranını temsil etmez.

**25/25 nokta için okuma ve yerel dosya geri kontrolü tamamlandı.**
50 GeoTIFF kesiti toplam 1.773.290 bayttır. Bu yerelde sıkıştırılmış
dosya boyutudur; HTTP aktarım miktarı ölçülmedi. Tam sahneler indirilmedi;
COG dosyalarına pencere erişimi kullanıldı. Google Cloud/EE işi açılmadı.

Katalog kimliği, edinim tarihi, tahmin zamanı, UTM koordinat sistemi,
raster dönüşümü, çözünürlük ve veri tipi kontrol edildi. Kaynak ETag,
son değişiklik zamanı ve boyut başlıkları pencere okumasının öncesi/sonrasında
aynı kaldı. ETag tam sahnenin SHA-256 doğrulaması diye sunulmaz. Yerel
kesitlerin piksel ve maske dizileri yazma sonrası aynı okundu ve hash'lendi.
Geçici erişim bağlantıları yalnız bellekte kullanıldı; raporlarda imzasız
kaynak adresleri tutuldu, token/URL hata mesajları yazdırılmadı.

## Alan ve kalite hesabı

VIIRS kaynağının önceki incelemede üretilmiş yaklaşık alanı Sentinel-2'nin
yerel UTM koordinatlarına taşındı. SCL piksel merkezlerinden bu alan
içinde kalanlar sayıldı. Payda nokta başına 360–1.285 piksel merkezidir;
oranlar bu merkez sayımlarına dayanır, hassas kesişim alanı ölçüsü değildir.
Yaklaşık sınır yangın çevresi veya resmî VIIRS piksel köşesi değildir.

Görsel bağlam için alan çevresine 500 metreye kadar pay eklendi. Bir
örnekte bu pay tile sınırını yaklaşık bir metre aştığı için ilk koşu
15 nokta sonrasında durdu. Tamamlanan kesitler korundu. Yeni kontrol,
yalnız görsel çevrenin tile kenarında kesilmesine izin verir; bilimsel
destek alanı sınırı aşarsa durur. Davranış testiyle doğrulandı. Yeni
koşu 15 kesiti hash/kimlik ve yeniden kalite sayımıyla kullandı, kalan
10 noktayı okudu. Araştırma alanı veya tahmin zamanı değiştirilmedi.

| SCL tanısı | En az bir işaretli pikseli olan nokta / 25 | Nokta içindeki en yüksek oran |
|---|---:|---:|
| Bulut veya sirüs (8/9/10) | 6 | %62,35 |
| Bulut gölgesi (3) | 4 | %5,32 |
| Koyu alan / topoğrafik gölge (2) | 11 | %49,18 |
| Sınıflanmamış (7) | 17 | %23,53 |
| Veri yok veya kusurlu (0/1) | 0 | %0 |
| Kar/buz (11) | 0 | %0 |

Sınıflar için nokta sayıları örtüşebilir; toplanarak ayrı örnek sayısı
hesaplanmaz. Bu dört belirsizlik grubundan en az biri 17 noktada vardır.
Kalan sekiz nokta otomatik kabul edilmedi. TCI geçerli veri maskesi ayrıca
kontrol edildi: yaklaşık alan içinde 25/25 kesitte bütün piksel merkezleri
geçerli maskeye sahipti. Bu, bulutsuzluk veya doğru habitat kanıtı değildir.

SCL otomatik bir algoritmadır; bulut/gölge işareti bağımsız insan doğrulaması
değildir. Tarihsel sınıf 2 koyu alanları da kapsayabilir. SCL 4 yalnız
bitki örtüsüdür; orman, çalılık ve tarımı birbirinden ayırmaz. Bulut veya
habitat kabul eşiği seçilmedi; nokta/kayıt silinmedi.

## Üç somut araştırmacı inceleme örneği

25 ayrı kart ve A/B/C içeren bir özet görsel üretildi. Her kart aynı
coğrafi alan için 2017 örtü haritasını, olay öncesi TCI görüntüsünü ve
SCL sınıflarını gösterir. 100 m referans harita en yakın komşuyla hizalandı;
bu işlem haritayı 10 m bilgiye dönüştürmez. TCI'nin kaynak renk gösterimi
kullanıldı; ek kontrast germe veya üretken görüntü işlemi uygulanmadı.

- **A — SNPP_815579_4958:** 15 Mayıs 2018 tespitinin 23 Nisan görüntüsü.
  Sahne bulutu %0,16629 olmasına rağmen yaklaşık alanın SCL bulut oranı
  %13,10'dur. Araç destekli görsel incelemede yollar, yapılaşma ve parlak
  yüzeyler görülüyor; parlak yüzey/bulut ayrımı kesinleştirilmedi. Araştırmacı
  için önerilen ön not: yapılaşma/çıplak yüzey bağlamı, belirsizlik korunmalı.
- **B — SNPP_815579_17606:** 15 Ağustos 2018 tespitinin 9 Ağustos görüntüsü.
  Tarla parselleri belirgin görünüyor. SCL merkezlerinin %70,19'u bitki
  sınıfında; bu orman anlamına gelmez. Bulut/gölge (3/8/9/10) oranı sıfır,
  koyu alan %0,54, sınıflanmamış %1,79. Önerilen ön not: tarım bağlamı.
- **C — SNPP_815579_146808:** 15 Ağustos 2021 tespitinin 20 Temmuz görüntüsü.
  Ağaçlık örtü ve açıklıklar görülüyor; eski harita yaklaşık alanı orman
  olarak sınıflıyor. SCL bitki %83,92, bitkisiz %16,08; diğer sınıflar sıfır.
  Önerilen ön not: orman/çalılık yönünde örtü bağlamı; tür kesinliği yok.

Bu yorumlar asistanın görüntü incelemesidir. Araştırmacı/uzman incelemesi,
bağımsız olay doğrulaması veya kabul edilmiş etiket olarak kaydedilmedi.
Araştırmacıdan A/B/C için görünür örtü yorumuna katılıp katılmadığı ve
kararsız kaldığı alanları belirtmesi istenir. `human_review_template.json`
25 noktanın değerlendirme, not, inceleyen ve tarih alanlarını boş korur.

### Araştırmacının sonraki teyidi

Araştırmacı A belirsiz, B tarım bağlamı, C orman/çalılık bağlamı ön notlarına
açıkça katıldı. Bu, asistan yorumunun araştırmacı tarafından teyididir;
bağımsız uzman doğrulaması veya kör değerlendirme değildir. A belirsizliği
korunur; B kalıcı dışlanmaz, C otomatik pozitif sayılmaz. Diğer 22 nokta
araştırmacı tarafından incelenmiş sayılmaz.

Donmuş boş şablon değiştirilmedi; üç teyit ayrı sürümlü kayıtta tutuldu:
`outputs/reports/dataset/preevent_researcher_review_v1/20261023T153234Z_ecee9147/readback.json`.
SHA-256 `36fac85b3d6fe2f288af7070b70cfed5b037f70bd5b0601646a2eeb38e184645`.
Kayıt, son görsel raporuna, üç ayrı karta ve A/B/C özetine beş girdi
hash'iyle bağlıdır. Bilimsel habitat kabulü, yangın etiketi veya nihai
birleştirme onayı değildir.

## İzlenebilirlik ve doğrulama

Kesit çıktısı:
`outputs/reports/dataset/preevent_image_windows_v1/20261023T152456Z_e03ae61d/`.
Readback SHA-256:
`a3d1378c3f13a2b1947b045aaa2f296426bdfb4246861160aa83adf3caa6a5f8`.
110 girdi/77 çıktı hash'i sonrasında yeniden doğrulandı. İlk sınırlı
koşu `20261023T152006Z_eda4d264` korunur; 15 tamamlanan örneğin ilk edinim
zamanları yeni makbuzlarda değiştirilmedi.

Son görseller:
`outputs/reports/dataset/preevent_review_cards_v1/20261023T152812Z_f80d7979/`.
İlk düzen `20261023T152544Z_ae830a3b` korunur; son sürümde başlık kısaltılıp
A/B/C işaretleri eklendi. Sunum düzeni kontrolü bilimsel insan incelemesi
olarak kaydedilmedi.

Görsel raporu SHA-256:
`3b91679a93850141ea8c338cc6e275b36c46a4b230571155cc61c8c8d7437d24`.
83 girdi/28 görsel çıktı hash'i geri kontrol edildi; 25 insan inceleme
kaydının değerlendirme alanları boştur.
[A/B/C görseli](../outputs/reports/dataset/preevent_review_cards_v1/20261023T152812Z_f80d7979/three_examples.png).
Görsel SHA-256:
`432f82413b2091dc21a37da812c5b096a8e6ef0003a19b0152f1ff807192e181`.

10 yeni davranış vakası dahil 51 ilgili test geçti: kalite paydası,
veri maskesi, alan dışı bulut, bilinmeyen sınıf, boş destek, pencere sınırı,
yalnız çevreyi kesme, önceki zaman ve etiket/birleştirme korumaları.
Yeni dört Python dosyasında lint/format denetlendi. Sonuçlar otomatik
etiket veya bütün veri setinin kabulü anlamına gelmez.

## Sıradaki iş

Bulut/gölge ve parlak yüzey belirsizliği bulunan noktalarda envanterdeki
diğer olay öncesi tarihlerle karşılaştırma yapılmalı. Üç araştırmacı ön notu
ayrı kanıt olarak korunur; genel "devam" kalan örneklerin görsel onayı değildir.
Bağımsız yangın kimliği ve yeterli günlük gözlem ayrı açık konulardır.
Görüntü kontrolü sırasında 2024/2025 açılmadı; boş hedefler ve
`daily_observation_status=unknown` korundu, nihai birleştirme yapılmadı.

## Birincil kaynaklar

23 Ekim 2026 erişimi:
[Copernicus SCL açıklaması](https://sentiwiki.copernicus.eu/web/s2-processing)
kalite sınıflarının ve algoritmanın niteliğini açıklar.
[Microsoft açık veri SDK'sı](https://github.com/microsoft/planetary-computer-sdk-for-python/blob/main/planetary_computer/sas.py)
geçici salt okunur varlık erişimi yönteminin kaynağıdır. Bu kaynaklar yerel
sonuçların yerine geçmez; sayılar korunan kesitlerden hesaplandı.
