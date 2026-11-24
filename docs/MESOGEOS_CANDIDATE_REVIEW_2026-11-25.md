# Mesogeos 32 kayıt incelemesi ve aşama durumu — 25 Kasım 2026

## Güncel durum ve plana göre ilerleme

Araştırmacı 32 farklı durumun incelenerek uygunları için ayrı, hata içerebilen
S önerileri hazırlanması yönünü açıkça seçti. Bu devamda yeni indirme veya
model kurmadan bu hazırlık tamamlandı. Karar
`configs/mesogeos_candidate_review_v1.json` içinde; önceki yalnız yardımcı
kaynak incelemesinin kapsamından ayrı tutulur.

Teknik hazırlık ilerledi: mevcut 44.082 satır/27 özellikli deneysel S/U
paketi, geçmiş yıllarda sınanan modeller, haritalı prototip ve rapor taslağı
var. **Ana hedef için bilimsel kabul henüz tamamlanmadı.** Kaynak adayını
ayırt etme/sıralama sonucu, gerçek yeni orman yangını risk başarımı olarak
doğrulanmış değil. Veri miktarı tek başına bu boşluğu kapatmıyor.

[22 Kasım planının](DELIVERY_PLAN_REVIEW_2026-11-22.md) 26–29 Kasım birinci
aşama karar aralığı bugün henüz geçmedi. Tahmini 1 Ocak 2027 teslimine
37 takvim günü var; resmî teslim tarihi teyit edilmiş değil. Teknik araştırma
teslimi için somut temel var, doğrulanmış risk sistemi için yetişme garantisi
yok. Tamamlanma yüzdesi, test/model/belge sayısından türetilmedi. Önceki
tarihli plan ve deney sonuçları değiştirilmedi.

## Tamamlanan 32 kayıt incelemesi

Önceki pilotta ham gün/hücre aramasında 60 eski S bağlamı dışında kalan
**5 mevcut U + 27 takvimde bulunmayan anahtar** seçildi. Yıllara göre
2/3/7/10/10 kayıt; kaynak il alanlarına göre İzmir 12, Muğla 9,
Antalya 7, İçel/Mersin 4. Bunlar bağımsız yangın sayısı değildir.

İki ayrı örtü kontrolü korundu: mevcut hücrenin donmuş örtü payları ve
kaynak noktasındaki raster sınıfı. 32 hücrenin tamamı önceki su kuralını
geçiyor. Asgari orman oranıyla hücre silinmedi.

| Kaynak noktasının harita bağlamı | CGLS 2017 ana | CORINE 2018 yardımcı |
|---|---:|---:|
| Orman/çalılık | 11 | 8 |
| Tarım | 8 | 11 |
| Diğer | 13 | 13 |

Altı nokta iki haritada da orman/çalılık. Fark, haritaların doğruluk
karşılaştırması değildir. Nokta sınıfı bütün MODIS pikselinin veya olay
günündeki yanan örtünün sınıfı sayılmaz. CORINE 2018, 2018 olaylarından
sonrasını içerebilir; zorunlu kabul filtresi yapılmadı. 21 ana harita
orman/çalılık dışı kayıt silinmeden tutuldu.

### Saat ve yeni olay bağlamı

MODIS alanları korunmuşsa UTC yorumu ile yalnız duyarlılık amaçlı eksi üç
saat yorumu ayrı sınandı. İkinci yorum kaynağın Türkiye yerel saatinde
olduğu iddiası değildir. Doğru saat yorumunun yerini almak için kullanılmadı.
Hazır örneklerdeki eksi bir gün dönüşümü uygulanmadı. `(T,T+24h]` sözleşmesi
korundu; tam gece yarısı önceki pencereye düştü. **28 kaydın koşullu hedef
günü aynı kaldı, dördünde değişti.**

Mevcut, yalnız 2018–2022'yi kapsayan 28.396 VIIRS merkezinin donmuş
tablosunda her kaynak için önceki 24/48/72 saat ve 500/1.000/2.000 m
bağlamı ayrı sayıldı. Eşzamanlı ve sonraki 24 saatlik tespitler ayrı
tutuldu. Sonraki kayıt yeni olay kanıtı veya tahmin girdisi yapılmadı.
Yakın önceki tespitler aynı fiziksel olay olduğunu; tespit yokluğu ise
yeni olay olduğunu kanıtlamaz. Ana veri setinin gözlem açığı sürüyor.

Ayrı hazırlık dosyasında yalnız şu **varsayımlara bağlı öneri maskesi**
üretildi: hedef penceresi izinli dönemde, hücre su kapsamında, kaynak
merkezi 2017'de orman/çalılık, seçilen yakın geçmişte önceki VIIRS merkezi
yok ve geçmiş aralığı kaynak döneminin içinde. Bu bir olay tanımı kabulü
değil; gözlenmeyen geçmişin eksikliği ve merkez/gerçek örtü farkı hata
kaynağı olarak kaydedildi. Dokuz ayardan üretim ayarı seçilmedi.

| Saat varsayımı | Mesafe | Her 24/48/72 saat ayarında koşullu öneri |
|---|---:|---:|
| Alanlar korunmuşsa UTC | 500 m | 7 |
| Alanlar korunmuşsa UTC | 1.000 m | 5 |
| Alanlar korunmuşsa UTC | 2.000 m | 5 |
| Yalnız eksi üç saat duyarlılığı | 500/1.000/2.000 m | Her birinde 10 |

Toplam 32 × 2 × 9 = **576 senaryo satırı** üretildi; bağımsız örnekler
gibi sayılmadı. 22 kayıt hiçbir senaryoda öneri değil; üçü 9/18,
ikisi 12/18, beşi 18/18 öneri. **Bu beşinin hedef günü de iki saat
yorumunda aynı kaldı.** Bunlar doğrulanmış beş yeni yangın değildir.

| Kaynak kimliği | Ham gün | Kaynak ili | Yardımcı 2018 merkez bağlamı |
|---|---|---|---|
| 41928 | 2020-07-21 | Muğla | Orman/çalılık |
| 42009 | 2020-08-13 | İzmir | Tarım |
| 51935 | 2021-08-02 | Muğla | Orman/çalılık |
| 206973 | 2022-07-22 | İzmir | Tarım |
| 206037 | 2022-07-14 | İzmir | Diğer |

Beşinde de ana 2017 merkez bağlamı orman/çalılık. Üçündeki yardımcı
harita farkı olay günü örtüsünün ayrıca belirsiz kalmasının somut örneği.
Kaynak kimliği gerçek tutuşma kimliği değildir; örtü/saat/olay şartları
çözülmeden ana S/U tablosuna kabul edilmiş üyelik eklenmedi.

## Doğrulama

30 ilgili test bu devamda geçti: önceki/sonraki/eşzamanlı ve uzak kayıtların
ayrılması, boş gözlemin sıfır sayım olarak kalması, gece yarısı penceresi,
önceki yıl/saat korumaları ve hedef kabul kapıları. İlk testte yeni çağrının
UTC ISO metni yerine zaman nesnesi verdiği yakalandı; yeni çağrı düzeltildi,
eski zaman çekirdeği değiştirilmedi. Hatalı çağrıyla veri üretimi yapılmadı.
NumPy/Pandas timedelta uyumluluk uyarıları çıktı; üretim tamamlandı, sonuçlar
ayrıca standart datetime/timedelta ile geri hesaplandı. Uyarılar bilimsel
başarısızlık veya yok sayılan veri hatası olarak gizlenmedi.

Ayrı denetim 32 noktanın iki raster pikselini doğrudan pencere okuyarak;
576 zaman/mesafe sayımını standart saat aritmetiği ve skaler jeodezik
mesafeyle doğruladı. Donmuş girdi, çıktı ve eski S/U hash'leri eşleşti.
Gerçek yangın kimliği veya bağımsız arazi doğrulaması yapılmış sayılmaz.

`outputs/reports/dataset/` altında:

- Hazırlık: `mesogeos_candidate_context_v1/20261124T234645Z_8d88cfe5`.
  Makbuz SHA-256 `ae94cfbf8659e42bd463af33b2357bfaba3e74f63e9ed4b59b7a1d49650ecb48`.
- Ayrı denetim: `mesogeos_candidate_context_audit_v1/20261124T234801Z_9b662cb9`.
  SHA-256 `c1a181f96e6a7f09079eb0108d243b0c7b9bb90f06b59a0cab48016c0b09b449`.

## Birinci aşama geçiş değerlendirmesi ve sınır

| Gerekli dayanak | Bu çalışma sonrasında durum |
|---|---|
| Yeni orman/çalılık olayı ve ilk hücre/gün kabulü | Beş ayar-kararlı koşullu öneri; gerçek olay, saat ve olay günü örtü kabulü hâlâ açık |
| PU/gürültü varsayımlarının yangın hedefine aktarımı | Yeni kanıtla doğrulanmadı; uydu kökenli kaynak bağımlılığı sürüyor |
| Gerçek hedefi değerlendirecek yeterli referans | Kaynak alan bağlamı genişledi; gerçek yangın AP/kalibrasyon doğrulaması sağlanmadı |

Bu inceleme tamamlandı; yalnız kayıt sayısını artırmak amacıyla yeni model
veya aynı kaynağın tekrar indirilmesi gerekmiyor. Teknik araştırma/prototip
yönü zaten seçilmiş ve teslim temeli mevcut. Bu beş öneri ayrı inceleme
ekinde tutulabilir; gerçek risk sistemine bilimsel geçiş bu sonuçla
başarılı sayılmaz. 26–29 Kasım karar incelemesinde açık koşullar takvim
dolduğu için kabul edilmeyecek. Mevcut hedef/S/U/model dosyaları, unknown
gözlem ve false negatif izni korundu; 2023–2025 bilimsel değerleri,
yeni eğitim ve nihai etiketli birleştirme açılmadı.
