# C adayının önceki tespit ve gözlem kontrolü — 8 Kasım 2026

Antalya'daki C adayı için `C609_R887` hücresinde kayıtlı ilk
tespit 15 Ağustos 2021 10.24 UTC'dir. Tahmin zamanı aynı gün
00.00 UTC. Bu inceleme, C'nin daha eski bir katalog bileşenine
bağlanıp bağlanmadığını ve yerel uydu taraması kayıtlarının önceki
günler için neyi desteklediğini ayrı değerlendirdi.

## Olay kataloğu

Dokuz kayıtlı gruplamanın her birinde C aynı tek S-NPP tespitinden
oluşuyor. Üye kimliğinin hash'i, en erken zaman ve ilk hücre,
üyelik dosyasından yeniden hesaplanıp katalogla eşleştirildi.
Son kayıt zamanı ilk kayıtla aynı. Dolayısıyla bu bileşende
önceki veya sonraki ek bir üye bulunmuyor.

12 Ağustos 10.24 UTC dahil ve 15 Ağustos 10.24 UTC hariç
72 saatlik penceredeki 53 eğitim kataloğu satırı WGS84 merkez
mesafesiyle tarandı. C noktasına 500 m, 1 km veya 2 km içinde
önceki satır bulunmadı. Aynı hücredeki önceki satır sayısı da
sıfır. En yakın kayıt 13 Ağustos 11.02 UTC'de yaklaşık 20,26 km
uzakta. Bu sonuç dört illik, seçilmiş Type 0 ve nominal/yüksek
güvenli katalog kapsamındadır. Katalog dışında veya algılanmamış
olayları kapsamaz.

## Aynı hücrenin kayıtlı uydu taramaları

11–16 Ağustos'un altı nominal paketi, mevcut Ağustos arşivi ve
kabul edilmiş kaynak manifesti üzerinden yerelde okundu.
Dört hedef günün her biri için önceki, aynı ve sonraki nominal
gün paketleri mevcuttu. Aşağıdaki pencereler UTC gün başlangıcına
bağlıdır. 72 saatlik nokta taraması ise C'nin tespit saatine bağlıdır.

| Hedef gün | Kesin pencere içi tarama satırı | Termal merkez sayısı | En uzun nominal kara merkezi zarf boşluğu |
|---|---:|---:|---:|
| 12 Ağustos 2021 | 14 | 0 | 11,50 saat |
| 13 Ağustos 2021 | 9 | 0 | 11,50 saat |
| 14 Ağustos 2021 | 11 | 0 | 11,50 saat |
| 15 Ağustos 2021 | 11 | 1 | 11,50 saat |

Dört günde de zaman sınırını kesen yüklü tarama satırı sıfır.
Tarama satırı bağımsız uydu geçişiyle aynı birim değildir.
Zarf boşluğu hücre içinde nominal kara merkezi kaydı olan tarama
zarflarından hesaplandı. Tespit noktasının her pikselde veya gün
boyunca gözlenip gözlenmediğini belirlemez. 15 Ağustos'taki termal
merkez sayımı bağımsız olay kanıtı olarak kullanılmaz.

## Araştırma sonucu

C'nin önceki bir **kayıtlı bileşenin** devamı olduğuna dair işaret
bulunmadı. C, ilk tespit zamanı ve önceki yakın kayıtların yokluğu
nedeniyle olay incelemesinde öncelikli kalır. Önceki günlerdeki
yaklaşık 11,5 saatlik zarf boşlukları ve tarihsel örtü sınırı
nedeniyle olayın gerçekten yeni olduğu ve yerel doğal örtü kabulü
hâlâ açık. Bu tek vakadan eğitim kümesi veya tespit başarısı oranı
çıkarılmaz. Hedef boş ve gözlem durumu `unknown`.

## Kontrol ve tekrar üretim

Üretici `scripts/quality/review_pu_candidate_timeline.py`.
Çıktı `outputs/reports/dataset/pu_candidate_timeline_v1/20261107T224018Z_21d83b2a/readback.json`.
SHA-256 `dc2489f28a0e4fcf3ce31fe8e9db3a570ddf792fe85562e4266a751d974b2b20`.
28 doğrudan dosya kimliği ve altı günlük iç rapor/tarama hash'i
doğrulandı. İkinci okuma 53 satır, 2 km'yi kapsayan muhafazakâr
koordinat kutusunda sıfır kayıt, dokuz tek üyeli bileşen, dört
pencere ve kapalı etiket alanlarını doğruladı. Ruff ve JSON geri
okuması geçti.

İlk çağrıda birleşik CSV'deki 2024 satırları eğitim korumasını
tetikledi. Düzeltilen çağrı 2.960 satırı tarih alanında atladı ve
30.295 eğitim satırını analiz etti. 2024 satırları bilimsel
hesaba girmedi. 2025 erişimi, dış veri edinimi, eğitim veya nihai
birleşme yapılmadı.
