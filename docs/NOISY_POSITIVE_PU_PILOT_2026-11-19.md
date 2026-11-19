# Hata içerebilen pozitiflerle PU pilot hazırlığı — 19 Kasım 2026

Araştırmacı, ana 24 saatlik yangın hedefini koruyarak hata içerebilen
pozitif adayları modelleyen PU yolunun girdi/varsayım pilotunun
hazırlanmasını seçti. Sonraki vaka kararıyla Salur'da kaynakla eşleşen
tek hücre olası L üyeliği önerisine alındı. İki karar da gerçek yangın
etiketi, yöntem kabulü veya eğitime başlama onayı değil.

**Tamamlanan:** ham ilk grup denetimi, iki birincil yöntem incelemesi,
tam kesirli hesap ve incelenebilir girdi anahtarları. **Hazır olmayan:**
bilimsel kabul edilmiş L örneklemi, gerçek sınıf/hata oranları ve model.

## Salur'da yeni ölçüm

1 km / 24 saat ayarının ilk anda Salur'a bağlı **74 kaydı** ham dosyada
ayrı ayrı doğrulandı. Sonraki tam bileşende aynı dakika görünen 75'inci
kayıt o anda bu gruba bağlı değildi; ilk gruba eklenmedi. Önceki üyelik
hash'i korundu. Bütün ikililerin jeodezik mesafelerinden ayrıca kurulan
geçiş kapanışı, indeksli komşu aramasıyla aynı 74 üyeyi verdi.

74 merkez tek NOAA-20 taramasında: 28 Temmuz 2021
10.12.00,000738–10.12.00,564538 UTC. Ham satırlar 10–19 arasında.
Bu aralık, tek tek piksel zamanlarının ölçümü veya eşitliği değildir.
Tarama zamanı dört ilk hücreyi tek hücreye indirmiyor; satır numarasına
bakılarak yeni bir kronolojik seçim yapılmadı.

| Bu tek ilk gruptaki durum | Katalog/ham tespit sayısı |
|---|---:|
| Nominal güven maskesi 8 | 50 |
| Yüksek güven maskesi 9 | 24 |
| İlk yedi giriş kalite biti tamamen sıfır | 20 |
| En az bir giriş kalite uyarısı | 54 |
| M13 kanal kalite uyarısı | 50 |
| Geolocation kalite uyarısı / artık bowtie | 0 / 0 |

Tamamen temiz giriş şartı, bu gruptaki yüksek güvenli 24 kaydın
tamamını ve Salur'un ilk yerel kaydını çıkarıyor. Kalan 20 kayıt yine
dört hücrede. Bu yalnız **bu vaka ve bu ayar için filtre duyarlılığı**;
uygulanan pozitif kabul kuralı, yanlış tespit oranı veya bütün dönem
ölçümü değil. Kalite uyarısı ile yanlış yangın etiketi eşitlenmedi.
[Önceki tek piksel ve kılavuz incelemesi](SALUR_LOCAL_COVER_2026-11-19.md).

Komut `python scripts/quality/audit_salur_prefix_quality.py`.
Makbuz `outputs/reports/dataset/salur_prefix_quality_v1/20261119T120007Z_42e00153/readback.json`.
SHA-256 `69c361554207695fbaa20d28a46ee04372860dbdf0ad4635ee8e5c98ac3f716c`.

## Yöntem için yeni kanıt

Shantanu Jain, Martha White ve Predrag Radivojac'ın **NIPS 2016**
çalışması, U ve hata içerebilen L'yi ortak iki sınıf dağılımının farklı
oranlı karışımları olarak ele alıyor. Pozitif zenginleşme ve ortak sınıf
koşullu dağılımlar önemli. Genel durumda oranlar tekil değil; karşılıklı
indirgenemezlik koşulu altında bir kanonik ayrıştırma tanımlanıyor.
Tek boyutlu dönüşümün oran koruma koşulları da ayrıca var.
[Yayıncı kaydı](https://papers.nips.cc/paper_files/paper/2016/hash/79a49b3e3762632813f9e35f4ba53d6c-Abstract.html),
[birincil PDF](https://proceedings.neurips.cc/paper_files/paper/2016/file/79a49b3e3762632813f9e35f4ba53d6c-Paper.pdf).

Aynı yazarların **AAAI 2017**, s. 2066–2072 çalışması, ortak karışım
modelinde sınıf oranı ve pozitif kümenin saflığı bilindiğinde/tahmin
edilebildiğinde TPR/FPR ve PR/ROC değerlendirmesinin düzeltilebileceğini
gösteriyor. Bu koşullu sonuç bilinmeyen oranları otomatik sağlamıyor.
[Yayıncı makalesi](https://ojs.aaai.org/index.php/AAAI/article/view/10937),
[yazarın PDF'i](https://www.ccs.neu.edu/home/radivojac/papers/jain_aaai_2017.pdf).

Kimlikler yayıncı ve arXiv kayıtlarıyla eşleşti. NIPS yöntem s. 2–6,
özellikle 3 ve 5; AAAI yöntem s. 2068–2069 incelendi. Kritik sayfalar
görüntüden de kontrol edildi. Yöntemler uygulanıp başarımı ölçülmedi.
NIPS arXiv v2 kaydı, ekte MSGMM yazım düzeltmesi belirtiyor; algoritma
kodu uygulanmadığından bu incelemede ek denklemler kullanılmadı.

**Projeye ilişkin çıkarım:** bütün PU yollarına kusursuz pozitif şartı
koymamalıyız. Buna karşılık kanonik matematiksel bileşenlerin gerçek
yangın/yangın dışı sınıflar olduğunu ve seçilmiş adayların genel nüfusla
aynı sınıf koşullu dağılımı paylaştığını gerekçelendirmeliyiz. Büyük ve
haberlere geçen olayların seçilmesi bu konuda incelenecek olası yanlılık;
bu raporda istatistiksel ihlal kanıtlanmış sayılmadı.

Gerçek yangın oranı `alpha`, L içindeki gerçek pozitif payı `beta` olsun.
Bu projede ikisi de ölçülmedi. 54 kalite uyarısı, %60 görsel orman
tahmini veya kaynak eşleşme payı `1-beta` olarak kullanılamaz.

## Sayısal formül kontrolü

Tam kesirli **yapay** bir örnekte `alpha=1/20`, `beta=4/5`, gerçek
TPR `4/5`, FPR `1/10` seçildi. L'de eşik üstü oran `33/50`, U'da
`27/200`. Bilinen parametrelerle formüller gerçek oranları aynen verdi.
Eşit büyüklükte L/U test havuzunda U'yu negatif sayan sözde precision
`44/53` (%83,02); gerçek yapay nüfus precision'ı `8/27` (%29,63).
Bu AP, kalibrasyon veya yangın deneyi değil. Tekil payda ve tutarsız
oranlar sessizce kırpılmak yerine reddedildi.

Komut `python scripts/quality/audit_noisy_positive_pu_review.py`.
Makbuz `outputs/reports/dataset/noisy_positive_pu_review_v1/20261119T120556Z_7e0c19bb/readback.json`.
SHA-256 `3b7b785f9363f91b903f34358d9cdba59cee1b187daf7e604ddf4877b2c012ad`.
Kaynak PDF SHA-256 değerleri:
NIPS `76411399354dc4de3d296f8867071b5d25edf0b445cb809f76e05a2e3f824478`,
AAAI `2b2594513ebf9b5dfc434704d3b989313647581c7613db0246a143c7f8a7933f`.

## Hazırlanan girdiler ve araştırmacı kararları

Yeni [pilot yönü ayarı](../configs/noisy_positive_pu_pilot_v1.json)
girdi hazırlığıyla sınırlı. Eski hash ile bağlı protokoller değiştirilmedi.

- **U:** 2.889 korunmuş hücre × 1.825 gün = 5.272.425 olası hücre-günden
  2.048 anahtar, sabit PCG64 tohumu ile eşit olasılıklı ve tekrarsız
  seçildi. Yangın, gözlem kalitesi ve L yakınlığıyla seçim/eleme yapılmadı.
  T aralığı 1 Ocak 2018–30 Aralık 2022. Sağ uç 2023'e değmesin diye
  31 Aralık 2022 yalnız bu pilot fit-rolü önerisinde yok; ana takvimden
  silinmedi. Önceki 2023 kalibrasyon, 2024 karşılaştırma ve 2025 kapalı
  final yönü korundu. Örnek büyüklüğü yeterlilik kanıtı değildir.
  Eşit olasılıklı seçim hücre/gün bağımlılığını ortadan kaldırmaz.
  Gelecekte her foldun oran/ön işleme tahmini yalnız o foldun eğitim
  parçasıyla yapılacak; bu havuzdan küresel oran öğrenilmedi.
  CSV'deki örnekleme ağırlığı tasarım bilgisi; sınıf ağırlığı veya
  eğitim kaybında kullanılacak kabul edilmiş ağırlık değildir.
- **L incelemesi:** başlangıçta tek Salur vakasına bağlı dört hücre
  olasılığı hazırlandı; dört ayrı yangın veya dört gerçek pozitif değil.
  Araştırmacı A'yı seçti: iki kaynak işareti uyumunun ve ilk yerel ham
  merkezin kesiştiği `C605_R879` hücresi için **olası L üyeliği önerisi**.
  Diğer üç hücre aynı vaka kimliği altında incelemede korundu.
  Bu tek vaka kararı genel eşleştirme kuralı değildir.
- **Etiket:** bütün tablolarda `target` boş. L önerisi de Y=1 kabulü
  değildir. Özellik değerleri bağlanmadı. U örneklemi değişmedi; L/U
  olası anahtar kesişimi incelendi, sessiz silme yapılmadı; burada sıfır.

L yönü [ayrı sürümlü ayarda](../configs/source_linked_L_proposal_v1.json).
Komutlar `python scripts/quality/prepare_noisy_positive_pu_pilot.py` ve
`python scripts/quality/prepare_source_linked_L_proposal.py`.

U ve dört hücreli ilk inceleme:
`outputs/reports/dataset/noisy_positive_pu_pilot_v1/20261119T121014Z_122b22c7/readback.json`.
SHA-256 `85d563d82dc13656136fe855e8e80252e5ef28dbdbb799fe3a0c814a3414f0b2`.
Son tek L önerisi ve korunmuş üç hücre:
`outputs/reports/dataset/source_linked_L_proposal_v1/20261119T121351Z_2d9aeb30/readback.json`.
SHA-256 `d0a09ecb249eb81d75e4494beaf0ca9989092c813ddd6b40e4acf0817576ab3e`.

## Geçiş sınırı ve kontroller

Pilotun **girdi hazırlığı tamamlandı**, gerçek veriyle karışım tahmini
yapılmadı. Tek kaynak vakası sınıf koşullu karşılaştırılabilirlik, hata
oranı, sınıf oranı veya dört ilde değerlendirme yeterliliği göstermiyor.
Sonraki iş daha geniş, kaynak kökeni açık L aday örneklemi ve onun
seçilme mekanizmasını incelemek. Doğru hedefe olay/hücre/gün eşlemesi
ve yöntemin varsayım desteği ayrı kalıyor; algoritma bunları yaratmıyor.

Girdi/çıktı hash'leri, CSV geri okumaları, 74 üyenin ham sınıf/koordinat
uyumu ve bağımsız grafik kapanışı kontrol edildi. U anahtarlarının gün/
indeks/sağ-uç dönüşümü ayrıca standart CSV/datetime ile yeniden okundu.
İki boş hedef tablosu mevcut ikili değerlendirme fonksiyonuna verildi;
ikisi de reddedildi. Eski test sayıları güncel sonuç diye yazılmadı.
Mevcut hedef kabulü/değerlendirme davranış kontrollerinde bu oturumda
83 test geçti; yeni dört komutta Ruff ve biçim kontrolü geçti.
İlk çalışma sürümlerindeki boş değer eşitliği ve zaman toplama
uyarıları açık tip/zaman birimiyle giderildi; eski çıktılar korundu.

Birinci aşama açık. Gözlem `unknown`, pozitif/negatif izinleri kapalı;
model/eğitim/nihai birleştirme yapılmadı. 2023/2024/2025 veri değerleri
açılmadı; takvim sınırı ve açık rol ayarları veriye erişim sayılmadı.

Son kapanışta dört yeni rapor, 34 tekil kaynak/çıktı/kod dosyası ve
korunan tek vaka/dört hücre üyeliği geri okundu. Bu dosya sayısı
bağımsız deney veya eğitim örneği sayısı değildir. Makbuz:
`outputs/reports/dataset/noisy_positive_pu_closure_v1/20261119T121836Z_71d0dc4b/readback.json`.
SHA-256 `3607dcbbf9b0ad0ad2b9a63498d4005ac15fcda55ba42dd554985c46c3fbe7d5`.

## Aynı gün kapsam devamı

Marmaris kaynak/ham/örtü/zaman kontrolü ve araştırmacının tek-vaka A
kararı sonrasında iki kaynak vakası için iki olası L önerisi inceleme
dizininde tutuluyor. Eski tek-Salur yapılandırması ve makbuzları değiştirilmedi;
yeni kapsam ayrı çıktı ve `configs/marmaris_L_proposal_v1.json` ile kayıtlı.
2.048 U anahtarı aynı; hedefler boş, oran/karışım tahmini yok.
Kaynak seçimi varsayımını incelemek için Mersin'in 2018–2022 coğrafi
tablosundaki 424 satırdan, yalnız kimlik/yıl kullanılarak 10 kontrol
satırı donduruldu. Bunlar L üyeleri veya doğrulanmış yangınlar değil.
[İki öneri ve kaynak-temelli kontrol örneklemi](SOURCE_SAMPLING_REVIEW_2026-11-19.md).
