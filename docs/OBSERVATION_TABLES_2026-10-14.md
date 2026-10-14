# Uydu gözlem denetim tabloları — 14 Ekim 2026

## Amaç ve kanıt sınırı

**Sonuç:** 72 ay/2.191 gün/6.351.709 hücre-gün gözlem tablosu
tamamlandı. 6.345.911 hücre-gün mevcut ürüne, 5.798 hücre-gün iki
eksik kaynak gününe bağlıdır. Bunlar etiketli eğitim örneklemi sayıları
değildir; son bağımsız dosya/kapsam kontrolü 14 Ekim 18:00 Türkiye'de geçti.

Tamamlanan 72 aylık aday özellik takvimine, yangın etiketinin denetiminde
kullanılacak uydu gözlem ölçülerini aynı hücre/tarih anahtarlarıyla ayrı
sunmak. Bu çalışma etiket üretimi değil, kabul edilmiş kompakt ürünlerin
yeni tablolara aktarılmasıdır. Yeni ham kaynak çekimi, bulut işi veya
geometri birleşimi hesabı yapılmaz. `unknown` ve negatif izin `false`
korunur; hedef pencereye ait bu ölçüler tahmin anında bilinen girdiler
gibi modele verilmez.

## Kaynak ve aktarım yöntemi

Üretimin 71 ay/2.158 günlük native finali ve 199 kompakt teslimin kayıtlı
SHA kimlikleri kontrol edilir. Her kullanılan aylık/günlük payload, canlı
Drive yerine yerel dosyadan okunur; teslimin hash'i ve completion boyut/
worker/scope/policy koşullarıyla eşleşir. Temmuz 2023'ün ayrı 31 günlük
referans ZIP'i kendi sabit hash'iyle alınır. Böylece iki farklı kabul
geçmişi birbirine karıştırılmaz.

Her günün `area.csv` ve `centers.csv` dosyaları, günlük raporundaki
SHA'larla kontrol edilir. Gün, bilimsel kompakt kod, coğrafya ve kapalı
etiket politikası eşleşir. Önceki tam native denetimi yeniden çalıştırma
iddiası yoktur; yeni aşamada seçilmiş tablo sayısal sınırları ve anahtarlar
tekrar denetlenir. Alan oranları kırpılmaz; yaklaşık paydalar ve küçük
sayısal toleranslar korunur. Piksel merkezleri tekrar geçişleri içerebilir;
termal merkez sayısı bağımsız yangın veya FIRMS Type sınıfı değildir.

`observation_table.py` aşağıdakileri ayrı `obs_` alanlarına taşır:

- Yeniden kurulan yaklaşık alan, nominal yangın dışı kara ve bulut alanı/payları.
- Seçilmiş merkez, nominal/yüksek güvenli termal sınıf ve tarama sayımları.
- Gün/gece tarama sayıları ve merkez zaman zarflarının birleşim/boşluk ölçüleri.
- Ürün varlığı, kaynak eksikliği, nominal granül günü ve çözülmemiş hedef
  pencere sınırı bilgisi.

Zaman zarfı sürekli gözlem süresi değildir. Nominal güne göre alan
birleşimi tam `(T,T+24h]` kapsamını kanıtlamaz; sınır taramaları çözülmeden
`observed` veya güvenilir negatif statüsü atanmaz. Alan ve merkez ölçüleri
birbirinin yerine kullanılmaz; oranlar yangın olasılığı değildir.

## Takvim ve eksik kaynaklar

2018–2023'ün 2.191 günü ve 2.899 hücresi korunur. 13 Haziran 2018 ve
31 Aralık 2023 için `obs_product_present=false`, `deferred_source_day`
ve boş sayısal/zamansal alanlar yazılır. İki gün × 2.899 = **5.798
eksik ürün hücre-günü**, sıfır gözlem veya yangınsız etiket değildir.
Gerçek ürünün sıfır sayımı ise ölçülmüş sıfır olarak korunur. Önceki
[dört hedef tarihi incelemesi](DATASET_QUALITY_REVIEW_2026-10-14.md)
bu aktarımda otomatik dışlama politikasına dönüşmez.

Özelliklerin kabul edilmiş tam takvim raporuna ve aynı grid dosyasına
hash ile bağlanılır. Tablo anahtarları satır sırasına göre değil hücre
kimliğiyle hizalanır; eksik/tekrarlı hücre reddedilir. 2024/2025 ayları
kaynak okumasından önce reddedilir. Gözlem tabloları özellik veya hedef
tablosu üzerine yazılmaz; aylık `observations.csv.gz` ve readback'ler
ayrı yeni sonuç dizininde korunur.

## Çalışma kontrolleri ve kullanım

`scripts/quality/materialize_observations.py`, ağ engeli, en fazla dört
yerel işçi, iki saat varsayılan süre ve 10 GiB disk rezerviyle çalışır.
Tek yazıcı kilidi var. `PAUSE` gün başında okunur; çocuk hatasında diğer
işler için duruş işareti üretilip bekleyen görevler iptal edilir. Kapanmış
ayların dosyaları korunur; var olan kabul çıktıları değiştirilmez.

```powershell
.\.venv\Scripts\python.exe scripts/quality/materialize_observations.py `
  --workers 4 --hours-limit 2
```

`--months 2018-01 2018-06 2023-07 2023-12` yalnız dar denemedir; tam
takvim kabulü diye sunulmaz. Son tam seçim başarı raporu
`accepted_readback.json`, canlı/son durum `progress.json` içindedir.
Her aylık tablo sıkıştırılmış CSV'den geri okunup anahtar/değer/NaN
örüntüsü ve özet sayımlarıyla karşılaştırılır. Yeni çalışma çıktıları
`outputs/reports/dataset/observation_materialization_v1/` altındadır.

## Bilimsel sonraki adım

Bu tablolar, geçiş/gece-gündüz/bulut ve kaynak boşluklarını bir arada
incelemeyi mümkün kılar. Güvenilir negatifler için fiziksel yorum,
sensör ve sınır zamanı belirsizlikleri ile gözlem yeterliliği protokolü
ayrıca gerekçelendirilmelidir. Kaynak Type teyidi, yeni olay/ilk hücre,
habitat ve dönem sınırı kararları açık kalır. Tek bir alan eşiğiyle
bu kararlar otomatik kabul edilmez. Yeni olay senaryosu seçilmedi,
ikili hedef atanmadı, model eğitilmedi; 2025 final testi kapalıdır.

## Gerçek çalışma, sonuç ve geri okuma

Önce dört biçim/sınır durumu (Ocak/Haziran 2018, Temmuz/Aralık 2023)
üzerinde gerçek dar deneme geçti. İlk sürücü ve yardımcı kaynaklarının
pilot kimlikleri ayrı çıktılarla korunur. Son sürüm, kaynak feature-grid
bağını ve genel takvim sayımını ayrıca kontrol ederek tam dönemde çalıştı.
Bu kontroller donmuş GCP bilimsel koduna veya mevcut aday özelliklere
değişiklik değildir.

Tam aktarım dört yerel süreçte **158,67 saniye** sürdü; bu mevcut
yerel ZIP'lerden seçilmiş alanları okuma/yazma süresidir, ham uydu işi
veya karşılaştırmalı model hız kazanımı değildir. 72 sıkıştırılmış
tablonun toplam boyutu **477.448.199 bayt** (477,45 MB, ondalık).
Her ayın bütün çıktısı geri okunarak sütun/anahtar/değer/NaN eşitliği
ve özet sayımları kontrol edildi.

| Ölçü | Hücre-gün |
|---|---:|
| Tam aday takvim | 6.351.709 |
| Ürün bulunan | 6.345.911 |
| Eksik kaynak günlerine ait | 5.798 |
| En az bir bulut sınıfı merkezi olan | 4.052.772 |
| En az bir seçilmiş nominal kara merkezi olan | 6.088.289 |
| En az bir nominal/yüksek termal merkezi olan | 17.922 |

Son üç satır ürün tanısının varlık sayımlarıdır; birbirini dışlayan
sınıflar değildir ve yangın/yangınsız etiket sayısı olarak kullanılamaz.
Bulut merkezi varlığı tüm hücrenin kapalı olduğunu; kara merkezi
varlığı tam gün gözlem yeterliliğini kanıtlamaz. Termal satırı neden,
olay, tutuşma veya bitki yangını doğruluğu değildir.

52 ilgili test ve lint/format geçti. Testler anahtar hizası, gerçek
sıfır/eksik ayrımı, kaynak hash/policy değişimi, sayısal sınır ve kapalı
dönemin kaynak okumadan reddini kapsar. Bu testler bilimsel gözlem
politikasının veya saha doğruluğunun kabulü değildir.

Kapanış denetimi 72 tablonun hash'ini ve aylık raporların final ile
eşitliğini kontrol etti. İki eksik güne ait 5.798 satır ayrı okunup bütün
ölçülerin boş kaldığı doğrulandı. 11 yöntem/kaynak pini ve 22 donmuş bulut
girdisi aynı kimlikte; yazıcı kilidi kalktı. Bu son kontrolde bütün CSV'ler
ikinci kez yeniden hesaplanmadı; seçilmiş iki aylık eksik günler okundu.

Kanıt kökü `outputs/reports/dataset/observation_materialization_v1/`:

- Pilot: `20261014T145446Z_c455b417/accepted_readback.json`.
- Tam dönem: `20261014T145638Z_c0881064/accepted_readback.json`;
  SHA-256 `fb5fa5ce8c83be2c4e21b130bb06935a5e2d8014e45460c1f61660b73262cb14`.
- Aynı tam dönem dizininde `completion_readback.json`;
  SHA-256 `4f3575224119340ca75b851a01d6527ec4359d229a3ec43f75478dd81fd5d506`.

Sıradaki işlem, bu tanıları mevcut olay/zor vaka incelemesiyle eşleştirip
gözlem yeterliliği ve kaynak farklarının etkisini değerlendirmektir.
Nihai olay/habitat/negatif politikası onaylanmış gösterilmez.

## İzleyen hazırlık

14 Ekim'de bu tablolarla [etiket kanıtı inceleme paketi](LABEL_EVIDENCE_REVIEW_2026-10-14.md)
hazırlandı: 53 amaçlı olay-senaryo vakasının bütün ilk hücreleri bağlandı;
ayrı 400 hücre-günlük tabakalı pilot seçildi. Bu, insan incelemesi veya
gözlem yeterliliği kabulü değildir; önceki tablo sonuçları değişmedi.
