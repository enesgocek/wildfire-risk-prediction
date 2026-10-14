# 400 hücre-günde gözlem kanıtı incelemesi — 14 Ekim 2026

Durum: otomatik ölçü/anahtar/zaman denetimi ve altı insan inceleme örneği
hazır. Güvenilir negatif etiketi kabul edilmedi; insan incelemesi yapılmış
sayılmadı. [İnsan değerlendirme rehberi](OBSERVATION_HUMAN_REVIEW_2026-10-14.md),
araştırmacı ve danışmanla değerlendirilmesi gereken kararları ayırır.

## Örneklem ve kanıt sınırı

Önceden seçilmiş 2018–2023 eğitim pilotunun 200 dolu tabakasındaki 400
hücre-gün aynen korundu. Tabakalar yıl × çeyrek × grid sütunundan türetilen
dört coğrafi sektör × üç tanısal sinyaldir; sektörler il değildir. Her
tabakada iki örnek bulunur. Seçim hash/sabit seed ile yapılmıştı; yeni
örneklem veya seed araması yapılmadı. Popülasyon büyüklüğü, örnekleme
olasılığı ve ağırlıkları tekrar kontrol edildi.

Aşağıdaki sayılar **bu 400 örneğin ağırlıksız tanılarıdır**. Farklı tabaka
örnekleme oranları nedeniyle bütün veri için yüzde, yanlış etiket oranı
veya yangın sıklığı olarak yorumlanmaz. 53 amaçlı olay vakasıyla birleştirilmedi.

| Tanı | Örnek hücre-gün |
|---|---:|
| Kaynak ürünü bulunan | 384 |
| Eksik kaynak; ölçüler NaN | 16 |
| Seçilmiş nominal/yüksek termal merkez bulunan | 192 |
| Ürün var, seçilmiş termal merkez yok | 192 |
| Ürün var, nominal kara merkezi yok | 11 |
| Ürün var, seçilmiş herhangi bir merkez yok | 1 |
| Gün sınırını aşan tarama içeren | 1 |
| Kara ve bulut alan payları toplamı yeniden kurulan alan payını aşan | 202 |

Son dört satır örtüşür. Termal sınıf yeni orman yangını, termal merkez
yokluğu yangınsız gün değildir. Eksik ürünün NaN ölçüleri ölçülmüş sıfıra
çevrilmedi. Bütün 400 hedef boş, gözlem durumu unknown ve negatif izin false.

## Alan ve zaman tanılarının yorumu

Ürün bulunan 384 örneğin yeniden kurulan yaklaşık alan payı sayısal
toleransla bire çok yakındır. Bu, bütün hücrenin bütün gün bulutsuz veya
kesintisiz gözlendiğini kanıtlamaz. Kara ve bulut alanları farklı geçişlerdeki
geometrik birleşimlerdir; birbirini dışlayan bir bölümleme değildir.
202 örnekte paylar toplamı yeniden kurulan alan payını aşar. Termal
merkez bulunmayan 192 örneğin 115'inde de bu durum görülür.

Yalnız örnekleyici bir alan kesimi uygulandığında, termal merkezi olmayan
192 satırdan aşağıdakiler kalır. **Bu kesimler kabul edilmiş eşik değildir**;
başarı ölçülmedi, eşik seçilmedi ve sıfır etiket üretilmedi.

| Örnek nominal kara alan payı kesimi | Koşulu sağlayan satır | Bunlarda alan birleşimleri çakışma tanısı |
|---|---:|---:|
| 0,50 | 176 | 111 |
| 0,80 | 170 | 105 |
| 0,90 | 167 | 102 |
| 0,95 | 164 | 101 |

Dolayısıyla %90 alan gibi tek bir sayı, aynı günün zamansal/bulut
yeterliliğini çözmez. Bu tanıdaki çakışma da otomatik hata veya dışlama
değildir; ölçülerin zamansal anlamının ayrı değerlendirilmesini gerektirir.

Nominal kara merkezi zaman zarfları arasındaki en uzun boşluk, ürünlü
384 örnekte 10,64–24 saat; ağırlıksız medyan 11,50 saattir. Bu zarflar
kesintisiz gözlem süresi veya gerçek yangının algılanmadan kaldığı süre
değildir. Seçilmiş kara merkezi olmayan satırda kayıtlı 24 saatlik boşluk,
fiziksel piksel ayak izlerinin hiç kesişmediğini kanıtlamaz. Alan ve merkez
ölçüleri farklıdır; tek bir birleşik güven puanı üretilmedi.

## Gece yarısı kaynak tanığı

Pilotun `E6933_5K_V1_C522_R918`, 18 Ocak 2022 kaydı bir boundary_unknown
tarama içeriyor. Kabul edilmiş Ocak payload'ı ve günlük scan_grid.csv
hash'iyle geri okundu. Hücreye ait bütün taramaların açık sol/kapalı sağ
pencere sınıfları kaynak kaydıyla eşleşti.

SNPP, `2022018.2354`, tarama 202:

- Başlangıç: `2022-01-18T23:59:59.481722951+00:00`.
- Bitiş: `2022-01-19T00:00:00.045531034+00:00`.
- Bu hücre/tarama satırında bir nominal güvenli termal merkez bulunuyor.

Tam piksel edinim zamanı bu zarfla çözülmedi. Tespiti otomatik olarak
18 veya 19 Ocak hedefine atamadık. Bu bir sınır örneğinin geri okumasıdır;
öteki günlerin komşu nominal granüllerindeki bütün sınır etkilerini
çözmüş sayılmaz. Bütün örneklerde `boundary_timing_unresolved` korunur.

## İnsan incelemesine ayrılan örnekler

A–F örnekleri 400 satırdan açıklayıcı uç durumlar olarak seçildi; yeni
temsili örneklem değildir. Seçilen altı birim birbirinden farklıdır.
Kaynak formlarının reviewer/kanıt/karar alanları boş ve not_reviewed kaldı.
Görsellerin üretilmesi insan veya bağımsız uzman kabulü değildir.

Özellikle F örneği, 5 km gridin AOI içinde yalnız **88,57 m²** kalan bir
parçasıdır; mevcut örtü bağlamında su oranı 1, orman/çalı oranları sıfırdır.
Geometri/merkez ayrımını ve habitat kapsamı gereksinimini görünür kılar.
Bu örtü bilgisi tarihsel uydu görüntüsüyle bağımsız doğrulanmış sayılmaz.
Habitat kararı bu işlemde değiştirilmedi. Sorumlular, sorular ve hangi
kanıtların eksik olduğu [ayrı kısa rehberde](OBSERVATION_HUMAN_REVIEW_2026-10-14.md).

## Denetim ve çıktı

Komut: `.venv/Scripts/python.exe scripts/quality/review_observation_pilot.py`.
68 ilgili test ve üç kod dosyasında lint/format geçti; son test koşusunda
kullanımdan kalkma uyarıları hata olarak ele alındı. Testler eksik/sıfır,
tabaka ağırlığı, zaman/pencere/sinyal uyumu, birbirinden farklı örnek seçimi,
gece yarısı uçları ve kapalı etiket koşullarını kapsar.

Final dizini:
`outputs/reports/dataset/observation_review_v1/20261014T174956Z_cca3d882/`.
Önceki `174800` dizini geliştirme çıktısıdır; finalin yerine kullanılmaz.

- Beş CSV: 400 satırlık denetim, altı örnek, kaynak tarama satırları,
  tabaka tanıları ve yalnız örnekleyici alan kesimi karşılaştırması.
- İki görsel: `human_observation_examples.png`, `midnight_boundary_example.png`;
  ikisi görsel olarak kontrol edildi. İlk görselde mavi nominal kara,
  gri bulut alan birleşimi; turuncu seçilmiş merkez zarfları arasındaki boşluk.
- `readback.json` SHA-256:
  `32f75f98feeef857e979fa50340c3b1a01053617f97aa72db6be53bf4a297c44`.
- `completion_readback.json` SHA-256:
  `5a3ae72ac2f5f7a298ebc6a072d3f641328779b2e73abcbd225deb84530ee865`.

Yedi çıktı ve 34 giriş kapanışta kontrol edildi; önceki altı inceleme
çıktısı ve 22 donmuş bulut girdisi aynı hash'te. 453 insan formu boş kaldı.
Yeni ham veri indirme, geometri/uydu yeniden üretimi, bulut işi, model
eğitimi ve 2024/2025 erişimi yok. Gözlem tanıları model girdisi yapılmadı.
Güvenilir negatif için bağımsız olay incelemesi, tam hedef pencere
hizalaması ve gerekçeli gözlem/habitat politikası hâlâ gereklidir.
