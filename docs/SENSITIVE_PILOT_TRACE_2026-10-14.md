# Senaryoya duyarlı 19 pilot örneğin kaynak ve zincir incelemesi — 14 Ekim 2026

Durum: yerel otomatik inceleme ve geri okuma tamamlandı. Fiziksel olay
kimliği, kaynak Type semantiği ve etiket politikası kabul edilmedi.
Başlangıç, [400 örnekteki protokol karşılaştırmasıdır](LABEL_PROTOCOL_REVIEW_2026-10-14.md).
Bu rapor bağımsız uzman veya insan incelemesi değildir.

## Kapsam ve yöntem

Sabit pilotta üyeliği değişen 11 örnek ve yalnız bazı senaryolarda ilk aday
eşleşmesi bulunan sekiz örnek seçildi. Toplam 19 hücre-gün, eşit olmayan
olasılıklı pilotun amaçlı alt kümesidir; popülasyon hata oranı çıkarılmaz.
2018–2023 eğitim verisindeki Type=0, n/h güvenli FIRMS adayları kullanıldı.
2024 doğrulama ve 2025 final test kaynakları açılmadı.

Her örneğin hücresinde `(T,T+24 saat]` içindeki **bütün kaynak adayları**
bağlantı noktası olarak alındı: toplam 35 farklı kayıt. Bir ortak bağlantı
noktası bütün ayrık kümelere zorlanmadı. Dokuz kayıtlı senaryonun her
birinde bu noktaları içeren bütün kümeler izlendi. Böylece ilk hücre/gün
eşleşmesinin bulunmadığı senaryolar da kapsandı; yalnız eşleşen 138
varyantla inceleme sınırlandırılmadı.

Dokuz atama tablosunun her biri 30.295 eğitim kaynak kimliği, hücresi,
sensörü ve zamanı ile karşılaştırıldı. İncelenen kümelerde üyelik hash'i,
ilk/son zaman, eşzamanlı bütün ilk tespitler/hücreler ve üye sayısı yeniden
doğrulandı. WGS84 merkez uzaklığı ve 24/48/72 saat mutlak farkıyla iç
graf yeniden kuruldu; seçilen 181 varyantın her biri bağlı bulundu.
Bu kontrol bütün kataloğun küresel yeniden gruplanması değildir; dışarıda
bağlanabilecek üye kalmadığının dayanağı önceki hash bağlı bölüm denetimidir.

En az kenarlı yollar her ilk tespitten o kümedeki her pilot bağlantı
noktasına çıkarıldı. Eşit yollar kimlik sırasıyla seçildi. Graf yönsüzdür;
zamanı geriye götüren kenarlar korunur. Bu yollar yayılma yönü, gerçek
tutuşma zamanı veya tek fiziksel yangın kanıtı değildir. Kaynak incelemesi
donmuş FIRMS kayıtları ve yakın Type=2 bağlamıdır; yeni uydu görüntüsü
yorumlama veya native L2 pikselinden bağımsız yangın doğrulaması yapılmadı.

## Geri okunan sonuç

| Ölçüm | Sayı ve birim |
|---|---:|
| Amaçlı pilot alt kümesi | 19 hücre-gün |
| Pencere/hücre içindeki kaynak bağlantı noktası | 35 farklı tespit |
| Hücre-gün/senaryo çifti | 171 |
| Bu noktalara bağlı küme bağlamı / farklı küme-senaryo varyantı | 181 / 181 |
| İlk hücre/gün eşleşmesi olan bağlam | 138 |
| İlk zaman önceki hedef gününde; ilk hücre örnek hücresini içeriyor | 31 |
| İlk zaman önceki hedef gününde ve ilk hücre örnek hücresini içermiyor | 12 |
| Senaryo tekrarlarıyla üye satırı / farklı kaynak tespiti | 38.639 / 5.436 |
| İlk tespit–bağlantı noktası yolu / yol-düğüm satırı | 1.863 / 39.694 |

Son üç eşleşme satırı 181 bağlamı böler. 43 eşleşmesiz bağlamın tamamında
kaynak noktaları mevcuttur; ilk zaman daha önceki bir pencereye gider.
12 bağlamda ayrıca ilk hücre de değişir. Bunlar 43 kayıp kayıt, negatif
örnek veya bağımsız yangın değildir. Aynı örnekte birden fazla küme olabilir.
Önceki paketin eşleşen küme kimlikleri, üyelik hash kümeleri ve sayıları
19 örneğin dokuz senaryosunda birebir tekrarlandı.

Küme başına ilk zamanların sıralı listesi 10 örnekte; küme başına ilk
hücre kümelerinin listesi sekiz örnekte değişiyor. Bu **imzalar** bölünme/
birleşmeyle listedeki öğe sayısının değişmesini de içerir; 10 ayrı olayın
başlangıcının veya sekiz örneğin hücresinin kesin yer değiştirdiği sonucu
çıkarılamaz. Ayrıntılar `unit_scenario_components.csv` içindedir.

## 19 örneğin tamamı

Hücre adlarında ortak `E6933_5K_V1_` öneki aşağıda kısaltıldı. Gün, T'nin
UTC takvim günüdür. Son sütun, o örneğin bağlantı noktalarını içeren
senaryolardaki en büyük keşif kümesinin tespit sayısıdır; yangın sayısı değildir.
9/9 eşleşme üyeliğin aynı veya etiketin kabul edilmiş olması anlamına gelmez.

| Hücre | T günü | İlk aday eşleşen senaryo | En büyük bağlı küme |
|---|---|---:|---:|
| C519_R917 | 2018-03-12 | 9/9 | 4 |
| C675_R877 | 2018-05-26 | 9/9 | 3 |
| C674_R878 | 2018-09-01 | 9/9 | 3 |
| C593_R880 | 2019-07-28 | 9/9 | 2 |
| C520_R916 | 2019-09-11 | 3/9 | 36 |
| C596_R878 | 2019-10-04 | 6/9 | 2 |
| C519_R917 | 2020-01-13 | 9/9 | 2 |
| C595_R878 | 2020-01-21 | 3/9 | 4 |
| C677_R878 | 2020-04-18 | 9/9 | 4 |
| C519_R917 | 2021-03-28 | 7/9 | 18 |
| C519_R917 | 2021-05-13 | 3/9 | 9 |
| C606_R882 | 2021-08-05 | 1/9 | 5.304 |
| C557_R877 | 2021-10-05 | 9/9 | 22 |
| C649_R864 | 2021-11-05 | 7/9 | 2 |
| C520_R916 | 2022-11-05 | 3/9 | 9 |
| C676_R876 | 2023-09-03 | 9/9 | 2 |
| C596_R878 | 2023-09-23 | 9/9 | 3 |
| C583_R882 | 2023-10-12 | 9/9 | 5 |
| C597_R878 | 2023-11-19 | 9/9 | 2 |

## Araştırmacı için üç açıklayıcı örnek

**21 Ocak 2020, C595_R878 — 533 metrelik bağlantı yeni aday gününü değiştiriyor.**
500 m senaryolarında o günün bir tespiti, önceki gün başlamış üç üyeli
kümeden ayrı kalır; bu yüzden o hücre/günde hâlâ bir ilk aday eşleşmesi
vardır. 1.000 ve 2.000 m senaryolarında dört kayıt birleşir, ilk zaman
20 Ocak 23:27 UTC olur. `SNPP_815579_77651` ile ayrı kalmış
`N20_815590_75522` arasındaki doğrudan tanık **533,02 m / 10,53 saat**tir.
İkinci noktanın zamanı 21 Ocak 09:59 UTC'dir. Kaydın silinmesi değil,
mesafe kuralının olay adayı tanımını değiştirmesidir; hangi tanımın fiziksel
olayı doğru anlattığı bu hesapla çözülmez.

**4 Ekim 2019, C596_R878 — aynı anda hedef gün ve ilk hücre değişiyor.**
500 ve 1.000 m'de `N20_815590_62588` tek üyeli ilk adaydır: 4 Ekim
10:42 UTC. 2.000 m'de önceki gün 11:01 UTC'deki
`N20_815590_62137` ile birleşir. İlk hücre C596_R879 olur;
merkezler arası **1.436,38 m**, zaman farkı **23,68 saat**tir. Yerel
bağlantı kuralı altında bu iki kayıt bağlanabilir; aynı fiziksel yangın
oldukları kabul edilmedi. Sadece tek canonical hücre seçilerek bu fark gizlenmedi.

**5 Ağustos 2021, C606_R882 — küçük bir aday büyük bir bileşene katılıyor.**
500 m/24 saatte bu günün iki kaynak noktasından biri 3.578 üyeli kümeye
bağlı, diğeri tek üyeli ilk adaydır; örnek 1/9 senaryoda ilk aday eşleşmesi
verir. Diğer senaryolar iki noktayı da daha önce başlamış kümelere bağlar.
En geniş varyant 5.304 tespit içerir; 28 Temmuz 10:11–6 Ağustos
23:03 UTC aralığındadır. Bu sayı binlerce bağımsız yangın veya tek yangın
kimliği değildir. 500 m/24 saatte seçilmiş bir tanık yol,
`N20_815590_134795` → `SNPP_815579_144908` için **48 kenar** içerir;
her kenar kendi mesafe/zaman sınırını sağlar. Yolun bazı adımları geçmişe
gider. Eşzamanlı bütün ilk tespitler ayrı korundu; fiziksel yayılma yolu
olarak okunmamalıdır.

En büyük küme ile en uzun küme farklıdır: C520_R916'nın 11 Eylül 2019
örneğine bağlı 72 saat varyantları yalnız 36 tespitli olmasına rağmen
28 Ağustos 00:06–30 Eylül 23:28 UTC arasında **815,37 saat / 33,97 gün**
sürer. 72 saat, toplam küme ömrünü sınırlamaz. Bu devamlılık fiziksel yangın
süresi olarak kabul edilmedi.

## Kaynak bağlamı ve bilimsel sınır

5.436 farklı üyenin 75'inde, 35 pilot bağlantı noktasının altısında
önceki 1 km yakınlıkta Type=2 kaydı vardır. Bu yakınlık geriye dönük kaynak
tanısıdır; endüstriyel köken kanıtı, eleme kuralı veya model girdisi değildir.
FIRMS Type üretim semantiği hakkındaki açık teknik konu devam eder.

181 varyantın ilk/son zamanına kenar aralığı eklenerek oluşturulan takvim
çevresi, kayıtlı iki ertelenmiş güne veya eğitim dışına uzanmıyor. Bu dar
sonuç bütün eğitim kaynaklarının tamam olduğunu veya gözlem yeterliliğini
kanıtlamaz. İki kaynak günü ve önceki gözlem belirsizlikleri açık kalır.

Öneri, bu 19 örneği silmek veya otomatik negatif yapmak yerine kaynak ve
senaryo duyarlılığıyla saklamaktır. Geniş mesafe veya uzun zaman aralığı
daha doğru kabul edilmedi. Bütün senaryoların uzlaştığı örneklerle sınırlı
bir veri seti de seçilmedi; bu seçim kapsam yanlılığı yaratabilir.
Sıradaki iş bu ölçümleri, 181 arka plan adayının gözlem yeterliliğiyle
birlikte karar verilebilir olay/gözlem kabul seçeneklerine dönüştürmektir.

Araştırmacının insan gözüyle değerlendirebileceği somut soru: yukarıdaki
533 m ile 1.436 m bağlantı ve uzun zincir örneklerinde bir günlük ilk
tespit hedefinin hangi belirsizlikleri açıkça taşıması gerektiği. Görüntüye
bakarak tutuşma zamanı veya doğru 0/1 etiket tahmin etmesi istenmiyor.
Bu raporun okunması yöntem veya nihai birleştirme onayı sayılmaz.

## Teknik kontrol ve kanıt

Yeni 21 davranış testiyle birlikte **94 ilgili test** geçti. İlk hücre
değişiminin aynı gün içinde olabilmesi, ayrık kümelere ayrı bağlantı noktası,
bütün ilk zaman bağları, `(T,T+24 saat]` gece yarısı sınırı, geriye giden
yönsüz yol, bozuk üyelik/kaynak, eksik senaryo ve kapalı etiket koşulları
kontrol edildi. Üç yeni Python dosyasında lint/format geçti.

Beş CSV kayıpsız geri okundu; **57 giriş, beş çıktı ve 22 donmuş bulut
girdisi** hash kapanışını geçti. Özgün pilot ve katalog dosyaları
değişmedi. Etiketler boş, `daily_observation_status=unknown`, pozitif ve
negatif etiket izinleri kapalı, `model_ready=false`. Olay politikası,
nihai birleştirme veya insan kabulü yapılmadı; model, holdout veya bulut
işi başlatılmadı. İşlem yereldir ve ağ bağlantıları engellenmiştir.

Komut: `.venv\Scripts\python.exe scripts/quality/trace_sensitive_pilot.py`.
Sonuç dizini: `outputs/reports/dataset/sensitive_trace_v1/20261014T194620Z_284f08c1/`.

- `unit_trace_summary.csv`: 19 örneğin özeti.
- `unit_scenario_components.csv`: eşleşen/eşleşmeyen 181 küme bağlamı.
- `component_graph_review.csv`: üyelik ve iç graf kanıtı.
- `component_source_members.csv`: kaynak kimliği/konumu/zamanı ve yakınlık tanıları.
- `first_to_pilot_anchor_paths.csv`: her ilk tespitten ilgili bağlantı noktasına tanık yollar.

`readback.json` SHA-256:
`f613115b0d67caea55353b102e2c420d1879666dfc8f94ea52416b0e9954fa11`.
Kapanış SHA-256:
`000ed76785212fc4a2b32cc4bdb806aabddba7c22b7ddee0caab85a3ad40dac1`.
Kaynak ve önceki rapor kimliklerinin tamamı geri okuma manifestindedir.
