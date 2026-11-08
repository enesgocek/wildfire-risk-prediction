# Yangın tespitinden bağımsız PU inceleme örneklemi — 8 Kasım 2026

2018–2023 takviminden incelenebilir iki tablo hazırlandı. İkisi de
yerel takvim, gözlem tabloları, 2017 referans örtüsü ve onaylı tam su
kuralı kullanılarak üretildi. Seçim sırasında yangın tespit kataloğu
okunmadı. İnceleme etiketleri boş tutuldu. [Takvim denetimi](PU_CALENDAR_OBSERVATION_2026-11-08.md).

## Tablolar nasıl okunur?

| Tablo | Seçim | Kullanım |
| --- | --- | --- |
| `sample.csv` | Dört il × altı yıl × dört mevsimde, her gruptan bir hücre-gün | Genel inceleme. İl, yıl ve mevsimi temsil etmek için dengeli seçim. |
| `contrasts.csv` | Tam su, orman/çalılık işareti yok, seçili kara merkezi yok, uzun nominal aralık, tek sensör ve iki ürün boşluğu | Veri sorunlarını yan yana inceleme. Bu örneklerin sıklığı araştırma alanındaki oran olarak yorumlanamaz. |

Ana tabloda 2017 haritasındaki tam su kuralı uygulandı. Başka örtü
eşiği kullanılmadı. Haritada orman/çalılık payı sıfır olan hücreler de
ana örnekleme girebilir. Tam su hücreleri tanı tablosunda ayrıca
gösterilir. `forest_shrub_fraction`, kaynak haritasında kapsanan alanın
payıdır. Tarihli doğal örtü veya yangının ilk tespit noktasındaki örtü
kararı ayrı bir kontroldür.

Seçimden önce ana gruplar il, takvim yılı ve mevsim olarak tanımlandı.
Sabit tohumla ay içinde sıralı hücre-günlere rastgele öncelik verildi ve
her grup için en düşük öncelik değerine sahip satır seçildi.
`stratum_rows` grubun tam su sonrası büyüklüğünü,
`inclusion_probability` bir satırın o grupta seçilme olasılığını gösterir.
Örneğin grubu 10.000 satır olan bir hücre-gün için olasılık 1/10.000’dir.
Tanı satırları ayrı bir rastgele sıralamadan gelir ve sadece belirtilen
durumları görünür kılmak için kullanılır.

`prediction_day_utc` tahmin günüdür. `source_sensors`, nominal günde
çalışma alanında kaydı olan sensörleri gösterir. Gözlem ve örtü tanıları
inceleme bağlamıdır. Gözlem sütunları tahmin girdisi olarak kullanılmaz.
Ürünü olmayan satırın sayısal gözlem alanları boş bırakıldı. Ürünü
olup seçili kara merkezi bulunmayan satırda ilgili sayı sıfırdır.

## Bulgular ve iki örnek

2.899 kaynak hücrenin 10'u tam su kuralıyla ana örnekleme alanı dışında
işaretlendi. Böylece ana seçim 2.889 hücre ve 2.191 günden oluşan
6.329.799 hücre-gün üzerinden yapıldı. **96 ana satır ve 31 ayrı tanı
satırı** seçildi. Mersin'de tam su kuralına giren hücre olmadığından
bu tanı grubu üç ilde bulunuyor. İki eksik ürün günü, dört ilin her
birinden birer satırla tanı tablosunda gösterildi.

Ana örneklemde 63 satırda seçili kara merkezi var ve nominal en uzun
aralık 12 saatin altında. 27 satırda seçili kara merkezi var ve aralık
en az 12 saat. Altı satırda seçili kara merkezi sıfır. 93 satırda 2017
haritası hücrenin bir bölümünü orman veya çalılık olarak gösteriyor.
Bu sayılar 96 satırlık örnekleme aittir.

Antalya'da 13 Haziran 2018 için seçilen hücrenin haritadaki orman/çalılık
payı %96,55. Ürün eksik olduğu için kara merkezi sayısı boş. 22 Aralık
2023 için seçilen başka bir Antalya hücresinin payı %82,85. Ürün var ve
seçili kara merkezi sayısı sıfır. İki satırın hedef hücresi boş kaldı.
İki tablonun dosya özetleri, 96 grubun seçim olasılıkları ve 31 tanı
satırının kaynak değerleri geri okumada doğrulandı.

## Nihai veri setine kalan üç aşama

1. **Hedef ve değerlendirme protokolü.** Güvenilir yeni orman/çalılık
   olayını kabul etmek için gereken kanıtı, gözlemin `(T,T+24h]`
   penceresiyle bağını ve değerlendirmenin dayanağını belirlemek. PU
   seçeneğinde pozitif adayların güvenilirliği, etiketlenme mekanizması
   ve sınıf oranı için desteklenebilir varsayımlar veya belirsizlik
   sınırları gerekiyor. [PU uygulanabilirliği](LABEL_PROTOCOL_DECISION_2026-11-04.md).
2. **Parça bazında son kontrol ve araştırmacı onayı.** Meteoroloji,
   arazi/örtü, bitki örtüsü, gözlem ve hedef parçalarının dosya kimliği,
   anahtar, şema, eksik değer, zaman, dönem ayrımı ve kabul protokolü
   kontrolü birlikte sunulur. Onay güncel rapor kimliğine bağlanır.
3. **Birleştirme ve teslim doğrulaması.** Onaydan sonra sürümlü paket
   hazırlanır. Anahtarlar, satır sayıları, dönem sınırı ve sızıntı
   kontrolleri yayımlanan paket üzerinde tekrar doğrulanır.

İlk aşama açık olduğu için üç adımın toplam süresi hesaplanamaz. Ana
hedefi koruyarak bir sonraki teknik iş, eldeki zaman ve olay kanıtıyla
hangi kabul kuralının gerçekten sınanabildiğini ortaya koymaktır.

Yeniden üretim komutu `python scripts/quality/prepare_pu_calendar_sample.py`.

Yerel çalıştırma kimliği `20261108T013027Z_d2b1102c`.
Denetim makbuzunun SHA-256 değeri
`84ab70f35c201ea36453e91c7e50a69c4123328456c37140ec4f6efafbdb5bf4`.
