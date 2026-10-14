# Etiket kanıtı inceleme paketi — 14 Ekim 2026

## Amaç ve kapsam

Otomatik etiketlemenin hata riski, kuralların çalışmasıyla ortadan kalkmaz.
Bu aşamanın amacı, henüz etiket atamadan aday olayları uydu gözlem tanılarıyla
ilişkilendirmek ve insan incelemesi için tekrarlanabilir bir pilot hazırlamaktır.
Eğitim dönemi 2018–2023'tür; bu işlem 2024 veya kapalı 2025 verisini açmaz.
İş yerelde ve ağ bağlantıları engellenerek yürütülür; yeni bulut işi yoktur.

Kaynaklar, [kabul edilmiş gözlem tabloları](OBSERVATION_TABLES_2026-10-14.md)
ve [10 Ekim karar inceleme paketi](DECISION_REVIEW_2026-10-10.md) ile sınırlıdır.
Eski CSV/ZIP/JSON sonuçları değiştirilmez. Önceki paket üyelerindeki boşlukla
ayrılmış açık UTC zaman gösterimi yalnız bellekte ISO `T` biçimine çevrilir;
genel zaman sözleşmesi gevşetilmez.

## İki farklı inceleme amacı

**Amaçlı olay vakaları:** Önceden seçilmiş 53 olay-senaryo vakası korunur.
Bu vakalar 28 farklı üyelik örüntüsü içerir; senaryolar aynı tespitleri
tekrarlayabilir. 53 bağımsız yangın veya temsili hata örneklemi değildir.
Her vakanın en erken zamanındaki bütün hücreler, korunan tespit üyeleriyle
yeniden eşleştirilir; yalnız kanonik ilk hücreye indirgenmez.

Her ilk hücre için iki gözlem bağlantısı vardır:

- İlk uydu tespitinin nominal UTC takvim günü.
- Sağdan dahil `(T,T+24h]` kuralına göre aday tahmin başlangıcı T'nin günü.

Gece yarısı tespiti bir önceki T'ye aittir. Takvim dışına taşan bir bağlantı
varsa bulunamadığı açıkça kaydedilir; komşu güne doldurulmaz. Aynı güne düşen
iki rol de saklanır. Bu bağlantılar nominal günlük tanılardır; fiziksel
gözlem kapsamının tam hedef penceresine uyduğu kanıtlanmış değildir.

**Tabakalı hücre-gün pilotu:** Örnekleme çerçevesi 72 ay/2.191 gün/2.899
hücreden oluşan 6.351.709 hücre-gündür. Henüz pozitif veya negatif sınıf
olmadığı için örnekler bu adlarla seçilmez. Tabakalar yıl × takvim çeyreği ×
coğrafi sektör × gözlem sinyali olarak kurulur.

Coğrafi sektörler, EPSG:6933 grid sütununun en küçük/en büyük değerleri
arasındaki tamsayı aralığın dört eşit genişlikli bölümüdür; batıdan doğuya
numaralanır. Hücrelerde ayrı il ataması bulunmadığından bunlar **il sınırı
veya il başına örnekleme değildir**. Alanı büyük/küçük hücre parçalarının
seçilme hakkı hücre-gün birimine göredir; alanla ağırlıklı örnekleme yapılmaz.

Sinyal grupları birbirini dışlar:

1. Kaynak ürün yok.
2. Ürün var ve en az bir nominal/yüksek güven termal sınıf merkezi var.
3. Ürün var, seçilmiş bu termal merkezlerden yok.

İkinci grup doğrulanmış bitki yangını; üçüncü grup yangınsız veya yeterli
gözlenmiş hücre anlamına gelmez. Bulut ve nominal kara merkezlerinin alan/zaman
tanıları örneklere ayrıca eklenir; eşik seçilmez, gözlem kapısı açılmaz.

Her boş olmayan tabakadan en fazla iki birim alınır. Sabit
`label-review-pilot-v1-seed42` tohumu ve hücre/tarih anahtarının SHA-256
sırası kullanılır. Tohum sonuçlara bakılarak aranmamıştır. Seçim satır
sırasından ve aylık parçalara bölünmeden bağımsızdır. Her tabakanın N
popülasyonu, n örneği, n/N seçilme oranı ve N/n genişletme ağırlığı saklanır.
Bu, tekrarlanabilir sözde rastgele seçimdir; tohum sabitlenince liste de sabittir.

İki birim seçimi bir **iş akışı pilotudur**; istatistiksel güç/örneklem
büyüklüğü hesabı veya hata oranı güvencesi değildir. Amaçlı vakalarla
birleştirilerek oran hesaplanmaz. Tabakaların seçilme oranları eşit değildir;
ileride bağımsız referans ve uygun örneklem büyüklüğü sağlanırsa tasarım
ağırlıklarıyla ayrıca analiz gerekir. Şu anda hata oranı hesaplanmaz.

## Çıktılar ve insan incelemesi

`outputs/reports/dataset/label_review_v1/<yeni-çalışma>/` altında:

| Dosya | Kullanım |
|---|---|
| `purposive_event_cases.csv` | Korunan vakalar, seçim gerekçeleri, üyelik kimliği ve boş hedef |
| `event_observation_links.csv` | Bütün ilk hücrelerin iki ayrı tarih rolüyle gözlem bağlantısı |
| `random_grid_days.csv` | Pilot hücre-günler, tanılar, arazi/meteoroloji bağlamı ve seçim oranları |
| `stratum_allocation.csv` | Her boş olmayan tabakanın N/n ve ağırlıkları |
| `sampling_geography.csv` | Bütün 2.899 hücrenin sektör ataması |
| `review_decisions_template.csv` | Karar ve kanıt alanları boş insan inceleme formu |
| `readback.json` | Kaynak/kod/çıktı hash'leri, kapsam, sayaçlar ve bilimsel sınırlar |

Kabul edilmiş şablonun üzerine yazılmaz. Gerçek inceleme, bu paketin hash'ine
atıf yapan ayrı tarihli bir revizyonda kaydedilmelidir. Her değerlendirmede
inceleyen kişi, inceleme zamanı, bağımsız kanıtın kaynağı/tarihi, olay yorumu,
ilk hücre, habitat, gözlem yeterliliği ve belirsizlik gerekçesi bulunmalıdır.
Bağımsız referans bulunamadığında karar belirsiz kalır. Aynı FIRMS/VIIRS
tespitini yeniden görüntülemek bağımsız doğrulama olarak sayılmaz.

Bu formun doldurulması da tek başına hedef üretme izni vermez. Kabul edilen
olay/ilk hücre tanımı, habitat kapsamı, Type anlamı, negatif gözlem protokolü
ve dönem kenarı kuralları ayrı sürümlenmelidir. `target` boş,
`positive_label_permitted=false`, `negative_label_permitted=false`,
`daily_observation_status=unknown`, `model_ready=false` korunur.

## Yerel çalıştırma

```powershell
.\.venv\Scripts\python.exe scripts/quality/prepare_label_review.py --per-stratum 2
```

Komut, hash ile bağlı 72 aylık gözlem kaynağını ve eski vaka paketini okur;
yeni sonuç dizini açar. Kaynak değişimi, eksik anahtar, kaybolan ilk hücre,
yanlış gece yarısı penceresi veya açık etiket kapısında durur. Aylık okuma
sınırında 15 dakikalık yerel süre rezervi vardır. Çıktı CSV'leri dosyadan
geri okunup karşılaştırılır; girişler kapanışta tekrar hash ile kontrol edilir.

## Gerçek sonuç ve kabul sınırı

Gerçek ilk çalışmada 6.351.709 hücre-günün 200 boş olmayan tabakasından
400 pilot hücre-gün seçildi. Bunların 192'si termal merkezli, 192'si ürünlü
ama seçilmiş termal merkezi olmayan, 16'sı eksik ürünlü gruptadır. Kaynak
çerçevesindeki karşılıkları sırasıyla 17.922, 6.327.989 ve 5.798 hücre-gündür.
Pilotun ham grup oranları toplumdaki oranların tahmini olarak kullanılamaz.

53 amaçlı vaka ve 400 pilot birim için 453 boş inceleme kaydı hazırlandı.
14 vakadaki çoklu ilk hücreler korunarak 104 vaka-ilk hücre için iki rol,
toplam 208 bağlantı oluşturuldu. Bu gerçek seçkide iki rol aynı güne
denk gelmiştir; gece yarısında önceki T'ye kayma davranışı ayrıca test edildi.
208 rol bağlantısı yalnız 28 farklı hücre-gün gözlem kaydını tekrar kullanır;
208 bağımsız gözlem veya yangın değildir.

18 bağlantı, aynı 2023-12-31 hücre-gününün dokuz ayrı senaryodaki iki
rolüne aittir ve kaynak ürünü eksiktir. Ölçüleri boş kaldı; yanlış pozitif,
yangın yok veya 18 ayrı kaynak kaybı olarak yorumlanmadı. Bu bulgu gözlem
bağlamını kaybetmeden vaka incelemenin neden gerekli olduğunu gösterir;
bağımsız referansla etiket doğruluğu ölçümü değildir.

İlk çalışma 117,81 saniyede dosya geri okumasını geçti. Daha sonra CSV boş
değer tiplerinin karşılaştırması ve yöntem pinlerinin işlem başında alınması
sağlamlaştırıldı. İlk rapor ve çalıştırılan kod kopyaları
`20261014T153230Z_b7c41b48` altında korundu; eski kabul dosyası değiştirilmedi.
Şablon hazırlığı insan incelemesi, bağımsız saha doğrulaması veya model
başarısı olarak raporlanmaz.

Son sürüm 18:36:50 Türkiye'de, 137,19 saniyede dosya geri okumasını geçti.
İlk pilotla altı çıktı CSV'sinin baytları aynıdır; son sağlamlaştırma
örnekleri veya vaka ilişkilerini değiştirmedi. 51 ilgili test, lint ve
format kontrolü geçti. Testler, sıra/parça bağımsız örnek seçimi, N/n,
eksik ürün/sıfır ayrımı, kapalı bilimsel kapılar, çoklu ilk hücre,
gece yarısı ve takvim dışı bağlantı, değişmiş kaynak hash'i, holdout
reddi ve boş insan inceleme alanlarını kapsar.

Final dizini:
`outputs/reports/dataset/label_review_v1/20261014T153649Z_ca3fb92e/`.

- `readback.json` SHA-256:
  `36ce8565a452efbf2a4f1e69fe3254ae33ccdd818eb08584f57b41a9eaf28037`.
- `completion_readback.json` SHA-256:
  `40bc3ac82c37f54f36d4bfcda4353aec550ed5c3e0b827ebcf4731505ab9b781`.

Kapanışta altı çıktı ve 186 kaynak/yöntem kimliği yeniden hash ile
kontrol edildi; 22 donmuş bulut girdisi aynı kaldı. Örnek anahtarları,
tabaka N/n toplamları, boş karar/hedef alanları ve 18 eksik ürün rolünün
aynı tek hücre-güne ait olduğu ayrı kontrolde doğrulandı. Bu kontrol
insan incelemesi veya yeni ham kaynak kabulü değildir. Yerel iş bitti.
