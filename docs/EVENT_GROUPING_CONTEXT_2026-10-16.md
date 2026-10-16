# Olay gruplama: yöntem kaynakları ve hedef gün sonrası bağlam

16 Ekim 2026. Durum: sınırlı yöntem araştırması ve yerel tanı tamamlandı;
olay kimliği veya gruplama eşiği kabul edilmedi. Önceki A tercihiyle bütün
ilk hücreleri ortak aday kimliği altında koruma kuralı değişmedi.

**19 duyarlı örnek × dokuz ayar = 171 karşılaştırmada**, hedef günün
sonrasındaki tespitler çıkarılınca ilk zaman/hücre kümesi veya aday eşleşmesi
değişmedi. Bu seçilmiş örneklerde ayarlar arasındaki farkı hedef gün
sonrasındaki bağlantılara bağlayamayız. Bu bulgu tüm katalog için güvence,
bağımsız olay doğrulaması veya herhangi bir eşik için doğruluk kanıtı değildir.

## Gerçek kaynaklarda aynı sayı farklı bir kural olabilir

Üç yöntemin ilgili tam metin bölümleri yeniden kontrol edildi.
[Kaynak sicili](research/event_grouping_sources_2026-10-16.json), erişilen
bölümleri, kimlik doğrulamasını ve erişim sınırlarını kaydeder. Mesogeos
önceki literatür sicilindeki çalışmadır; yeni ve bağımsız bir dördüncü
çalışma gibi sayılmaz. Bu araştırma sistematik derleme veya deney tekrarı değildir.

| Birincil kaynak | Okunan yöntem | Bizim kapsamımız açısından sonuç |
|---|---|---|
| Chen ve ark., 2022 — [FEDS tam metni, s.4–6](https://efi.eng.uci.edu/papers/efg_242.pdf) | Zaman adımlarında nesne büyütme ve birleşme; ilk atanmış piksel kimliği ve birleşme geçmişi saklanır. Beş günlük aktiflik, ormanda 5 km/diğer tiplerde 1 km çevre tamponu kullanılır. | Bunlar iki ham tespit arasındaki sabit mesafe/aralık kuralıyla aynı değildir. Kaliforniya girdileri ve doğrulaması Türkiye'ye aktarılmış sayılmaz. |
| Kondylatos ve ark., 2023 — [Mesogeos, §3–4.1](https://papers.nips.cc/paper_files/paper/2023/file/9ee3ed2dd656402f954ef9dc37e39f48-Paper-Datasets_and_Benchmarks.pdf) | EFFIS olay alanı çevresinde 1 km ve tarih çevresinde yedi günlük arama ile MODIS ilk tespiti bulunur. Olayın omurgası hotspot kümesi değildir. | Yedi gün tahmin ufku veya VIIRS komşuluk aralığı değildir. Bizde uygun olay referansı olmadan aynı eşikler kullanılamaz. |
| Cardíl ve ark., 2023 — [NHESS, §2.3](https://nhess.copernicus.org/articles/23/361/2023/) | 5 km gridde komşu hücre büyütme; en az 48 saat tespitsizlikte ayırma; 20'den az hotspot olan kümeleri çıkarma. Eşikler sezgiseldir. | Büyük yangınların yayılım hızı için kurulan örneklem, bütün yeni olayları hedefleyen çalışmamız değildir. Bizim 5 km tahmin gridimiz bu gruplama kuralını gerekçelendirmez. |

FEDS'in makale kimliği yayıncı indeks kaydı ve yazar kurumundaki DOI'li
PDF ile; güncel uygulamayla ilişkisi [resmî algoritma belgesiyle](https://earth-information-system.github.io/fireatlas/docs/fireatlas_core.html)
kontrol edildi. Mesogeos konferans metni [resmî yazar deposuyla](https://github.com/Orion-AI-Lab/mesogeos)
eşleşti. Cardíl için yayıncının tam metni/yazar/DOI kaydı okundu; ayrı
kurum kopyası doğrulanmadı. Crossref adresi bu araçla açılamadı. Hiçbir
çalışmanın kodu/verisi bu incelemede yeniden çalıştırılmadı. Birleşme
geçmişini kaydetmenin yararlı bir aday yaklaşım olduğu yorumu, bizim
projemiz için ayrıca sınanması gereken araştırma önerisidir.

## Ölçülen soru ve kesim anı

Mevcut dokuz senaryo, 500/1.000/2.000 m ve 24/48/72 saatlik **kenar**
koşullarıyla yönsüz bağlı bileşenlerdir. Kenar aralığı bileşenin toplam
ömrünü sınırlandırmaz. Nihai grafik daha sonraki tespitlerle eski parçaları
birleştirebilir; bunun bu 19 örneğin hedefini gerçekten değiştirip
değiştirmediği ölçüldü.

Her örnekte kesim anı **T+24 saat** alındı. Bu, tahmin anı T değildir;
hedef pencerenin bittiği andır. `timestamp <= T+24 saat` kayıtları tutuldu.
Geçmiş tespitler başlangıç bağlamı için korundu; yalnız hedef günün içine
hapsedilmiş bağımsız günlük kümeler kurulmadı. Ham ölçümlerin edinilme zamanı
kullanıldı; operasyonel veri yayın gecikmesi bu tanıda modellenmedi.

Etiket inşasında daha sonraki bağımsız olay bilgisinin kullanılması tek
başına model girdisine gelecek bilgisi sızdığı anlamına gelmez. Buna karşılık
olay tanımının hangi bağlam ufkunda dondurulduğu kaydedilmeli; eğitim/2024/
2025 sınırları aşılmamalıdır. Bu tanı yalnız 2018–2023 kaynaklarını okudu.

## Kanıt yolu ve sonuç

181 bileşen bağlamının 58'inde pencere sonrasında üye vardı. Kaydedilmiş
**39.694 yol-adımı satırının** kaynak kimlik/zaman/konumu ve ardışık kenarların
WGS84 mesafesi/zaman aralığı tekrar kontrol edildi. Her bağlamda bütün ilk
tespit×örnek tespiti çiftleri için yol kapsamı doğrulandı. Bunlar 39.694
bağımsız kenar veya fiziksel yayılım yolu değildir.

| Kontrol | Sonuç ve anlamı |
|---|---|
| Pencere sonrasına geçmeyen tanık yollar | 174 bağlamda bütün ilk tespitler örneğe kesimden önce zaten bağlı; ilk kümenin korunması doğrudan gösterildi. Bütün altgraf üyeliği yeniden kurulmadı. |
| Kaydedilmiş yolda pencere sonrası nokta bulunan bağlam | 7; bu durum tek başına sonraki noktaya zorunlu bağımlılık göstermez. |
| Tam kesilmiş grafiği yeniden kurulan bağlam | Bu 7 bağlamda yarıçap ve zaman kenarlarıyla yeniden kuruldu; alternatif eski yollar bulundu. |
| İlk zaman/hücre imzası değişen bağlam | **0/181** |
| Aday varlığı değişen örnek×ayar | **0/171**; eşleşmeme negatif yangın etiketi değildir. |

Somut örnek: 5 Ekim 2021, C557_R877'nin şüpheli altı senaryosunda tam
bileşen 21/22 üyedir; gün sonuna kadar 10 üye kalır. Buna rağmen ilk
kayıtlı **23.29 UTC**, iki ilk hücre **C556_R877/C557_R877** ve örnek
eşleşmesi korunur. Bazı eski tanık yolların sonraki güne uğraması alternatif
eski yollar bulunmadığını göstermemiştir. 12 Ekim 2023, C583_R882'nin
500 m/72 saat senaryosunda da ilk **10.49 UTC** ve hücre korunur.

Yedi yeniden kurma [ayrı tabloda](../outputs/reports/dataset/event_window_context_v1/20261016T183626Z_0c072991/rebuilt_prefix_components.csv),
171 sonuç [karşılaştırma tablosunda](../outputs/reports/dataset/event_window_context_v1/20261016T183626Z_0c072991/unit_scenario_comparison.csv)
saklanır. Örneklem amaçlı ve duyarlılık seçimine bağlıdır; bütün 30.295
eğitim tespitinde aynı sonuç elde edildiği ileri sürülmez.

## Sonraki araştırma işi

Bu tanı, dokuz ayardan en doğrusunu seçmez. Önceki 19 örneğin sekizinde
ayar değişince aday varlığının değişmesi bulgusu geçerliliğini korur.
Sıradaki sınırlı karşılaştırma, zaman içinde oluşan adayları ve sonradan
birleşmelerini ayrı kaydederek **başlangıç, devam, bölünme ve birleşme**
durumlarını ayırmaktır. Bu bir öneri/deney hazırlığıdır; FEDS'in aynen
uygulanması veya yeni olay kuralının kabulü değildir. Mevcut dokuz
senaryo karşılaştırma olarak korunmalı; gerçek ayrılma/birleşme doğruluğu
uygun referans örnekleri ve kapsam denetimiyle değerlendirilmelidir.

Sadece yüksek model skoru veya az sayıda küme üreten ayarı seçmek etiket
doğrulaması sağlamaz. Grup seçimi, habitat ve güvenilir negatif/gözlem
koşulları çözülene kadar hedefler boş kalır. Kullanıcıdan mevcut görsellere
bakarak gerçek yangın kimliğini veya keyfî bir mesafe eşiğini tahmin etmesi
istenmiyor. Bir politika değişikliği somut etkileriyle ayrıca sunulacaktır.

## Kontrol ve tekrar üretim

`python scripts/quality/audit_event_window_context.py` ağ erişimi kapalı
yerel tanıdır; yukarıdaki literatür okuması ayrı web araştırmasıdır.
16 doğrudan girdi/beş çıktı hash kapanışı ve CSV geri okuması geçti.
**8 yeni vaka dahil 95 ilgili test**, üç dosyada lint/format kontrolü geçti.
Testler sonraki köprü, alternatif eski yol, eşit zamanlarda sıra bağımsızlığı,
kesim anının dahil edilmesi, gelecek ankraj/2024 girdisinin reddi ve mevcut
olay/etiket/nihai onay kontrollerini kapsar; bütün depo testleri değildir.
İlk test çalıştırmasında mevcut bir test sistem geçici klasörü oluşturamadı;
çalışma alanında yeni, benzersiz test klasörüyle tekrarında 95 test geçti.
Önceki tanı dizini korunarak son kod/testle yeni sonuç üretildi.

Sonuç: `outputs/reports/dataset/event_window_context_v1/20261016T183626Z_0c072991/`.
Readback SHA-256:
`52be23b64057c01666a3de8fe341f5646b1e6aa97c2bbeccd819c9eaa3ca21b4`.
Kapanış SHA-256:
`27e700bf751b64fe50dc1fec706b2aadffe1823c3c030a9506ca400ccb1c9ef8`.

Gerçek etiket, eğitim, yeni bulut işi, kaynak silme ve nihai birleştirme yoktur;
`daily_observation_status=unknown`, `negative_label_permitted=false` korundu.
