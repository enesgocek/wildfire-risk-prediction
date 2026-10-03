# Uydu gözlem alanı — yöntem ve doğrulama kaydı

3 Ekim 2026. Yalnızca 2018–2023 eğitim dönemi örnekleri. Nihai etiket veya
kesin günlük gözlem maskesi değildir; 2024'ten kural seçilmedi, 2025 açılmadı.

## Veri ve yöntem sınırı

İndirilen geolocation dosyalarında merkez enlem/boylamları, tarama zamanları
ve kalite bilgileri mevcut; hazır piksel köşe koordinatları bulunmuyor.
[NASA L1 kılavuzu](https://ladsweb.modaps.eosdis.nasa.gov/api/v2/content/archives/Document%20Archive/Science%20Data%20Product%20Documentation/NASA_VIIRS_L1B_UG_August_2021.pdf)
merkez konumları ve tarama alanlarını açıklıyor. Resmî doküman kopyaları,
adresleri ve SHA256 değerleri yerelde `area_method_sources/` altında.

[NASA C2 aktif yangın kılavuzuna](https://ladsweb.modaps.eosdis.nasa.gov/archive/Document%20Archive/Science%20Data%20Product%20Documentation/VIIRS_C2_AF-375m_User_Guide_1.2.pdf)
göre 375 m ürününde her tarama 32 dedektör satırı içerir. Komşu taramalar
örtüşebilir; dolayısıyla tüm diziye tek bir kesintisiz görüntü gibi köşe
interpolasyonu uygulanmadı. Sabit 375 × 375 m kareler de kullanılmadı.

`scan_interior_center_midpoints_v1_approximate` yalnızca araştırma amaçlıdır:

- Konumlar EPSG:6933 eş alan koordinatlarına dönüştürülür. Her tarama ayrı işlenir.
- Aynı taramadaki dört komşu merkez ortalaması yaklaşık köşeyi oluşturur.
- Taramanın ilk/son satırı ve görüntünün ilk/son sütunu yeniden oluşturulmaz.
  Eksik komşu ve 10 km'den büyük yerel açıklıkta ekstrapolasyon yapılmaz.
  10 km sınırı geometri kontrolüdür; gözlem/etiket eşiği değildir.
- Yaklaşık poligon, merkezi pilot dışında olsa bile hücrenin pilot içindeki
  parçasıyla kesişiyorsa hesaba girer. İl sınırları ve delikler korunur.
- Alan, parçaların **geometrik birleşiminden** hesaplanır. Aynı taramadaki,
  farklı taramalardaki ve iki sensördeki örtüşme tekrar alan eklemez.
- Yeniden oluşturulan alan, sınıf 5 nominal girdili/artık bowtie olmayan
  yangınsız kara ve bulut ayrı tutulur. Yangın pikselleri yangınsız kara sayılmaz.
  Farklı taramalar aynı alanı farklı sınıflandırabileceğinden sınıf alanları
  toplanıp bir bölümleme veya gözlem süresi çıkarılamaz.
- Payda, hücrenin pilot içindeki tüm alanıdır; henüz bitki örtüsü alanı değildir.

Bu yaklaşık poligon **resmî sensör ayak izi değildir**. Kesin alt/üst alan
sınırı iddiası yok. Ölçülen geometri ve hesap doğruluğu, fiziksel ayak izi
doğruluğundan ayrı tutulur. Paylarda 1'e çok yakın kayan nokta sapmaları
korunur; bağımsız kontrolde sayısal toleransla sınanır.

## Tarama zamanı

Yerel `scan_start_time`, `scan_end_time`, `ev_mid_time` dizileri doğal sırada
okunur. TAI93 dönüşümünde dosyanın `TAI93_leapseconds` değeri kullanılır; bu
örneklerde 10 saniye. Dönüşüm nominal UTC aralığıyla sınanır. Tarama sayısı
32 satır yapısıyla, zaman sıralaması ve kalite/mod dizileriyle doğrulanır.

Bazı son taramalar dosyanın nominal bitişini geçer; bu bilgi CSV'de korunur.
Nominal dosya aralığı gerçek piksel zamanı yerine kullanılmaz. Modelin
`(T,T+24h]` aralığı için tarama zarfı tamamen içerideyse `inside`, tamamen
dışarıdaysa `outside`, sınıra değiyor/kesişiyorsa `boundary_unknown` raporlanır.
Tarama zarfı kesin piksel alım saniyesi veya kesintisiz 24 saat gözlem değildir.

## Gerçek veri üzerinde tamamlanan çalışma

13 Ocak 2019 01:00 kontrolü ve 14 Ocak'ın beş S-NPP/üç NOAA-20 örneği işlendi.
Her çıktıda 2.899 hücre korunur. Kaynak dosya ve önceki denetim özetleri
doğrulanır; ham maskeler ve mevcut aday/meteoroloji tabloları değiştirilmez.

13 Ocak kontrolünde yaklaşık yeniden oluşturulan alan 28.856,745 km²;
nominal yangınsız kara birleşimi 9.078,883 km². Bunlar tek geçişin yaklaşık
tanı değerleridir. 203 tarama gece modunda ve tarama kalite değerleri sıfır.
Son tarama nominal bitişi geçiyor. 14 Ocak'ın iki sensörlü yaklaşık alan
birleşimi ayrı yerel raporda; nihai etiket tablosuna aktarılmıyor.

Sekiz geçişin nominal yangınsız kara alanı yaklaşık 36.011,819 km²; tüm pilot
paydasına göre %59,30. S-NPP yaklaşık 33.428,676 km², NOAA-20 11.158,228 km²;
iki sensörün örtüşmesi 8.575,085 km². NOAA-20'nin eklediği yaklaşık alan
2.583,143 km². Bu değerler merkez bulunan hücre sayılarıyla aynı ölçü değildir.
Bulutun en az bir taramada kapladığı alan da yaklaşık 60.726,555 km²;
kara ve bulut birleşimleri farklı zamanlarda örtüşebilir. %59,30, bütün gün
bulutsuz alan yüzdesi veya bir günlük negatif etiket kriteri değildir.

Üç FIRMS kontrol pikseli için yaklaşık kenarlar ayrıca WGS84 jeodezik
mesafeleriyle, arşivin yuvarlanmış `scan`/`track` boyutlarıyla karşılaştırıldı:

| FIRMS kaydı | Yaklaşık scan / arşiv (km) | Yaklaşık track / arşiv (km) |
|---|---|---|
| SNPP_815579_37380 | 0,5350 / 0,49 | 0,6782 / 0,65 |
| SNPP_815579_37382 | 0,5009 / 0,49 | 0,6787 / 0,65 |
| SNPP_815579_37383 | 0,4953 / 0,49 | 0,6791 / 0,65 |

Scan yönünde fark yaklaşık %1,1–9,2, track yönünde %4,3–4,5. Bu üç kontrol
ölçümü üretim için fiziksel doğruluk onayı veya hata üst sınırı değildir;
arşiv boyutları da yuvarlanmıştır. Merkez aralıklarından çıkarılan poligon ile
sensörün fiziksel görüş alanı aynı kabul edilmeyecek. Kontrol tespitlerinin
79/80 numaralı taramaları 01:02:20,871–01:02:23,214 UTC içinde; arşivdeki
01:02 dakikasına uyuyor. Tek tek piksel alım saniyesi çıkarılmadı.

## Denetimler ve üretime geçiş koşulları

14 geometri/alan testi ve 8 zaman/birleşim testi eklendi. Analitik alanı bilinen
geometriler, AOI dışındaki merkez, delikli sınır, yinelenen/örtüşen poligon,
tarama sınırı, eksik komşu, bozuk geometri, TAI dönüşümü, açık/kapalı hedef
uçları ve tutulmuş yıl koruması sınanır. Bozuk geometri otomatik onarılıp
gizlenmez. Tüm hücrelerin günlük durumu `unknown`; negatif izin `False`.

Yerel bağımsız geri okuma, GPKG geometrilerinden alanı tekrar hesaplar; CSV/JSON
toplamlarını ve paydaları, kaynak özetlerini, AOI dışına taşmayı ve tüm hücrelerin
korunmasını kontrol eder. Tarama saatleri ayrıca standart datetime aritmetiğiyle
sınanır. Sekiz geçişin birleşimi, tüm kaydedilmiş geometrilerin bağımsız global
birleşimiyle karşılaştırılır. Bunlar hesap/geometri tutarlılığı kontrolleridir;
yaklaşık fiziksel sınırın doğruluğunu kanıtlamaz.

Bu geri okuma tamamlandı: dokuz kaynak/geometri/alan/saat denetimi ve sekiz
geçişin bağımsız global birleşimi geçti. Toplam 123 otomatik test ve kod/biçim
kontrolleri başarılı. Bu sonuç fiziksel doğruluk veya nihai etikete onay değildir.

Nihai gözlem kullanımından önce açık işler:

1. Fiziksel ayak izi yöntemi/yeniden örnekleme yaklaşımı ve hata payı daha geniş
   tarama açısı, arazi ve iki sensör kontrolünde doğrulanmalı; gerekiyorsa
   NASA geolocation algoritması veya uygun resmî ürünle desteklenmeli.
2. Tarama modu/kalitesi, artık bowtie ve gece/gündüz için kullanım kuralı
   eğitim verisinde seçilmeli. Geçiş sayısı ve gözlemsiz zaman boşlukları
   mekânsal alan birleşiminden ayrı incelenmeli.
3. Bitki örtüsü paydası ve eksik gözlem kararı belirlenmeli; gözlenmeyen örnek
   otomatik negatif sayılmamalı. NASA Type üretim teyidi ayrıca açık.
4. Tam dönem veri edinme/hesap planı katalog üzerinden boyutlandırılmalı.
   İncelenen 14 Ocak'ın sekiz ham çifti yaklaşık 1,36 GiB. Bu tek gün temsilî
   olsaydı 2.191 eğitim günü yaklaşık 2,91 TiB ederdi; bu yalnızca ölçek senaryosu,
   tam dönem katalog envanteri veya kesin indirme gereksinimi değildir.

## Yerel çıktılar

`outputs/reports/observation_coverage/` altında:

- `l2_sample_*_area_estimate.json/.csv/.gpkg`: dokuz örneğin yaklaşık alanı,
  üç ayrı geometri katmanı ve kaynak özetleri.
- `l2_sample_*_scan_times.csv`: doğal tarama sırası, UTC zaman zarfı/mod/kalite.
- `l2_area_union_2019-01-14_SNPP_N20_8samples.json/.csv/.gpkg`: aynı alanı
  tekrar saymadan iki sensörün listelenen geçiş birleşimi ve zaman tanısı.
- `control_scan_geometry_crosscheck.json`: üç kontrolün boyut/zaman karşılaştırması.
- `area_saved_outputs_verification.json`: bağımsız geri okuma sonucu.

Yeni dosyalar tanı çıktısıdır. Alan eşiği, günlük negatif, olay kataloğu veya
nihai eğitim tablosu üretilmedi.

4 Ekim'de geometri tanısı 1.176 termal tespite genişletildi ve eğitim dönemi
katalog kayıtları sayıldı. Üç referansta yuvarlama tek başına boyut farkını
açıklamıyor; otomatik düzeltme seçilmedi. Güncel toplam 148 test başarılı.
Ayrıntılar: [geometri ve hacim incelemesi](GEOMETRY_DIAGNOSIS_2026-10-04.md).
