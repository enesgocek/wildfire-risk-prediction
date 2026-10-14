# Gözlem desteğinin mekânsal anlamı — 15 Ekim 2026

Durum: sekiz saklanmış yaklaşık geçiş geometrisinde yerel tanısal inceleme.
Geri okuma, görsel inceleme ve kaynak kapanışı geçti. Yeni etiket politikası
kabulü değildir.

## Soru ve kaynak

14 Ekim'deki 181 arka plan adayında kara/bulut birleşimi çakışmaları
sayılmıştı. Bu çakışmaların hatalı veri veya negatif etiketi reddetme
gerekçesi olduğu ileri sürülmemişti. Yeni çalışma bu ayrımı saklanmış
geometrilerde ölçer; önceki 181 örneğin tamamına yeni geometri üretmez.

İnceleme günü **14 Ocak 2019**, kapsam aynı dört ilin AOI ile kesilmiş
**2.899 hücresi** ve önceki incelemeden saklanan **beş S-NPP/üç NOAA-20
granülüdür**. Gün amaçlı seçilmiştir; rastgele doğruluk örneklemi değildir.
Granül, altı dakikalık dosya parçasıdır; sayısı bağımsız uydu geçişi
sayısı olarak yorumlanmaz.

Kaynak, 3 Ekim'deki
`outputs/reports/observation_coverage/l2_area_union_2019-01-14_SNPP_N20_8samples.json`
raporudur; SHA-256
`d4598b888465069898543ec844b83b17fd24f65e36f9a5ff46eedcd5f6dea1cc`.
Yeni hesap, bu rapordaki GPKG/CSV/tarama ve önceki denetim kimliklerini
doğrular; özgün ham uydu ürünlerini yeniden hesaplamaz. Yaklaşık alan
yönteminin fiziksel doğruluğu veya yangın gerçekliği yeniden doğrulanmış
sayılmaz. Önceki kabul edilmiş dosyalar değiştirilmez.

## Alanların doğru yorumu

Her hücre için aynı yeniden kurulmuş alan içinde:

- **D:** saklanmış geçişlerde yeniden kurulmuş alanın birleşimi.
- **L:** nominal QA ve residual dışlama koşulundaki yangın olmayan kara
  alanlarının birleşimi; listelenen gözlemlerde en az bir kez bu sınıf görülür.
- **C:** listelenen geçişlerde bulut sınıfı görülen alanların birleşimi.

`L ∩ C` aynı yerde farklı zamanlarda iki sınıfın görülmesini içerebilir.
Bu alanı L'den çıkarıp kalanını tek geçerli kara desteği saymak, önceki
açık gözlemi de silebilir. Çakışma otomatik veri hatası veya negatif aday
eleme kuralı değildir. Öte yandan L'nin büyük olması aynı alanın gün
boyunca veya her geçişte açık olduğunu kanıtlamaz.

Aynı D'nin alt kümeleri için yalnız alanlarla bilinen sınır:

`max(0, |L| + |C| − |D|) ≤ |L ∩ C| ≤ min(|L|, |C|)`.

Geometrik kesişim bu aralıkla karşılaştırılır. Aynı granül içindeki
kara/bulut kesişimi de ayrıca ölçülür: bir granül birden fazla tarama
içerdiğinden bu tanı tek başına aynı piksel/zamanda çelişki kanıtı değildir;
yaklaşık geometri ve tarama örtüşmesi de incelenmelidir.

İkinci ayrım günlük kara birleşimi, **tek granüldeki en büyük kara alanı**,
**en az iki granülde ortak kara alanı** ve **iki sensörün kara birleşimlerinin
kesişimi** arasındadır. Tekrar alanı üst üste toplanmaz. Bütün payların
paydası hücrenin AOI alanıdır; kabul edilmiş habitat/orman paydası değildir.
Tekrar alanı bağımsız geçiş sayısı veya sürekli gözlem süresi değildir.

Bir davranış testi aynı günlük birleşimin hem birbirini tamamlayan iki
ayrı alanla hem de büyük ölçüde tekrar eden gözlemlerle oluşabildiğini
gösterir. Günlük birleşimden bu iki durum tek başına geri çıkarılamaz.

## Bu eğitim gününde ölçülen sonuç

AOI toplamı **60.727,11 km²**; günlük nominal kara birleşimi **36.011,82
km²**, bulut birleşimi **60.726,55 km²**, bunların kesişimi **36.011,26
km²**'dir. Bu yüzden günlük bulut birleşimini karadan çıkarmak, saklanan
kara desteğinin neredeyse tamamını silebilir. Bu örnekte çakışma varlığı
kara desteğinin hiç oluşmadığı anlamına gelmez.

En az iki granülde ortak nominal kara alanı **11.198,71 km²**, iki
sensörün kara birleşimlerinin kesişimi **8.575,08 km²**'dir. Bunlar
tekrar alanıdır; toplam piksel sayısı, bağımsız geçiş sayısı veya yangın
tespit doğruluğu değildir. Aynı granül içindeki kara/bulut kesişimlerinin
toplamı **1.719,80 km²**'dir; bu toplam farklı granüllerde tekrar eden
aynı alanı içerebildiği için benzersiz alan diye sunulmaz.

Aynı granül içindeki çakışmaların **benzersiz birleşimi 1.711,69 km²**;
günlük çakışmanın bunun dışında kalan **34.299,57 km²**'si yalnız farklı
granüllerin kara/bulut destekleri birleştirildiğinde oluşur. Bu iki alanın
günlük kesişimi kayıpsız parçaladığı kontrol edildi. İlk sayı taramalar
arasındaki örtüşme/yaklaşık geometriyi ayrıca içerir; ikinci sayı bağımsız
uydu geçişlerinin sayısını veya tespit doğruluğunu vermez.

| Kabul edilmemiş alan payı kesimi | Günlük kara birleşimi kesimi geçen hücre | En az bir tek granülde kesimi geçen hücre | Birleşim geçerken hiçbir tek granülün geçmediği hücre |
|---|---:|---:|---:|
| 0,80 | 1.360 | 1.281 | 79 |
| 0,90 | 1.151 | 1.037 | 114 |
| 0,95 | 977 | 849 | 128 |

Bu üç kesim bir negatif politikası seçmez. Sayılar bütün 2.899 AOI
hücresindedir; su kapsamı filtresi uygulanmış nihai eğitim popülasyonu
değildir. Tek gün/amaçlı seçim nedeniyle bütün altı yıla, 181 arka plan
adayına veya etiket hata oranına genellenmez.
**Tek granülün yüksek alan payını zorunlu tutmak da doğrulanmış bir kabul
kuralı değildir.** Farklı geçişler birbirini tamamlayabilir; 114 hücre
otomatik hatalı veya elenecek hücre değildir. Hangi zamansal/mekânsal
desteğin yeterli olduğu hedefe bağlı ayrıca sınanmalıdır.

En büyük birleşim kazancı olan üç hücre açıklayıcı tanık olarak seçildi.
Örneğin `E6933_5K_V1_C630_R868` hücresinde günlük nominal kara payı
**%94,45**, tek granüldeki en yüksek pay **%59,91**'dir. Her ikisi aynı
AOI paydasındadır. Bu fark bir gün boyunca toplam destekle bir dosyadaki
destek arasındaki ayrımı gösterir; hücrenin negatif/pozitif olduğunu söylemez.

## Negatif kabulü için yöntem seçenekleri

| Seçenek | Sağladığı bilgi | Ana sınır ve öneri |
|---|---|---|
| Günlük alan/merkez eşiğini doğrudan etiket yapmak | Düşük hesap yüküyle kolay seçim | Zaman ve yer desteğini birleştirir; ana hedef için tek başına önerilmez |
| Zamanı ve kaliteyi koruyan geçiş desteğiyle gerekçeli negatif aday kabulü | Nerede/ne zaman hangi destekle aday seçildiği izlenebilir; eşik duyarlılığı ölçülebilir | Önerilen araştırma yönü; eşik ve hata değerlendirmesi henüz kabul edilmiş değil |
| Pozitif–etiketsiz öğrenme ile belirsiz kayıtları korumak | Bilinmeyenleri sıfır yapmadan ayrı bir deney kurulabilir | Etiketlenme mekanizması ve olasılık kalibrasyonu ayrıca gerekçelendirilir; kabul edilmiş ana model yöntemi değil |

**Öneri:** ikinci yönde, sınırlı kaynak pilotunda geçiş/zaman/kalite
desteğini kurup aday kapsamı ile kaçırılmış olay riskini birlikte ölçmek.
Sadece daha katı bir yüzde seçmek veya bütün gün kusursuz gözlem talep
etmek çözüm değildir. Gözlenebilirliği güçlü bir negatif, yine tanımlı
ölçüm koşullarında kabul edilen araştırma etiketidir; fiziksel olarak
hiç yangın olmadığına dair hatasız gerçeklik iddiası taşımaz.

Bu önerinin uygulama/kabul kapıları:

1. **Hedef ve zaman:** ana 24 saatlik yeni olay hedefi korunur. İlk uydu
   tespiti ile gerçek tutuşma ayrımı, olay/ilk hücre kararıyla birlikte
   yazılır. Komşu granüller gerçek tarama zamanıyla pencereye alınır.
2. **Mekân ve geçiş:** nominal QA kara desteği ayrı zamanlarda tutulur;
   yörünge/zaman kanıtı olmadan komşu dosyalar bağımsız geçiş sayılmaz.
   AOI ile habitat paydası ayrılır; su/kıyı/karışık hücreler açık kalır.
3. **Önceden kayıtlı pilot:** alan payı ve zaman boşluğu seçenekleri
   eğitim döneminde karşılaştırılır. Kapsam kaybı il/mevsim/habitatta
   raporlanır; en çok örnek bırakan seçenek otomatik seçilmez.
4. **Hata kanıtı:** pozitif olay çevresi ve zor arka plan örnekleri için
   kaynak/zamanı bilinen referans incelemesi yapılır. Aynı VIIRS'ten
   türetilmiş başka katalog bağımsız doğrulama diye sunulmaz. Bağımsız
   referans yoksa bu açıkça yazılır; bilinmeyene sıfır atanmaz.
5. **Kabul:** ancak tanımı, kapsamı ve hata sınaması gerekçelendirilmiş
   sürüm değerlendirmeye sunulur. Kullanıcı kararı ve en son parça
   kontrollerinden önce mevcut etiket kapıları değişmez.

Bu kapılar milyonlarca satırın elle etiketlenmesini gerektirmez. Amaçlı
zor vaka incelemesi ile sonradan tasarlanacak olasılıklı doğruluk örneklemi
ayrıdır; mevcut 400 amaçlı pilot veya bu tek gün için hata oranı genellenmez.

## Resmî kaynakla karşılaştırma

NASA'nın Collection-2 375 m kılavuzu, tam fire mask ile QA katmanının
gözlem koşullarını kısmen yeniden kurmak için kullanılabileceğini belirtir.
Bu açıklama bu projenin yaklaşık alan yöntemini veya bir günlük negatif
eşiğini doğrulamaz. Granülün altı dakikalık parça olması da bağımsız
geçiş sayımı için dikkate alınır.
[NASA VIIRS C2 kılavuzu v1.2, bölüm 3.1, 15 Ekim erişimi](https://ladsweb.modaps.eosdis.nasa.gov/archive/Document%20Archive/Science%20Data%20Product%20Documentation/VIIRS_C2_AF-375m_User_Guide_1.2.pdf).

Geçişler arasında başlayıp biten yangınlar ile bulut/duman/ağaç örtüsü
nedeniyle tespit kaçabileceği NASA FIRMS notlarında açıklanır. Bu nedenle
gözlem desteği ile fiziksel yokluk ayrı tutulur; resmî notlardan belirli
bir yüzde/saat eşiği türetilmez.
[NASA FIRMS notları, 15 Ekim erişimi](https://firms.modaps.eosdis.nasa.gov/alerts/notes.php).

## Çalıştırma, inceleme ve kapanış

Komut: `.venv/Scripts/python.exe scripts/quality/review_spatial_observation_support.py`.
Betik ağ bağlantısını engeller. Eğitim dışı CSV veya yeni bulut işi yoktur.
Tam özellik takvimi bu işte yeniden denetlenmiş sayılmaz; 14 Ekim'in
ayrı tam takvim denetimi geçerlidir. Bu çalışma ham uydu ürünlerini yeniden
işlemez ve yeni piksel-zaman geometrisi üretmez.

Son çıktı dizini:
`outputs/reports/dataset/spatial_support_v1/20261014T222953Z_5b507709/`.
UTC dizin zamanı 14 Ekim; Türkiye'de rapor günü 15 Ekim'dir.

- `grid_support.csv`: 2.899 hücrede alanlar, kesişim sınırları, tekrar,
  tek granül desteği ve kapalı etiket bayrakları.
- `swath_support.csv`: sekiz granül × 2.899 hücre, **23.192 satır**;
  granül içi kara/bulut kesişimleri ayrıca kayıtlıdır.
- `swath_times.csv`: sekiz dosyanın gerçek tarama zarfı ve alan toplamı;
  hücre/piksel zaman eşleştirmesi değildir.
- `illustrative_screens.csv`: kabul edilmemiş üç alan kesimi.
- `geometry_witnesses.csv` ve `geometry_witnesses.png`: amaçlı seçilen
  üç açıklayıcı hücre; grafik görsel olarak kontrol edildi.

Üç grubun geometri birleşimi önceki kaydedilmiş birleşimle karşılaştırıldı.
CRS, aynı AOI/hücre anahtarları, alan alt kümeleri, CSV/geometri alan
eşitliği, taramaların `(T,T+24h]` içinde olması, alan sınırları ve
granül içi/dışı kesişim ayrıştırması denetlendi. **72 giriş dosyası ve
altı çıktı** kapanışta aynı; **22 donmuş bulut girdisi** korundu.
16 yeni davranış testi dahil **82 ilgili test**, üç Python dosyasında
lint/format geçti. Bu sayı bütün proje testlerinin çalıştırıldığı anlamına
gelmez. Testler yanlış alan/bozuk geometri/anahtar dizisi, boş destek,
tekrar alanının bir kez sayılması ve aynı günlük birleşimin farklı geçiş
destekleriyle oluşmasını kapsar. Mevcut zaman ve nihai onay kapıları da
ilgili test grubunda kontrol edildi.

`readback.json` SHA-256:
`4d16e1dac4380e7b8da121f549d2dd5493631b831a99d1b5a75b5478c45cdcb4`.
`completion_readback.json` SHA-256:
`73a430c87d74f70bd47b544378cbb4778dd6b9310d157f3d30a12b3d6628681d`.

`daily_observation_status=unknown`, `negative_label_permitted=false`,
boş hedefler ve nihai birleştirme kapısı korunur. Teknik geri okuma,
bağımsız yangın doğrulaması veya araştırmacı kabulü değildir. Sonraki
somut yöntem işi, sınırlı eğitim kaynaklarında gözlem alanını zaman/kalite
kanıtıyla birlikte kurmak ve protokol seçeneklerinin kapsam/hata
incelemesini hazırlamaktır.
