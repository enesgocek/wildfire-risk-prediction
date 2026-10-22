# Tam eğitim kataloğunda ilk-gün adayı duyarlılığı

22 Ekim 2026. Araştırmacı üniversite üzerinden OGM talebini şimdilik
planlamadığını belirtti; bu kanal ilerlemenin zorunlu önkoşulu yapılmadan
mevcut kanıtla devam edilmesi istendi. Bu, OGM'nin veri paylaşamayacağı,
bağımsız doğrulamanın gereksiz olduğu veya hedefin değiştiği anlamına gelmez.
Yeni dış ileti veya kurumsal talep gönderilmedi.

## Amaç ve gerçekleşen işlem

Önceki 400 birimlik pilot/19 duyarlı örnek bütün adayların ayar duyarlılığını
ölçmüyordu. Bu iş, korunmuş dokuz kataloğun tamamında **ilk hücre + tahmin
günü** anahtarlarını karşılaştırır. Kaynak 2018–2023 dönemindeki seçilmiş
30.295 Type=0, nominal/yüksek güven tespitine dayanan eski kataloglardır.
21 Ekim yeni FIRMS teslim eşitliği ayrıca kaynak kanıtına bağlandı.

Dokuz katalog 500/1.000/2.000 metre × 24/48/72 saat nokta bağlantı
kurallarını kullanır. Yeni grafik veya eşik üretilmedi. Araştırmacının
16 Ekim A tercihiyle bütün eşzamanlı ilk hücreler aynı bileşen kimliği
altında korundu. `(T,T+24h]` sağ kapalı pencere kontrolü yeniden kullanıldı.

67.577 senaryo-bileşen-ilk-hücre satırı, **7.610 farklı aday hücre-gün**
anahtarına açıldı. Bir senaryoda aynı hücre-günde birden fazla bileşen varsa
tek senaryo desteği sayıldı; bileşenler ayrıntı tablosunda kaybedilmedi.
Bütün anahtarlar eğitim döneminde kaldı. Bu sayılar bağımsız yangın,
pozitif etiket veya bütün özellik satırlarının paydası değildir.

## Sonuç

| Ayrık tanı grubu | Aday hücre-gün | Anlamı |
|---|---:|---|
| Dokuz ayarda varlık, ilk zaman kümesi ve üyelik kümesi eşit | 5.214 | Parametre değişiminde bu tanılar aynı; doğruluk kabulü yok |
| Dokuz ayarda aday var, ilk zaman veya üyelik farklı | 977 | Yalnız aday varlığına bakmak belirsizliği gizliyor |
| Aday yalnız bazı ayarlarda var | 1.419 | İlk-gün aday varlığı seçilen ayara bağlı |
| Toplam | 7.610 | Dokuz ayarın birleşimi; aday olmayan günler bu tabloda yok |

2.396 anahtar en az bir ayar duyarlılığı taşıyor. 5.214 eşit tanılı
anahtarın **311'inde** katalog inceleme işareti var; 4.903'ünde bu işaretler
yok. İşaret yokluğu kaynak tamlığı, uygun habitat, bağımsız olay veya
yeterli gözlem kanıtı değildir. Bütün gruplar etiketsiz korunur; 5.214 veya
4.903 satır ana eğitim kümesi olarak seçilmedi. Dokuz ayar aynı kaynağı
kullandığından dokuz bağımsız doğrulama sayılmaz.

## Somut inceleme örnekleri

| Hücre / tahmin günü | Aday bulunan ayar | İnceleme konusu |
|---|---:|---|
| C507_R908 / 2021-06-27 | 9/9 | İlk zaman/üyelik aynı, katalog işareti yok; gözlem ve olay kanıtı ayrıca gerekli |
| C518_R907 / 2021-06-20 | 9/9 | İlk zaman/üyelik aynı, mekânsal zincir işareti var |
| C606_R882 / 2021-08-05 | 1/9 | Önceki büyük bileşen örneğinde aday varlığı duyarlı |
| C520_R916 / 2022-11-05 | 3/9 | Önceki birleşme örneğinde aday varlığı duyarlı |
| C557_R877 / 2021-10-05 | 9/9 | Aday her ayarda var; zaman/üyelik imzası aynı değil |

Beş örnek amaçlıdır; hata oranı örneklemi değildir. İlk iki örnek, 2021'deki
ilgili grupların hücre/tarih sıralamasında ilk kaydıdır; kalan üçü önceki
somut inceleme vakalarıdır. `review_examples.csv` ve 45 satırlık
`case_scenarios.csv` özgün kimlikleri ve ilk zamanları gösterir. Eksik aday
bayrağı gerçek yangın yokluğu değildir; kullanıcıdan yalnız bu tabloya
bakarak fiziksel yangın kimliği veya doğru mesafe eşiğini tahmin etmesi
beklenmez. Uygun dış kanıt gelirse bu somut örneklerde neyi desteklediği
açıkça gösterilerek yöntem seçenekleri sunulacaktır.

## Doğrulama ve çıktı kimlikleri

13 yeni vaka dahil **41 ilgili test** geçti; bütün depo testleri değildir.
Çok ilk hücre, senaryo başına tek destek, eksik ayar, tekrar, değişen üyelik/
ilk zaman, eğitim dışı tarih, boş hedef ve gece yarısı sınırı sınandı.
İlk geliştirme testinde zaman çıkarma biçimi uyarı verdi; donmuş kodu
değiştirmeden mevcut pencere hesabı kullanıldı ve son testler uyarıları
hata kabul ederek geçti. Üç yeni Python dosyasında lint/format geçti.

Ana sonuç `outputs/reports/dataset/full_event_sensitivity_v1/20261022T204358Z_820d043d/`.
Readback SHA-256 `40818450ec28a2597eca1155bb6bb5896ce41fc65ec5fad2db6f1314d7229a86`.
17 doğrudan girdi başta/sonda aynı; altı çıktı hash'i, CSV şekilleri/boş
hedefleri ve JSON geri okuması kontrol edildi. Önceki katalogların hash'leri
korunmuş inceleme raporuna eşleşti; 30.295 ham tespit yeniden parse edilmedi.

Ayrı standart CSV okuyucusuyla 7.610 anahtarın ve 67.577 ayrıntı satırının
destek, zaman/üyelik çeşitleri, işaret birleşimi, kategorisi ve kapalı kabul
alanları yeniden hesaplandı. Bu ikinci otomatik hesap uzman doğrulaması değildir.
Sonuç ve örnekler `outputs/reports/dataset/full_event_sensitivity_v1/20261022T204540Z_ac2af75f_readback/`.
Readback SHA-256 `41b79018b74e030f37ff3c080d7e956866da8a5f7049f3d610d90de743a4da62`.

## Sonraki iş ve sınır

Gruplama seçimini tek bir keyfî eşikle kapatmak yerine, bu aday gruplarının
mevcut gözlem pilotuyla kesişimi ve uygun açık referansların gerçekten
sağladığı kanıt incelenecek. Öncelik açık kanıtla değerlendirilebilen sınırlı
bir örneklem; bütün 7.610 anahtarın bağımsız doğrulandığı varsayılmayacak.
Gözlem politikası için ayrı kabul gerekçesi gerekiyor; aday tablosunda
bulunmayan milyonlarca özellik satırı otomatik negatif yapılmayacak.

Yeni hedef veya dışlama politikası seçilmedi. Habitat, kaynak gün eksikleri,
zaman/üyelik ve gerçek yangın yokluğu açık konulardır. `target` boş,
`daily_observation_status=unknown`, pozitif/negatif izinleri false kaldı.
2024/2025 açılmadı; özellik hesabı, bulut işi, eğitim ve nihai birleştirme yok.
