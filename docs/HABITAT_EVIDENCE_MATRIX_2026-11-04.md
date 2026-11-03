# Ortak habitat kanıt tablosu — 4 Kasım 2026

## Tamamlanan hazırlık

25 nokta / 21 hücre-gün biriminde önceki kanıtlar kaynak kimlikleri
korunarak aynı tabloya bağlandı. Bu, kabul edilmiş etiketli veri seti
birleştirmesi değildir; sınırlı inceleme kaydıdır. Altı donmuş rapor,
iki ölçekli tasarım kararı ve yeni üretici kodunun toplam sekiz hash'i
işlem öncesinde ve sonrasında kontrol edildi.

Her nokta için ayrı alanlarda şu bilgiler var:

- 2017 haritasında **risk hücresinin** orman/çalılık oranı, AOI ve
  haritalanmış alan paydası; tam 25 km² varsayılmadı.
- 2018 CORINE haritasında **yaklaşık tespit alanının** sınıf payları,
  merkez sınıfı ve en büyük alan sınıfı.
- Olay öncesi görüntülerin çekim zamanı, kullanılan ürünün üretim zamanı
  ve kalite kayıtları; bunlar geçmişte erişilebilirlik kabulü değildir.
- Araştırmacı ön notları, asistan görsel yorumundan ayrı; C'nin önceki
  teyidi dahil tarihsel notlar kaybolmadan korundu.
- Açık kanıt gereksinimleri ve boş hedef/kabul alanları.

İki haritanın farklı sınıf tanımları, yılları, çözünürlükleri ve
paydaları vardır. Aralarındaki sayısal fark gerçek örtü değişimi veya
bir haritanın hata oranı olarak hesaplanmadı.

## Güncel kapsam

| Alan | Durum / payda |
|---|---:|
| Kimliği eşleşen inceleme noktası | 25/25 |
| Hücre-gün birimi | 21 |
| Birden fazla ilk noktası olan birim | 3/21; bütün üyeler ayrı korunuyor |
| İnsan görsel ön notu bulunan nokta | 10/25 |
| Birden fazla olay öncesi görüntü tarihi | 6/25 |
| CORINE referans dönemi T'nin sonrasına uzanan nokta | 10/25 |
| CORINE referansı T'den önce biten, fakat eski olan nokta | 15/25 |
| Olay tarihindeki doğal/yönetilen örtüsü kabul edilmiş nokta | 0/25 |
| Nihai habitat kabulü | 0/25 |

İlk 10 noktanın tahminleri 2018 içindedir. CORINE referansı 2017–2018
dönemidir; yerel sınıfın tam gözlem zamanı bilinmiyor. Dolayısıyla
referans dönemi tahminden sonrasını içerir; bu, ilgili pikselin mutlaka
sonraki gözlemden üretildiğini kanıtlamaz. Diğer 15 nokta 2021/2023'e
aittir; eski harita doğrudan o tarihin gerçeği sayılmaz. Aynı yılın
haritası bile otomatik olay öncesi kanıt değildir.

Görüntü kanıtında 37 kayıt / 31 farklı ürün bilgisi önceki hash bağlı
rapordan aktarıldı. 20 nokta–görüntü kaydındaki ürün sürümü T sonrasında
üretilmiştir. Bu ayrım, geriye dönük inceleme ile tarihsel model girdisi
uygunluğunu ayrı tutar. Rasterlar bu adımda yeniden hesaplanmadı.

## Somut karar hazırlığı

| Örnek | Birlikte okunan kanıt | Önerilen sonraki inceleme; kabul değil |
|---|---|---|
| C | İnsan ağaçlık notu; CORINE alanda %77,98 orman; 2021'de tek görüntü | Orman bağlamı destekleniyor; 2018–2021 tarih farkı ve alan sınırı görselle değerlendirilmeli |
| D | İnsan karışık/ağaçlık notu; %58,55 geçişli ağaçlık, kalan mera/meyvelik; 2021 tek görüntü | Tek doğal/tarım sınıfına zorlamak yerine yerel karışım korunmalı |
| E | İnsan tarla benzeri not; %100 tarım/doğal mozaik; 2023 tek görüntü | Mozaik sınıfının iç doğal oranı bilinmiyor; kesin tarım veya doğal kabulü açık |
| F | İnsan tarla benzeri not; %100 meyvelik; 2018 tek görüntü | Yönetilen örtü için destek var; haritanın olay öncesi kullanım durumu henüz doğrulanmadı |
| R03 | İnsan belirsiz ağaçlık/açık alan notu; üç görüntü; tarım–sklerofil karışımı | Sınır ve parlak geometrik yüzeyler mevcut tarihli görüntülerde birlikte incelenmeli |
| R11 | İnsan kuru görünüm notu; seyrek ve odunsu sınıflar; 2018 tek görüntü | Kuru görünümden örtü yokluğu veya ölçülmüş kuraklık çıkarılmamalı |
| R15/R16 | İnsan ayıramama/benzerlik; bataklık–tarım bağlamı; ortak birim | İki üyeyi koru; yeni sınıf seçmeye zorlamadan tarih ve kullanım belirsizliğini kaydet |

Tablo hiçbir eski insan yorumunu değiştirmez ve insan onayı eklemez.
Kaynak tablodaki geçmiş altı insan noktası yeni dört notla uzlaştırıldı;
eski kuyrukta kullanılan sayısal `labels_created=0` alanı, diğer
raporlardaki `false` alanından açıkça ayrılarak kontrol edildi.

CORINE etiketleri yalnız inceleme başlıkları için kullanıldı. 25 noktada
6 odunsu kod, 14 tarımsal kod, 2 tarım/doğal mozaik, 9 yapay yüzey,
6 su/sulak ve 7 çayır/açık/diğer kod kesişimi var. Bu sayılar örtüşür,
toplanmaz; küçük sınır parçaları dahildir. Örneğin E tarımsal ve mozaik
başlıklarında birlikte bulunur. Bu başlıklar otomatik kapsam grubu değildir.

## Yöntem yönü ve açık iş

Önerilen yön, kullanıcının iki ayrı kontrol kararını sürdürmektir:
hücrenin risk nüfusuna uygunluğu olay varlığından bağımsız değerlendirilmeli;
aday yerel örtüsü ise bütün ilk noktaları ve karışımlarını korumalıdır.
Merkez sınıfı, en büyük sınıf veya herhangi bir odunsu kesişim tek başına
kabul kuralına dönüştürülmemelidir. Çözülemeyen durumlar ayrı incelemede
kalır; bilinmeyen durum negatif etiket olmaz.

Bu adım kanıtların **bir araya getirilmesini** tamamladı. Habitat
aşamasının kapanması için tarihe aktarım, konum/sınır belirsizliği ve
doğal/yönetilen örtü için kabul/belirsizlik protokolü hâlâ gereklidir.
Sıradaki somut hazırlık C/D/R03 sınırları ve E/F kullanım bağlamını
mevcut olay öncesi görüntülerle aynı mekânsal çerçevede incelemek;
sonrasında ölçülen belirsizlikleri içeren yöntem seçeneklerini sunmaktır.
Yeni veri indirmeden yapılabilecek bu karşılaştırma nihai kabul sayılmaz.

## Kontrol kaydı

Üretici `scripts/quality/consolidate_habitat_review.py`.
Çıktı `outputs/reports/dataset/habitat_evidence_matrix_v1/20261103T215030Z_1106f3eb/readback.json`.
SHA-256 `da877cc44c0626995dde7577892b2dbfbbc9f3a2efea5f226aa268569298366e`.
UTC dizin tarihi 3 Kasım, Türkiye çalışma tarihi 4 Kasım'dır.
Sekiz doğrudan kaynak/kod kimliği, 25 tekil nokta, 21 birim üyeliği,
10 insan notu, tarihler ve kapalı etiket/dışlama alanları doğrulandı;
JSON geri okuması ve lint/format geçti. Bu, önceki raporların bütün
ham kaynaklarının yeni baştan denetlendiği iddiası değildir.
Yeni ağ, GCP veya 2024/2025 veri erişimi yapılmadı; nihai birleşme yoktur.
