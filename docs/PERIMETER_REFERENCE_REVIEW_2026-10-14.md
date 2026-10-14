# Yangın sınırlarıyla coğrafi karşılaştırma — 14 Ekim 2026

## Amaç ve kapsam

[Kurumsal vaka bağlamından](REFERENCE_CONTEXT_REVIEW_2026-10-14.md) sonra
amaç, seçilmiş uydu kümelerini tarihli yanmış alan geometrileriyle karşılaştırmaktı.
İki açık veri kaynağının gerçek dosyaları denetlendi. Sonuç, otomatik
**coğrafi bağlam incelemesidir**; bağımsız saha doğrulaması veya nihai etiket
kabulü değildir. 2024 ve 2025 açılmadı; yeni VM/ücretli servis işi yapılmadı.

## Kaynak denetimi

[Kaynak sicili](research/perimeter_reference_sources_2026-10-14.json), kimlik,
lisans, boyut, checksum, yöntem ve sınırları saklar.

**FireSpread_MedEU:** Müller ve çalışma arkadaşlarının veri seti optik Planet
görüntülerinden, elle düzeltilmiş yangın yayılım sınırları sunar.
[Veri/CC-BY-4.0 kaydı](https://zenodo.org/records/18200075),
[yöntem makalesi](https://doi.org/10.1038/s41597-026-06965-2).
2.751.019 bayt ZIP, API boyutu ve MD5 ile kontrol edildi; SHA-256 ayrıca
kaydedildi. Yerel dosyada 103 olay/649 kayıt vardır: 320 pozitif yayılım
adımı, 103 yangın öncesi bağlam kaydı, 226 geometrisi eksik kayıt.

Yangın öncesi kayıtlar dosyada yaklaşık 3,14 m² küçük poligon geometrileri
taşır; `Prop_step=0` ve yanmış alan ölçüsü boş olduğundan yanmış alan
veya güvenilir negatif sayılmaz. Eksik geometrinin gerekçesi bulut, eksik
görüntü veya değişmeyen alan olabilir; boş geometri otomatik yangınsızlık
değildir. İki yanmış alan poligonu geçersizdir; kaynak onarılmadı.
Değişken açıklama PDF'sinin tek sayfası metin ve görüntü olarak incelendi;
çıktı alanında özgün hali korundu.

Gerçek yanmış geometrilerin en doğusu yaklaşık 23,733°D, pilot AOI'nin
en batısı 26,206°D'dir. Eğitim kapsamındaki geçerli geometrilerle gerçek
AOI kesişimi sıfırdır. **Bu kaynak dört il için referansa alınmadı.**
Başlığındaki Akdeniz ifadesinden Türkiye kapsamı varsayılmadı.

**EFFIS:** Resmî veri servisindeki WFS katmanı, alan şeması ve filtreli
`hits` sayısıyla kontrol edildi. [Servis ve veri erişimi](https://forest-fire.emergency.copernicus.eu/applications/data-and-services).
Temmuz–Ağustos 2021 başlangıç tarihi ve CRS84 kutusu
`[26.2, 36.0, 35.2, 39.4]` için 84 kayıt bildirildi. Tam güncel arşiv
indirilmedi; en fazla 100 kayıt/10 MB sınırıyla aynı filtre kullanıldı.
433.192 bayt GML'deki 84 kayıt, tarih ve kimlik bakımından doğrulandı.
Bir ilk geometri denemesi HTTP 502 verdi; küçük istekle şema doğrulandıktan
sonra varsayılan koordinat sistemiyle tam filtreli istek başarılı oldu.

Kutudaki 79 kayıt TR, beş kayıt EL ülke kodludur; bunların hepsi pilot
kapsamı değildir. 84 geometri geçerlidir. Pozitif/negatif etiket tanımı
değişmeden, gerçek AOI ile sınır dahil kesişen **42 dış kaynak poligonu**
bulundu. Poligonun AOI ile kesişmesi, tamamının dört il içinde olduğu
veya 42 bağımsız tutuşma olduğu anlamına gelmez.

EFFIS, MODIS/Sentinel-2/VIIRS kaynakları kullandığından FIRMS/VIIRS'le
tam bağımsız kabul edilmez. Son sınır içindeki bir nokta, yangının o noktada
ilk gün başladığını göstermez. [Resmî yöntem](https://forest-fire.emergency.copernicus.eu/about-effis/technical-background/rapid-damage-assessment),
[EU içerik lisansı ve atıf koşulu](https://forest-fire.emergency.copernicus.eu/about-effis/data-license).

## Koordinat, zaman ve eşleştirme yöntemi

MapServer'ın WFS 1.1/GML3 çıktısında EPSG:4326 koordinatları enlem/boylam
sırasındadır. Okuyucu bunları boylam/enlem olarak geometriye dönüştürür;
her kaydın zarfıyla ayrıca kontrol eder. Tek Polygon ve MultiSurface,
iç halkalar, kapalı iki boyutlu koordinatlar, benzersiz kimlik ve eğitim
dönemi zorunludur. XML dış şemaları/varlıkları izlenmez; kapsam dışı tarih
ve bilinmeyen CRS reddedilir. Ham kaynak geometrileri değiştirilmez.

Önceki 53 amaçlı vakanın yalnız sorgu dönemine düşen **21 küme-senaryo
varyantı** işlendi. Bütün üyeler ve aynı en erken zamanda bulunan tüm
ilk hücreler, korunan kaynak üyelikleriyle kontrol edildi. Nokta son
yanmış alanın içinde veya sınırındaysa coğrafi bağlantı yazıldı. Bir nokta
birden fazla poligona değebilir; birleşik sayımda tespit kimliği tek sayılır.

Kaynak başlangıç/bitiş saatlerinin UTC olduğu varsayılmadı; ham metin
korundu. Yalnız takvim aralığı örtüşmesi bir ipucu olarak kaydedildi.
Bu ipucu tam zamansal olay kimliği kabulü değildir. Hiçbir zaman son
yanmış alan geometrisi model girdisine veya günlük hedefe çevrilmedi.

## Gerçek bulgular

21 varyant için **24 küme–sınır bağlantısı** oluştu; bağlantılarda beş
farklı EFFIS kimliği kullanılıyor. Senaryo tekrarları bağımsız yangın
sayısı değildir. Üç varyantta üyeler iki farklı son sınıra denk gelir;
ancak ek sınır, kümenin tarih aralığıyla örtüşmez. Takvim örtüşmesi ipucu
uygulandığında birden fazla sınırla ilişkili varyant sayısı sıfır olur.
Üç varyant, yanlış birleşmiş üç yangın olarak raporlanmadı.

Somut iki inceleme örneği:

- `d2000m_t72h_C003757` varyantında 5.304 tespit satırının 4.560'ı EFFIS
  51931 son sınırı içinde/sınırındadır. Tek ilk nokta bu sınırın dışındadır;
  UTM 36N/EPSG:32636 ile en kısa uzaklık yaklaşık **174,23 m** bulunmuştur.
  Bu bir nokta–son sınır mesafesidir; yanlış tespit oranı, tutuşma hatası
  veya belirlenmiş konum toleransı değildir. Konum hassasiyeti, piksel
  desteği ve referans sınırı belirsizliği çözülmeden ilk nokta reddedilmedi.
- `d1000m_t24h_C004736` varyantının 1.348 satırından 1.196'sı EFFIS 52429'a,
  biri 54640'a coğrafi olarak bağlanır. İkinci kaydın tarihi 20 Ağustos'tur;
  kümenin son tespiti 12 Ağustos olduğu için takvim örtüşmesi yoktur.
  Sadece konumla yeni olay kimliği atanmadı.

Yerel çizim:
`outputs/reports/dataset/perimeter_review_v1/20261014T162023Z_61ec4cba/spatial_context.png`.

Şekil, ilk örneğin tüm üye tespitlerini ve son sınırı gösterir; ilk günün
yayılımı veya bağımsız tespit doğruluğu olarak yorumlanmaz. Coğrafi sınır:
European Union / Copernicus EMS / JRC, EFFIS; kaynak 14 Ekim'de alınmış,
çizim proje tarafından üretilmiştir.

## Doğrulama ve sonraki adım

53 ilgili test ve lint/format geçti. Testler enlem/boylam dönüşümü, zarf,
Polygon/MultiSurface, zararlı XML, kapsam dışı tarih, yangın öncesi/eksik
geometri ayrımı, kaynak bozulması, ilk hücre bağları, sınırdaki ortak
nokta ve takvim uyuşmazlığında etiket yaratılmamasını kapsar. CSV'ler boş
değer desenleri ve string kimlikleri korunarak dosyadan geri okundu.

Final dizini `outputs/reports/dataset/perimeter_review_v1/20261014T162023Z_61ec4cba/`:

- `readback.json` SHA-256
  `32f85afaf1b2a223bae1c7e4003a2f953fa8563d03c97925ca5b0d12b9126810`.
- `completion_readback.json` SHA-256
  `4fe1db02eb4df632cc734a578bf6016a1c423f5268b7bdddd746c590ee7a2d19`.

Beş çıktı ve 35 giriş kimliği kapanışta tekrar hash ile kontrol edildi;
22 donmuş bulut girdisi ve önceki altı inceleme çıktısı aynı kaldı.
453 insan inceleme formu hâlâ not_reviewed; 0/1 hedef, kesin olay kimliği,
bağımsız başarı veya hata oranı üretilmedi. Bu son kontrol ham uydu
ürünlerini yeniden hesaplamadı.

Sıradaki ihtiyaç, bu somut uyuşmazlıkları olay tanımı/ilk hücre kuralları
için değerlendirmek; referansın sensör bağımlılığını ve belirsizliğini
taşıyan bir kabul protokolü oluşturmaktır. Bu dar 2021 incelemesi altı
yıllık referans veya güvenilir negatiflerin tamamlandığı anlamına gelmez.
`daily_observation_status=unknown`, iki etiket kapısı kapalı ve
`model_ready=false` korunur.
