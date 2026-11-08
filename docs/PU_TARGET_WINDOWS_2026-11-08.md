# 24 saatlik hedef için zaman ve olay kanıtı — 8 Kasım 2026

Amaç, kesin UTC pencere denetiminin hangi eksikleri kapattığını ve
mevcut olay kayıtlarının hangi araştırma sorularını desteklediğini
ayırmaktır. 2018–2023 için daha önce seçilen 96 ana ve 31 karşılaştırma
satırı kullanıldı. Beş olay vakasının mevcut kaynak saatleri ve olay
günündeki gözlem makbuzları ayrı olarak karşılaştırıldı.
[Örneklem](PU_CALENDAR_SAMPLE_2026-11-08.md) · [Olay bağlamı](STRATIFIED_EVENT_CANDIDATES_2026-11-08.md).

## Yöntem

Bir hücre-günün tahmin zamanı UTC 00.00, hedef aralığı `(T,T+24h]`.
Önceki, aynı ve sonraki nominal uydu dosyasının yalnız eğitim dönemi
içindeki kullanılabilir olanları okundu. Dosya ve iç tarama tablosu
kimlikleri kabul makbuzuyla doğrulandı. Taramalar, zaman zarflarına
göre tamamen içeride, tamamen dışarıda veya sınırı kesiyor olarak
ayrıldı. Bu sınıflar zaman damgalarından ikinci bir yöntemle de
hesaplandı. Nominal günün kara merkezi sayısı önceki örneklemle
uzlaştırıldı. Sonuçlar seçilen 127 pencereye aittir.

Beş olay adayının ilk uydu zamanı aynı sağ-kapalı kuralla günlere
atandı. Dört vaka için kayıtlı altı yaklaşık kaynak saati Türkiye
saatinden UTC'ye çevrildi. Ekip çıkışı, yaklaşık başlangıç ve ilk
uydu tespiti ayrı saklandı. Kaynak saati ile tespit aynı güne düşse
bile konum, başlangıç örtüsü ve olay kimliği ayrıca kanıt gerektirir.

## Sonuçlar

341 farklı nominal gün paketi okundu. Ana örneklemin 96 satırında üç
paket de mevcuttu. Karşılaştırma tablosundaki 31 satırın sekizinde
2018-06-13 veya 2023-12-31 ürün boşluğu nedeniyle kaynak dizisi
eksikti. Bu sekiz satırda okunan komşu taramalardaki sayım sıfırdı.
Eksik ürün nedeniyle pencerenin tamamı hakkında çıkarım yapılmadı.
2023-12-31'in planındaki 2024-01-01 paketi eğitim kapsamı dışındaydı.

**19 Şubat 2019, İzmir.** Nominal dosyada 922 seçili kara merkezi vardı.
99 merkezin ait olduğu tek tarama UTC gün sınırını kesiyordu. Böylece
kesin içeride sayılan merkez sayısı 823 oldu. 119 ürünlü pencerenin
yalnız birinde nominal kara merkezi sayısı değişti. Ürünlü 119 satırın
hiçbirinde 12 saat ve sıfır merkez tanı kategorileri değişmedi.
127 satırın hiçbirinde içeride ya da sınırda yüklü nominal/yüksek
güvenli termal merkez bulunmadı. Bu, örneklemde gerçek yangın
bulunmadığını göstermez. Örnek seçilirken tespit kayıtları kullanılmadı.

Beş olay adayının beşinde ilk uydu tespiti ve önceki gözlem
makbuzundaki tahmin günü uyumlu. Dört aday için kayıtlı altı kaynak
saati de aynı UTC hedef penceresine düşüyor. Örneğin Kemalpaşa'da
yaklaşık başlangıç 11.06 UTC, ekip çıkışı 11.17 UTC, uydu tespiti
11.22 UTC. Bunlar aynı gün için zaman bağlamı sağlıyor. Beş adayda
bağımsız doğrulanmış başlangıç konumu sayısı sıfır.

## Kabul sınırı ve yöntem kararı

| İş | Sonuç |
| --- | --- |
| Takvim, ilk tespit ve tarama zamanı | UTC pencere kuralı denetlenebilir. Paket boşlukları ve sınır taramaları ayrı işaretlenebilir. |
| Yeni fiziksel orman/çalılık olayına bağlama | Eldeki ayrıntılı beş vakada başlangıç konumu bağımsız olarak doğrulanmadı. Güçlü iki bağlantı olay bağlamı olarak saklanır. |
| PU modeli ve gerçek risk değerlendirmesi | Bağımsız seçilen inceleme örneklemi var. Güvenilir pozitif küme, gerçek olay oranı ve tespit mekanizması için yeterli dayanak henüz yok. Gerçek olay AP veya kalibrasyonu bu kanıttan hesaplanamaz. |

**Ana hedefi koruma.** Bağımsız olay ve değerlendirme kanıtı elde
edilene kadar mevcut paket denetlenmiş veri ve yöntem çıktısı olarak
sunulabilir. Nihai etiketli birleştirme için hedef kabulü bekler.

**Ayrı deney.** Arşivdeki belirli kurallarla gruplanmış ilk VIIRS
tespitinin ertesi 24 saatte kayda girip girmediğini araştıran ayrı
bir deney seçilebilir. Buradaki sıfır yalnız tanımlı katalog kaydının
yokluğu anlamına gelir. Bu deney, etiket ve kapsam protokolü, 2024 için
ayrı hazırlık ve araştırmacının açık seçimini gerektirir. Ana araştırma
verisiyle birleştirilmez. 2025 kapalı kalır.

Yerel üretici `python scripts/quality/audit_pu_target_windows.py`.
Son çalıştırma `20261108T013906Z_90d21c5b`, makbuz SHA-256
`854d47a259fa18157838ed1804e666dab9a5358c940d87f9ca4e6cde7101a26e`.
İlk çalıştırmadaki zaman birimi ve boş değer uyarıları giderildi.
İki çalıştırmanın pencere tabloları bayt düzeyinde, bilimsel makbuz
alanları içerik düzeyinde eşleşti. İlgili 61 test geçti.
