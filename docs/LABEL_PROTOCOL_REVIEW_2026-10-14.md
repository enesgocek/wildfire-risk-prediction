# Olay/etiket protokolü için ölçülmüş seçenekler — 14 Ekim 2026

## Yapılan işlem

Sabit 400 örnekli pilot, daha önce geri okunmuş dokuz eğitim olay
senaryosuyla karşılaştırıldı. Yeni kümeleme yapılmadı. 500/1.000/2.000 m
ve 24/48/72 saat bağlantı senaryolarının ilk zamanındaki **bütün bağlı
ilk hücreleri** korundu; canonical hücre alfabetik olarak hedef yapılmadı.
Her grid/hedef gününde aday küme sayısı ve üyelik hash kümeleri karşılaştırıldı.
3.600 örnek/senaryo kaydı üretildi. Bunlar 3.600 farklı olay değildir.

Özgün 400 örnek, 200 tabaka/ağırlık, gözlem ve boş hedefler aynı kaldı.
İnceleme yönlendirmesi ayrı sütunlardır; eğitim özellikleriyle hedeflerin
nihai tam birleştirmesi yapılmadı.

## Ölçülen olay senaryosu duyarlılığı

| 400 örnekte ilk hücre/gün katalog eşleşmesi | Ham örnek sayısı |
|---|---:|
| Hiçbir senaryoda aday ilk hücre/gün eşleşmesi yok | 304 |
| Dokuz senaryoda eşleşme ve eşleşen üyelik hash kümeleri aynı | 77 |
| Dokuz senaryoda eşleşme var, üyelik kümeleri farklı | 11 |
| Yalnız bazı senaryolarda eşleşme var | 8 |

Son iki satırdaki **19 örnek**, senaryo seçimine duyarlı inceleme kümesidir.
İlk hücre/gün varlığının aynı çıkması yeterli değildir: 11 örnekte bu
varlık sabit olduğu hâlde olay üyeleri değişiyor. Aynı üyelik çıkan 77
örneğin beşinde de zincir/çoklu ilk hücre/dönem gibi en az bir kayıtlı
inceleme bayrağı var. Dolayısıyla senaryo ortaklığı fiziksel olay kimliği
veya doğrudan pozitif kabulü değildir.

304 eşleşmesiz örnek, 192 nominal termal merkezsiz, 16 kaynak ürünü eksik
ve **96 termal merkezli** örnekten oluşuyor. Bu 96 örnekte ilk olay
eşleşmesi yokluğu, yangın yokluğu anlamına gelmez. Devam eden tespit,
FIRMS Type/güven seçimi, L2 sınıfı, zaman veya kaynak/konum farkı ayrıca
incelenmelidir; nedenlerden biri otomatik doğru sayılmadı. Yeni hedef,
her termal pikseli yeni yangın kabul ederek üretilemez.

Dokuz senaryonun bütün eğitim kataloğunda 6.089–8.485 keşif kümesi vardır;
bunlar kabul edilmiş bağımsız yangın sayısı değildir. Küme sayısı az veya
çok diye bir senaryo üstün seçilmedi; 2024/2025 kullanılmadı.

## Kaybolmayan işaretlerle önerilen inceleme sırası

Aşağıdaki yönlendirmeler birbirini dışlayan **iş sıralama kategorileridir**.
Kaynak, zaman ve katalog bayraklarının tamamı ayrıca korunur; ilk sıradaki
gerekçe diğer belirsizlikleri silmez. Hiçbir kategori 0/1 hedef değildir.

| İlk inceleme kategorisi | Örnek |
|---|---:|
| Su kapsamı dışında, yalnız denetim | 1 |
| Kaynak paketi eksik | 16 |
| Sınır tarama zamanı belirsiz | 2 |
| Olay senaryosu uyuşmazlığı | 19 |
| Ortak katalog ilk adayı; olay/kaynak kabulü gerekli | 75 |
| Termal merkez var, katalog ilk aday eşleşmesi yok | 96 |
| Nominal kara merkezi desteği yok | 10 |
| Termal/ilk aday yok, kaynak tam ve kara merkezi var; arka plan incelemesi | 181 |

Son satır negatif etiket kabulü değildir. En az bir nominal kara merkezi,
bulutsuz bütün gün, yeterli alan desteği veya kaçırılmamış yangın kanıtı
sağlamaz. Alan birleşimi/zaman, kaynak semantiği ve seçim yanlılığı açık kalır.
Sayılar eşit olmayan olasılıklı sabit pilotun ham sayılarıdır; popülasyon
veya etiket hata oranı olarak raporlanmaz.

## Gerekçeli seçenekler ve öneri

1. **Tek olay senaryosu:** bir uzaklık/zaman kuralını gerekçelendirip
   dondurmak uygulamayı sadeleştirir. Bunun için 19 duyarlı örnekte ilk
   zaman/hücre ve zincir etkisi değerlendirilmeli; 1 km/24 saat yalnız
   yaygın göründüğü için seçilmemelidir.
2. **Önce ortak/duyarlı adayları ayrı incelemek — önerilen sonraki iş:**
   77 ortak üyelik ve 19 duyarlı örnek ayrı tutulur; bayraklılar öncelikli
   kaynak incelemesine gider. Bu, nihai veri setine yalnız bütün senaryoların
   uzlaştığı örneklerin alınması kararı değildir. Böyle bir filtre kullanılırsa
   kapsam ve seçim yanlılığı ayrıca ölçülmelidir.
3. **Tarihli referansa dayalı alt küme:** olay kaydı/sınırıyla değerlendirilen
   bir alt kümede ilk tespit kuralını sınamak mümkündür. Referans kapsamı,
   büyük yangına seçilim ve ortak sensör bağımlılığı sınırlamadır; bütün
   olaylara bağımsız yer gerçeği elde edilmiş sayılmaz.

Mevcut öneri ikinci sırayla incelemeyi sürdürmek, daha sonra gerekçeli
olay kuralını araştırmacıya sunmaktır. 181 arka plan örneğinde negatif
gözlem ölçütü için ayrı kanıt gerekir; sayımı sıfır olan her satıra sıfır
etiket atanması önerilmiyor. Hiçbir olay veya negatif politika seçilmedi.

### Literatür ve resmî kaynakla karşılaştırma

Mesogeos, olay dayanağı olarak EFFIS yanmış alanlarını, ilk zaman/konumu
iyileştirmek için MODIS tespitlerini kullanır. Büyük yangın tehlikesi
görevinde negatif örnekleme ve örtü dağılımı ayrıca tanımlanır. Bizim tüm
kapsamda böyle bir referans olay envanterimiz yok; o çalışmanın etiket
kurallarını doğrudan taşımak aynı hedefi veya doğruluğu sağlamaz. Bu bir
yöntem karşılaştırmasıdır; onların değerlendirmesi bu projenin sonucu değildir.
[Mesogeos, NeurIPS 2023; ilgili yöntem bölümleri 14 Ekim'de yeniden kontrol edildi](https://papers.nips.cc/paper_files/paper/2023/file/9ee3ed2dd656402f954ef9dc37e39f48-Paper-Datasets_and_Benchmarks.pdf).

NASA, bulut/duman/örtü ve uydu geçişleri arasında kısa süren yangınların
tespit edilemeyebileceğini açıklar. Bundan çıkan proje yorumu, tespit
yokluğunu doğrudan fiziksel yangın yokluğu saymamaktır. Kaynak tek başına
bizim için sayısal bir gözlem eşiği sağlamaz.
[NASA FIRMS açıklamaları; erişim 14 Ekim 2026](https://firms.modaps.eosdis.nasa.gov/alerts/notes.php).

## Nihai birleştirme için kullanıcının son kontrol/onay isteği

Araştırmacının yeni talebi proje kuralına ve kabul sözleşmesine eklendi:
meteoroloji, arazi/örtü, bitki örtüsü, gözlem ve hedef parçaları nihai tam
birleştirmeden **hemen önce** ayrı son kontrolden geçecek; rapor sunulacak
ve açık kullanıcı onayından sonra birleştirilecek. Eski kontroller son
kontrolün yerine geçmez. Genel devam talimatı nihai birleştirme onayı değildir.

`final_merge_review_v1.json` bu akışı, `final_merge_gate.py` gelecekteki
nihai birleştiricinin çağıracağı programlama kontrolünü tanımlar. Eksik
parça/bilimsel kabul, onaysız veya başka rapora ait makbuz reddedilir.
Parça kimliği değişirse eski rapor hash'iyle verilen onay geçmez. Gerçek
onay makbuzu hazırlanmadı; testlerdeki makbuzlar yalnız sentetiktir.
Bu işlev kullanıcı kimliğini doğrulayan güvenlik servisi değildir ve
henüz var olmayan nihai birleştiricinin yerine geçmez. Nihai birleştirici
güncel dosyaları ayrıca doğrulayıp bu işlevi çağırmalıdır.

## Gerçek kontrol ve kayıt

97 ilgili test ve beş yeni Python dosyasında lint/format geçti. Testler
çoklu ilk hücreleri, aynı varlık/farklı üyeliği, eksik senaryoyu, kapalı
etiket koşullarını, eksik/eski onayı ve değişmiş parça kimliğini kapsar.
Dört çıktı/46 giriş ve 22 donmuş girdi hash ile kapanışta kontrol edildi.
Önceki beş pilot çıktısı ve kaynak kataloglar aynı kaldı.

Komut: `.venv\Scripts\python.exe scripts/quality/review_label_protocol.py`.
Yeni sonuç dizini:
`outputs/reports/dataset/label_protocol_v1/20261014T193224Z_54fdbb95/`.
Çıktılar: `pilot_protocol_review.csv`, `pilot_scenario_matches.csv`,
`scenario_overview.csv`, `protocol_options.json`.
`readback.json` SHA-256:
`534d67c44cad55a267aaf57330b4396a9cbb6aa65baa8bfdd71b9037b7bb0cab`.
Kapanış SHA-256:
`97bb378040b2a7dd74893ddb163803794316fc29f6a28932ad992cee917d7e40`.

Hedefler boş, `daily_observation_status=unknown`, etiket izinleri kapalı
ve `model_ready=false`. Nihai birleştirme/onay, model eğitimi, 2024/2025
veri erişimi veya yeni bulut işi yok. Araştırmacıdan şu an ham görüntüye
bakarak yangın veya piksel günü tahmin etmesi istenmiyor. Olay kuralı
seçimi için 19 duyarlı örneğin kaynak/zincir incelemesi önerilen sonraki iştir.
