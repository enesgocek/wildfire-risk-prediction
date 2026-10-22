# Eşleşen adaylarda örtü ve açık olay kanıtı

23 Ekim 2026. İnceleme 22 Ekim'de başladı; kaynak taraması ve ilk yerel
inceleme sonrasında nihai hesap 23 Ekim Türkiye tarihinde tamamlandı.
Önceki tarihli sonuçlar değiştirilmedi. Kapsam, ayrıntılı gözlem pilotuyla
eşleşen aynı **21 amaçlı aday hücre-gün**dür; bütün eğitim verisinin hata
oranı veya temsili olay örneklemi değildir.

## Gerçekleşen kontrol

21 aday, korunmuş 2017 örtü tablosuna hücre anahtarıyla bağlandı. Hücre
ortalaması tek başına tespitin örtüsünü göstermediğinden, dokuz senaryodaki
ilk hücre ve kayıtlı ilk zamana ait **bütün tespit noktaları** ayrıca bulundu.
180 aday-senaryo-bileşen kaydının 207 ilk nokta tanığı, **25 farklı kaynak
tespitine** karşılık geliyor. Bu sayılar bağımsız yangın sayısı değildir.
Eşzamanlı noktalar tek bir keyfî merkezle değiştirilmedi.

Özgün tespit kimlikleri, hücreleri ve zamanları korunmuş atamalar ve kaynak
CSV ile eşleşti. Kaynağın 2024 satırları yalnız tarih filtresinden geçti;
koordinat/alan incelemesine alınmadı. 2025 kapalı kaldı.

Yerel 2017 rasteri tek bantlı, EPSG:3857 ve 100×100 projeksiyon metre
piksel aralığındadır. EPSG:4326 boylam/enlem noktaları açık xy sırasıyla
raster koordinatına dönüştürüldü. Merkezdeki sınıf yeniden örneklendi;
aynı piksel doğrudan satır/sütun okumasıyla ayrıca kontrol edildi.
Bu örnekleme VIIRS piksel ayak izinin tamamını veya gerçek tutuşma yerini
temsil etmez; kaynak raster değiştirilmedi.

## Ölçülen örtü dağılımı

| 2017 haritasında tespit merkezi sınıfı | Farklı kaynak noktası |
|---|---:|
| Tarım | 11 |
| Yerleşim/yapılaşmış alan | 6 |
| Orman | 3 |
| Çalılık | 1 |
| Otsu örtü | 3 |
| Otsu sulak alan | 1 |
| Toplam | 25 |

Hücre-gün bazında bütün ilk noktalar birlikte tutulduğunda: dokuz örnekte
yalnız tarım, beşinde yalnız yerleşim, üçünde yalnız orman, birinde yalnız
çalılık, birinde yalnız otsu örtü var. Bir örnek tarım+otsu, bir örnek
tarım+otsu sulak alan karışımıdır. Toplam **21** korunur. Hiçbiri silinmedi,
0 veya 1 yapılmadı. Nokta sayımı ile hücre-gün sayımı birbirine eklenmez.

Sınıfların anlamı [resmî veri kataloğundan](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_Landcover_100m_Proba-V-C3_Global)
kontrol edildi. Type=0 varsayılan bitki yangını sınıfıdır; orman yangınına
özgü kanıt değildir. Tarım veya yerleşim sınıfına düşmek de tespitin hatalı,
endüstriyel kaynak veya kesin anız yangını olduğunu kanıtlamaz. Harita 2017'ye
aittir; sınıflandırma hatası, sonraki örtü değişimi, piksel karışımı ve tespit
konum belirsizliği vardır. Ayrıca kalıcı odunsu tarım örtüsü haritada orman/
çalılık sınıfına girebilir. Bu nedenle harita sınıfı tek başına yangın türü
etiketine veya kalıcı dışlama kuralına çevrilmedi.

Somut örnekler:

- **C676_R876 / 2018-08-15:** 5 km hücrenin tarım payı yaklaşık %99,98;
  ilk tespit merkezi de 2017 rasterinde tarım. Dokuz ayarın aynı olay adayı
  sonucunu vermesi bunu orman yangınına dönüştürmez.
- **C509_R907 / 2018-05-15:** hücrede orman ve çalılık da var, ilk tespit
  merkezi ise haritada yerleşim. Hücrenin herhangi bir yerinde orman bulunması
  o tespitin orman yangını olduğunu göstermiyor.
- **C518_R903 / 2018-11-15:** aynı ilk zamanda üç farklı nokta var;
  ikisi otsu, biri tarım sınıfında. Tek bir ilk nokta seçmek bu karışımı gizlerdi.

## Mevcut ve yeni açık olay kanıtının sınırı

Korunan OGM yayınından aktarılmış 12 bağlam kaydının bildirilen başlangıç
tarihleri bu 21 adayın günleriyle eşleşmiyor. Bu karşılaştırma devam eden
olayları veya başka kayıtların bulunmasını dışlamaz. Bu kayıtlarda önceki
konum/saat/bağımsızlık eksikleri korunuyor; yeni kesin olay eşleşmesi yok.

Üç il/tarih birleşimi için iki tarih yazımıyla altı sınırlı web sorgusu
yapıldı. İlk aramalarda medya ve ilgisiz belge adayları, kurum alan adı
filtrelerinde de bu hücre/zamana kesin olay eşlemesi sağlamayan önizlemeler
bulundu. Bunlardan olay etiketi kabul edilmedi. Bu, 21 örneğin tamamında
sistematik arama veya olay bulunmadığının kanıtı değildir. Arama ve teknik
kaynak kaydı [ayrı sicildedir](research/candidate_context_sources_2026-10-23.json).
Kurumlara ileti gönderilmedi veya hesaplara girilmedi.

## Kontroller ve makbuz

Yedi yeni vaka dahil **35 ilgili test** geçti; bütün depo testleri değildir.
EPSG:4326→3857 xy dönüşümü, doğrudan piksel eşliği, nodata/dış alanın
bilinmeyen kalması, boş/tekrarlı/geçersiz nokta ve bilinmeyen sınıf reddi
sınandı. Üç yeni Python dosyasında lint/format geçti. Kaynaklar ve yöntem
dosyaları dahil 24 doğrudan girdi başta/sonda aynı kaldı. Üç çıktı CSV'nin
bütün içeriği diskten geri okunarak eşleşti; manifestle dört çıktı hash'i korundu.

Sonuç `outputs/reports/dataset/linked_candidate_context_v1/20261022T210339Z_23e2e5a4/`.
Dizin kimliği UTC, rapor tarihi Türkiye takvimidir. Readback SHA-256:
`58363f7e1640af945195ecf9d13144a5ec4951fb259a30816274c12956710de8`.
Başlıca çıktılar `case_cover_reference_context.csv`, `first_point_cover.csv`
ve `scenario_first_point_witnesses.csv`.

## Karar ve sonraki sınırlı iş

Araştırmacıya ana örtü kapsamı için **orman+çalılık (öneri)**, yalnız orman
ve orman+çalılık+doğal otsu alan seçenekleri sunuldu. Bu kaydın hazırlanma
anında yanıt bekleniyor; öneri kabul edilmiş gibi kodlanmadı. Soru ana
araştırmanın hangi örtü türlerini ele alacağıdır; harita tek başına 0/1
etiket, kalıcı dışlama veya gerçek yangın türü kararı sağlamayacak.

Seçilen kapsama göre tespit konum belirsizliği ve komşu örtü karışımı ayrıca
incelenmeli; ardından kapsam kararı bütün adayların dağılımıyla değerlendirilmeli.
Mevcut amaçlı pilot, bağımsız olay doğrulama örneklemi yerine geçmez. Referans
bulunabilen olay günlerine dayanan ayrı inceleme çekirdeği gerekebilir;
bu işlemle böyle bir çekirdek tamamlandı denilmiyor.

Gözlem `unknown`, pozitif/negatif kabulü false ve hedefler boş kaldı.
Yeni ham veri kuyruğu, model, nihai birleştirme veya dış ileti yapılmadı.
