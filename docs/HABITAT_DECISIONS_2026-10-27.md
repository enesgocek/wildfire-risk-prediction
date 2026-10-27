# Orman/çalılık kapsamı: karar hazırlığı

27 Ekim 2026. Mevcut 23 Ekim kanıtları ve ön notları yeniden bağlandı;
yeni uydu verisi veya yeni insan değerlendirmesi üretilmedi. Bu çalışma
altı ana veri hazırlık paketinin ilkine, habitat kapsamına aittir.
Kapsam kabulü veya nihai filtre değildir.

## Tamamlanan iş

25 noktanın eski harita bağlamı, insan notlarının geçmişi, ayrı asistan
yorumları ve 21 hücre-gün inceleme birimi bağlantısı ortak karar kaydına
alındı. C'nin eski notu ve yeniden teyidi birlikte korundu; sessiz bir
üzerine yazma yapılmadı. Yedi tarihsel insan notu kaydı altı farklı noktaya
aittir. Diğer 19 noktada yalnız asistan ön yorumu vardır. Bütün 25 noktada
kapsam kararı belirsiz, hedef boş ve gözlem durumu unknown kaldı.

Üç inceleme biriminde birden fazla nokta vardır:

| Hücre / tahmin günü | Görsel kodları | Karar hazırlığına etkisi |
| --- | --- | --- |
| C518_R903 / 2018-11-15 | R08, R09, R10 | Üç seyrek örtü yorumu aynı hücre-gün bağlamına ait |
| C519_R916 / 2021-11-15 | R01, R13 | İki sensörün yapı/tesis benzeri bağlamları aynı hücre-günde |
| C566_R867 / 2021-11-15 | R15, R16 | Karışık örtü yorumları aynı hücre-günde; R15 konum belirsizliği korunuyor |

Tam hücre kimlikleri `E6933_5K_V1_` önekiyle kayıtlıdır. Aynı hücre-gün,
tek fiziksel yangın olduğunun kanıtı değildir. 207 senaryo ilişkisi
kaynak dosyada korunur; karar özetindeki nokta kümesi onların yerine
geçmez. 21 birimin altısında en az bir insan ön notu vardır; bu sayı
kabul edilmiş veya bağımsız doğrulanmış olay sayısı değildir.

## Hangi kanıt hangi kararı sağlayabilir?

| Konu | Mevcut kanıt | Açık karar / eksik kanıt |
| --- | --- | --- |
| C'nin orman/çalılık görünümü | Araştırmacı ön notu ve tekrar teyidi | Zaman ve konumla uyumlu doğal örtü gerekçesi; görünüm yangın olayı kanıtı değildir |
| D ve R11 gibi karışık alanlar | Ağaçlık ile açık/parsel alanlarının birlikte görünümü | Yaklaşık tespit alanı içindeki örtü ile çevresinin ayrımı; kullanılacak kapsam kuralı |
| E/F ve R03'te doğal/yönetilen örtü | Parsel veya sera benzeri yapılar ve yeşil alanlar | Uygun tarihli, yeterli ayrıntılı görüntü veya belgeli arazi kullanım bilgisi; bunların elde edildiği varsayılmıyor |
| R15/R16 koridoru | Aynı hücre-gündeki iki karışık görünüm | Doğal/yönetilen örtü ayrımı; R15 için ayrıca native konum sınırlaması |
| R08/R09/R10 seyrek örtüsü | Açık/kuru yüzey, seyrek koyu doku | Kuru görünümden bitki türü veya doğal çalılık yokluğu çıkarılamaz |
| Yapı/tesis görünümü | Altı noktada asistan ön yorumu | Tesis kimliği veya termal kaynağın nedeni doğrulanmış değil; yangın dışlama gerekçesi ayrı |
| 5 km model hücresinin kapsamı | 2017 örtü bileşimi ve mevcut hücreler | Nokta çevresi yorumu bütün hücreye aktarılamaz; alan ve karışım kuralı ayrıca seçilmeli |

Bu çalışma yeni bir örtü ölçümü, tarihsel arazi kullanım doğrulaması veya
bağımsız olay referansı sağlamadı. Şu anda tekrar indirme kuyruğu açmak
yerine mevcut kanıtla çözülemeyen ayrımlar açıkça kaydediliyor.

## Araştırmacıya sunulan somut inceleme

R03, R11, R15 ve R16 için sarı yaklaşık tespit alanındaki görünüm soruldu:
doğal ağaçlık/çalılık, tarımsal görünüm, karışık veya ayırt edilemiyor.
27 Ekim bu kayıt hazırlanırken yeni yanıt yoktu. Görsel yorumu, bağımsız
uzman onayı veya 0/1 etiket kararı yerine geçmeyecek.

- [R03 alternatif tarihleri](../outputs/reports/dataset/preevent_date_comparison_v1/20261023T154219Z_144befb7/N20_815590_200133.png)
- [R11 ve R15](../outputs/reports/dataset/remaining_cover_review_v1/20261023T162553Z_e9d8f8dd/sheet_3.png)
- [R16](../outputs/reports/dataset/remaining_cover_review_v1/20261023T162553Z_e9d8f8dd/sheet_4.png)

## İlk iş paketinin kapanış sınırı

Öneri: bütün örnekleri zorla orman/tarım sınıfına atamak yerine kanıtın
desteklediği kapsam, kapsam dışı bağlam ve çözülemeyen durum ayrı
tutulmalı. Bu üçlü yaklaşımın nihai üretim kuralı henüz kabul edilmedi.
Bir eşiğin veya belirsizleri dışlama kararının kapsam ve seçim yanlılığı
etkisi ölçülmeden otomatik filtre kurulmayacak.

Habitat aşaması ancak nokta ve 5 km hücre için uygulanacak kuralın,
belirsizliğin nasıl taşınacağının ve ihtiyaç duyulan kanıt düzeyinin
belirlenmesiyle kapanabilir. 25 amaçlı örneğin görsel notları tek başına
genel bir filtre eşiği veya tüm takvim doğruluğu sağlamaz. Kabul edilen
kural daha sonra ilgili adaylara uygulanarak etkisi denetlenmelidir.

Sıradaki karar hazırlığı, insan notları geldiğinde bunları ayrı makbuzla
bağlamak ve çözülemeyen örnekler üzerinden kapsam seçeneklerini sunmaktır.
Olay gruplaması, güvenilir negatif ve bağımsız olay kanıtı konuları ayrı
iş paketlerinde açık kalır; bu tablo onların yerine geçmez.

## Teknik kapanış

Üretici: `scripts/quality/prepare_habitat_decisions.py`.
Yerel çıktı:
`outputs/reports/dataset/habitat_decision_queue_v1/20261027T183748Z_e1e64136/readback.json`.
SHA-256: `6cd6b2bbe0dc9ac026219541283af5f339557d2a3e7063fedffa5734337fd236`.

27 kaynak/kod kimliği kontrol edildi. 25 tekil nokta, 6 insan notlu nokta,
19 yalnız asistan notlu nokta ve 21 inceleme birimi eşleşmesi doğrulandı.
JSON diskten geri okundu; kaynak hash'leri işlem sonunda tekrar kontrol
edildi. Yeni betik lint/format kontrolünü geçti. Değişiklik kabul algoritması
değil, mevcut kanıtların karar hazırlığıdır; bilimsel üretim/test kuyruğu
yeniden çalıştırılmadı. Eski çıktılar değişmedi, ağ veya bulut işi yapılmadı;
etiket ve nihai birleştirme kapıları kapalı kaldı.

## Araştırmacı yanıtı sonrası ek kayıt

27 Ekim'de dört örnek için gelen insan yorumları yeni, ayrı makbuzla
kaydedildi. Yukarıdaki yanıt bekleniyor durumu önceki anın kaydıdır.
Yorumlar yönlendirilmiş görsel ön incelemedir; bağımsız uzman doğrulaması
veya üretim kapsamı onayı değildir.

| Örnek | Araştırmacının gözlemi | Korunan belirsizlik |
|---|---|---|
| R03 | Alternatif 2'de yeşil ormanlık alan; bulutlu düşünülen bölümde bozkır benzeri görünüm. Yanılma olasılığı açıkça belirtildi. | Doğal ağaçlık ve açık alan ayrımı kesin değil. Alternatif tarihlerde tekrarlanan parlak geometrik yüzeyler asistan incelemesinde sera benzeri; bulut olarak otomatik kabul edilmedi. |
| R11 | Tamamen kurak görünen alan. | Kuru görünüm, ölçülmüş kuraklık veya bütün alanda örtü yokluğu değildir. Kenarlarda odunsu görünüm bulunması ayrıca incelenmeli. |
| R15 | Görsel anlaşılamadı. | Örtü sınıfı atanmadı. Meteor benzetmesi fiziksel olay iddiası olarak kullanılmadı. |
| R16 | R15'e benzer görünüm. | Açık bir örtü sınıfı söylenmedi. R15 ile aynı hücre-gün biriminde olması iki bağımsız olay anlamına gelmez. |

Yeni dört tekil noktayla insan ön notu kapsamı 6'dan 10'a çıktı.
Önceki C teyidi dahil tarihsel not sayısı 11; insan notu bulunan inceleme
birimi sayısı 9/21'dir. Kalan 15/25 noktada yalnız asistan yorumu vardır.
Bu amaçlı örneklerin sayıları genel sınıflandırma doğruluğu değildir.

### Sonraki kapsam kararı için seçenekler

1. **Önerilen yön: kanıt düzeyini koruyan kapsam.** Doğal orman/çalılık
   bağlamı desteklenen, başka kullanım bağlamı desteklenen ve çözülemeyen
   durumlar ayrı tutulur. Karışık veya ayırt edilemeyen örnekler veri
   kaybı olmadan incelemede kalır. Ek kanıt ve nokta–hücre kuralı gerektirir;
   bu nedenle henüz otomatik eğitim filtresi vermez.
2. **Daha geniş harita temelli kapsam:** eski haritada orman/çalılık
   kesişimi bulunan adayların tamamı ön havuzda tutulur. Uygulaması kolaydır;
   ancak harita yaşı, yönetilen tarım örtüsü ve nokta–hücre farkı nedeniyle
   doğal yangın kapsamı kabulü olarak kullanılamaz. Yalnız duyarlılık
   karşılaştırması için hazırlanabilir.

Öneri bir yöntem kabulü olarak uygulanmadı. İnsan gözleminin çözemediği
R15/R16'ya tekrar zorunlu sınıf seçtirmek yerine ek örtü kanıtı ihtiyacı
korunacak. Bir sonraki teknik hazırlık, nokta desteği ile 5 km hücre
kapsamını ayıran kural adaylarını ve kapsam etkilerini sunmaktır. Nihai
kural kullanıcı kararı ve uygun kanıt kontrolleri gerektirir.

Yeni makbuz:
`outputs/reports/dataset/habitat_researcher_notes_v2/20261027T184619Z_c71bd189/readback.json`.
SHA-256: `8bf261ccf2c3b9677dc3970b1c1af06c22411dc4b8b36cf24d9bef30f603389e`.
28 kaynak hash'i işlem öncesinde ve sonrasında kontrol edildi; dört
kimliğin önceki altıyla çakışmadığı, toplamların doğruluğu ve JSON geri
okuması doğrulandı. Türkçe metinde bozuk Unicode yer tutucusu bulunmadığı
kontrol edildi. Eski çıktılar değiştirilmedi; yeni indirme, etiket,
otomatik dışlama veya nihai birleştirme yapılmadı.
