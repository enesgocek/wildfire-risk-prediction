# Sabit 400 örnekli pilotta hedef pencere kontrolü — 14 Ekim 2026

## Sonuç ve kapsam

Önceki 11 amaçlı pencere kontrolü, yeniden örnekleme yapılmadan **400
hücre-günlük sabit pilotun tamamına** uygulandı. 200 tabaka, örnek kimlikleri,
N/n ağırlıkları, nominal gün gözlem sütunları ve boş hedefler korundu.
348 farklı hedef gününün komşuları için 885 farklı nominal gün planlandı;
kayıtlı iki kaynak boşluğu okunmadı. 72 eğitim ayındaki **883 farklı
günlük paket** yerelden kontrol edildi. Bu 883 gün, bütün 2.191 eğitim
gününün pencere kabulü anlamına gelmez.

| Ölçü | 400 örnekte ham sayı |
|---|---|
| Önceki nominal ürün sinyali | 192 termal merkezli / 192 seçilmiş termal merkezsiz / 16 ürün eksik |
| Üç komşu nominal paketi mevcut örnek | 384 |
| Eksik paket kümesi bulunan örnek | 16 |
| Pencere sınırını kesen okunmuş tarama bulunan örnek | 2 |
| Sınırdaki taramada nominal/yüksek güvenli termal merkez bulunan örnek | 1 |
| Kesin pencere içindeki taramalarda seçilmiş termal merkez bulunan örnek | 191 |
| Kapsam dışı su hücresi; denetimde korunan | 1 |
| Önceki amaçlı pencerelerle ortak sonuçların birebir tekrar üretimi | 6/6 |

Termal merkez sayımı fiziksel yangın veya kabul edilmiş olay sayısı
değildir. Bu ham örnek sayıları popülasyon oranı veya etiket hata oranı
olarak yorumlanmaz. Gözlem desteği ve olay kimliği ayrı kabul koşullarıdır.

## Komşu gün okumasının ortaya çıkardığı fark

22 Ocak 2020 hedefli `E6933_5K_V1_C555_R877` örneğinde, **21 Ocak
paketinde** bulunan `N20:2020021.2354`, tarama 201 hedefin sol sınırını kesiyor:

- Başlangıç: `2020-01-21T23:59:59.736242056+00:00`.
- Bitiş: `2020-01-22T00:00:00.300039053+00:00`.
- 130 piksel merkezi / 130 nominal kara merkezi; seçilmiş termal merkez yok.

Bu örnekte yalnız hedef nominal gününü okumak sınır taramasını göstermiyordu.
Yeni kontrol taramayı önceki günlük paketten buldu ve `boundary_unknown`
olarak korudu. Kara merkezlerinin kesin gününü orta zamanla tahmin etmedi.
Bu hücrenin hedef pencere içinde ayrıca bir termal merkezi var; sınır
taraması bu termal merkezin kendisi değildir.

18 Ocak 2022 hedefli `E6933_5K_V1_C522_R918` örneğinin bilinen
`SNPP:2022018.2354`, tarama 202 kaydı sağ sınırı kesiyor. Başlangıç
`2022-01-18T23:59:59.481722951+00:00`, bitiş
`2022-01-19T00:00:00.045531034+00:00`. Bir nominal güvenli termal
merkezin kesin günü çözülmedi; içerideki kesin termal merkez sayısı sıfırdır.
Önceki 11 amaçlı incelemede aynı merkezin ertesi gün için de belirsiz
görünmesi iki ayrı yangın sayılmamıştı; sabit pilotta yalnız 18 Ocak örneği var.

384 ürünlü örnekte **kesin içeride + sınırda belirsiz** termal merkez
toplamı eski nominal sayımdan farklı değil. Buna karşılık **yalnız kesin
içerideki** termal merkez sayımı bir örnekte farklıdır: yukarıdaki SNPP
örneği. Toplamların eşitliği kesin pencere hizalaması anlamına gelmez.
Okunmuş kaynaklarda başka nominal günden bütünüyle içerideye taşınan
tarama bu pilotta bulunmadı. Eski/yeni içerideki merkez zarfı birleşimi ve
en uzun boşluk ölçüleri, ürünlü 384 örnekte birebir aynı kaldı.

## Eksik kaynak, kapsam ve ağırlıklar

Paket kümesi eksik 16 örneğin sekizi 13 Haziran 2018, sekizi 31 Aralık
2023 günündedir. 31 Aralık örneklerinde 2024-01-01 komşusu eğitim dışı
olduğu için plan kaydı olarak görünür; dosyası okunmadı. 1.200 örnek/gün
rolünün 1.176'sı okunabilir, 16'sı ertelenmiş kaynak, sekizi eğitim dışıdır.
Bunlar farklı gün sayıları değildir; aynı gün birden fazla örneğe kaynak olur.

Eksik nominal ürünün önceki sayısal tanıları NaN kaldı. Komşu dosyalardan
okunmuş sıfır sayımı, eksik günün ölçülmüş sıfırı veya yangınsız gün
olarak kullanılmaz. Su kapsamı kararı yeniden seçilmedi: küçük su hücresi
denetimde korunur, modelleme kapsamı dışında işaretlidir. 400 örnek 399'a
yeniden örneklenmedi ve kalan örneklerin ağırlıkları yeniden normalize edilmedi.

`stratum_impacts.csv`, her tabakanın N ve n değerlerini, ham örnek
sayılarını ve `sum(weight × flag)` genişletilmiş sayı **tahminlerini**
kaydeder. Bunlar tam sayım değildir; güven aralığı verilmedi. Özellikle
bir veya iki sınır vakasını bütün takvimin kesin sıklığına çevirmek uygun
değildir. Genişletmeler özgün 6.351.709 hücre-günlük evrene aittir;
su kuralı sonrasındaki modelleme kapsamının oranları değildir.
Kaynak eksikliği tabakasındaki örnekler bilinen iki boşluğa ait
olduğundan genişletilmiş eksik paket tahmini 5.798 hücre-gündür; önceki
tam takvim ürün eksikliği sayımıyla uyumludur. Diğer belirsizliklerin
tam takvim sayısı bu pilotla ölçülmüş sayılmaz.

## Veri okuyucusu, kontroller ve izlenebilirlik

`observation_window_source.py`, aylık kabul raporunu ve payload hash'ini
doğrular, arşivi bir kez belleğe alır ve yalnız istenen gün/grid taramalarını
tutar. Normal aylık, eksik ayın günlük ve Temmuz 2023 ayrı referans
paketleme biçimleri ayrı testlerle kontrol edildi. Günlük rapor ve
scan_grid kimliği, coğrafya/kod bağı ve kapalı etiket koşulları denetlenir.
Eğitim dışı tarih, dosya açılmadan reddedilir. En fazla dört yerel işçi,
gün/iş geçişlerinde kontrol edilen iki saatlik süre ve başlangıçta 10 GiB
disk rezervi vardır; ağ her işçide engellidir.

`observation_window_pilot.py`, donmuş `observation_window.py` zaman
sözleşmesini değiştirmeden sonuçları grid/UTC zaman anahtarıyla bağlar.
`Z` ve `+00:00` gösterimleri aynı zaman anahtarına eşleşir, özgün sütunlar
birebir korunur. Yeni tanılar `window_` ad alanındadır; tahmin anında bilinen
özellik gibi modele verilmez. Çelişen tekrar ve anahtar, değişmiş kaynak,
etiket/gözlem izni veya örnekleme ağırlığı reddedilir.

**79 ilgili test** geçti; dört yeni Python dosyası lint/format kontrolünden
geçti. Gerçek işlem dört yerel işçiyle 146,156 saniye sürdü. Bu yalnız bu
makinedeki kompakt dosya okuma/denetimidir; ham uydu hesaplama veya VM
hızlanması ölçümü değildir. Önceki altı ortak amaçlı sonuç birebir üretildi.
210 giriş ve beş CSV kapanışta kontrol edildi; 22 donmuş bulut girdisi,
eski kaynak/pilot çıktıları ve 453 boş insan formu aynı kaldı.

Komut:

```powershell
.venv\Scripts\python.exe scripts/quality/review_window_pilot.py --workers 4 --hours-limit 2
```

Sonuç dizini:
`outputs/reports/dataset/window_pilot_v1/20261014T191547Z_b008fcf9/`.
Çıktılar: `pilot_window_audit.csv`, `window_scan_rows.csv`,
`source_day_schedule.csv`, `stratum_impacts.csv`, `boundary_source_review.csv`.
12.146 pencere/tarama satırı vardır; aynı kaynak taraması farklı hedef
pencerelerinde yer alabileceğinden bağımsız geçiş veya yangın sayısı değildir.
`readback.json` SHA-256:
`f79fcb11ede0b7d0c24cf3a976146eae6df871791e9abddf179b4fa96a9e195f`.
Kapanış SHA-256:
`d5fd9e414ddf8f881df79c5be1e9fdd757af1bdd03f53d3be429d4b9dcfef98f`.

## Sonraki bilimsel karar

Bu adımla sabit pilotun **komşu paket ve tarama zarfı denetimi** tamamlandı.
Tam piksel zamanı, hedef penceresine kırpılmış alan birleşimi, bağımsız
olay kanıtı ve gözlem yeterliliği henüz kabul edilmedi. Üç paketin mevcut
olması tek başına yeterli gözlem değildir. `daily_observation_status=unknown`,
pozitif/negatif izinleri `false`, hedefler boş ve `model_ready=false` kalır.

Bu pilotta su kapsamını geçen, üç paketi mevcut, sınır taraması ve kesin
içeride seçilmiş termal merkezi bulunmayan 191 örnek var. Bunların 10'unda
kesin içeride nominal kara merkezi de yok; 181'inde en az bir nominal
kara merkezi var. Bu, sonraki gözlem protokolü tartışmasının ölçülen
başlangıç kümesidir; 181 örneğin negatif etikete kabul edildiği anlamına gelmez.

Önerilen devam, olay/ilk hücre ve gözlem yeterliliği için ölçülebilir
protokol seçeneklerini bu sonuçlar üzerinden hazırlamaktır. Sınır ve
eksik kaynak kayıtları şimdilik belirsiz tutulmalıdır. Yalnız sayımın sıfır
olması negatif etiket için yeterli kabul edilmeyecek; yeni yöntem tercihi
gerektiğinde gerekçeli alternatifler araştırmacıya sunulacaktır. 2024/2025
verisi açılmadı, yeni bulut işi veya model eğitimi yapılmadı.
