# Yangın riski literatürü ve araştırmanın konumlandırılması

İnceleme tarihi: **12 Ekim 2026**. Kapsam: Antalya, Muğla, İzmir ve Mersin'de
24 saat içinde yeni olayın ilk aktif yangın tespiti. Bu belge kaynaklı araştırma
değerlendirmesidir; model sonucu, danışman onayı veya yayın kabulü değildir.

İkinci kontrol notu — 12 Ekim: [kaynak varlığı denetiminde](LITERATURE_IDENTITY_AUDIT_2026-10-12.md)
34 kaydın yayın/ön baskı/veri/kurum varlığı ve yazar atfı doğrulandı.
R18'in 2025 Scientific Data yayını ve R32'nin 2023 IEEE TGRS yayını
sicile işlendi; önceki yayın-yeri belirsizliği burada açıklanarak düzeltildi.
Üç eksik DOI tamamlandı; R30 çalıştay kabulünün yazar bildirimi olduğu
ayrıldı. Bu kayıt kontrolü deneylerin bağımsız yeniden üretimi değildir.

## Temel sonuç

**Yapay zekâ ile uydu ve meteoroloji verilerini birleştirip ertesi gün yangın
riski üretmek daha önce yapılmıştır. Türkiye'de de yakın uygulamalar vardır.**
Projenin değeri, aynı genel fikri ilk kez sunduğumuz iddiasına bağlanamaz.
Buna karşılık yerel veri oluşturma, olay/etiket belirsizliğini ölçme, gerçekçi
zamansal değerlendirme ve uyarı yükünü karşılaştırma araştırma konusu olabilir.
Bunlar ancak karşılaştırmalı sonuçla katkıya dönüşür; iyi dosya düzeni veya
harita arayüzü tek başına bilimsel özgünlük değildir.

Bu taramanın önerisi, kapsamı büyütmek veya yeni bir model adını merkeze almak
yerine şu soruyu sınamaktır:

> Gözlem yeterliliği ve olay tanımındaki belirsizlik, dört ilde ertesi gün
> ilk yangın tespitini öngören modellerin ölçülen başarısını, olasılık
> güvenilirliğini ve sınırlı günlük uyarı kapasitesindeki yararını nasıl etkiler?

Bu soru öneridir. Eksik gözlemden güvenilir negatif çıkarma yöntemi ve bağımsız
olay doğrulaması kabul edilmeden model eğitimine geçişi yetkilendirmez.

## Tarama yöntemi ve kanıt sınırı

Web indeksi üzerinden İngilizce/Türkçe konu ve coğrafya sorguları, ardından
yayıncı, konferans, yazar/kurum kopyası ve resmî ürün sayfaları incelendi.
Tespit/oluşum, yatkınlık, FWI, yayılım, etiket eksikliği ve değerlendirme
araştırmaları ayrı gruplandı. Temel yöntem/ürün kaynakları ve 2026 yakın
çalışmaları dahil edildi. İlgisiz başlık eşleşmeleri ve birincil kaynağı
bulunamayan pazarlama sonuçları karşılaştırma dışı bırakıldı.

[Kaynak sicilinde](literature_sources_2026-10-12.json) **34 seçilmiş kayıt**
vardır: hakemli makaleler, konferans/veri kümesi kayıtları, ön baskılar,
derlemeler ve resmî ürün/kurum belgeleri birlikte. Bu sayı 34 bağımsız deney
veya 34 tam metin okuması anlamına gelmez. Her kaydın erişim düzeyi ve yayın
durumu ayrıdır. [Arama kaydı](literature_search_log_2026-10-12.json), sorgu
ailelerini, tutulan doğrulama sorgularını ve erişim sorunlarını içerir.

Bu çalışma eksiksiz sistematik derleme/PRISMA çalışması değildir. Scopus,
Web of Science ve TR Dizin'den dışa aktarılmış bir sonuç evreni yoktur;
taranan/dışlanan toplam sonuç sayıları bilinmediğinden akış sayıları üretilmedi.
Tam metni açılamayan kaynaklar özet veya indeks düzeyinde işaretlendi.
Yalnız özette görünmeyen bir yöntemin makalede hiç olmadığı ileri sürülmez.
Ekler, bütün kodlar ve deneyler yeniden üretilmedi. Başvuru/makale öncesinde
üniversite erişimiyle tam metin ve atıf zinciri taraması yenilenmelidir.

Prapas çalıştayı, Kondylatos makalesi ve FireCube aynı araştırma ailesidir.
Mesogeos ile onu kullanan model karşılaştırmaları da bağlantılıdır. Veri kümesi
ve onu kullanan makaleler, aynı hipotezin bağımsız tekrarları gibi sayılmadı.
Tonbul–Veraverbeke kaydı DOI içinde 2025 taşısa da yayıncıya göre 2026 yayınıdır.
Ön baskılarda incelenen sürümün durumu kullanıldı; arXiv kaydı hakemli kabul
yerine geçmez.

## Aynı ad altında farklı problemler

| Araştırma görevi | Hedef | Bizim hedefimizle ilişkisi |
|---|---|---|
| Mekânsal yatkınlık | Bir yerin uzun dönem yangına elverişliliği | Zaman sözleşmesi olmadan günlük yeni olay olasılığı değildir |
| Yangın hava tehlikesi | FWI gibi meteorolojik koşul/endeks | Tutuşma veya ilk uydu tespitiyle aynı değişken değildir |
| Aktif yangın olasılığı | Bir hücre-günde aktif tespit görülmesi | Devam eden yangınların tekrar tespitlerini içerebilir |
| Yeni olayın ilk tespiti | T'den sonra ilk kez gözlenen olay | Mevcut proje hedefi; gerçek tutuşma zamanı değildir |
| Yayılım | T'de mevcut yangının sonraki konumu/alanı | Başlangıçta yangın bilgisini kullanır; ayrı görevdir |
| Nihai yanmış alan | Başlamış olayın toplam alanı | Olay öncesi günlük risk ile karıştırılmaz |

Bu ayrım yayınları elemek için değil, karşılaştırmayı doğru kurmak içindir.
Bir yayılım çalışmasının yüksek F1 değerini yeni olay modelimize hedef koymak;
FWI tahmin başarısını yangın olayını tahmin etme başarısı diye sunmak uygun
değildir. Alan/çözünürlük, olay büyüklüğü, sınıf oranı, ölçüt ve veri ayrımı
eşitlenmeden makalelerin puanları yan yana bir liderlik tablosu oluşturmaz.

## En yakın çalışmaların eleştirel karşılaştırması

**Türkiye'de doğrudan ürün benzerliği — FireAId.** Resmî kurum kaydı,
Güney Ege/Batı Akdeniz'de 24 saatlik risk haritası ve kaynak planlamasını
tanımlar. Dolayısıyla “Türkiye'de ilk 24 saatlik yapay zekâ haritası” iddiası
kullanılamaz. Açıklanan başarı oranı kurum beyanıdır; örneklem, hedef ve
bağımsız test koşulları bizim deneyimize eşitlenmeden bilimsel üstünlük
karşılaştırması yapılamaz. Tam rapor PDF'sine erişim sınırlıydı; resmî etki
sayfası ve indekslenen rapor bölümü esas alındı.
[Resmî FireAId kaydı](https://www.weforum.org/impact/artificial-intelligence-wildfire-prediction-and-prevention/) [R08].

**Ertesi gün yerel risk — Apostolakis ve arkadaşları.** Yunanistan için
500 m günlük oluşum sınıflandırması, meteoroloji/yerel özellikler ve karar
desteği incelenmiştir. Eğitimdeki örnekleme ile doğal dengesiz değerlendirme
ayrımı bizim tasarımımıza doğrudan yol gösterir. “Uydu + meteoroloji +
makine öğrenmesi + ertesi gün” bileşimi yeni değildir.
[Kurumsal tam metin](https://publications.beyond-eocenter.eu/DISASTERS/Estimating_Next%20Day_s%20Forest%20Fire%20Risk.pdf) [R03].

**Zamansal derin öğrenme — Kondylatos ve arkadaşları.** Günlük veri küpünde
tabular, zamansal ve uzamsal modeller karşılaştırılmıştır. Pozitif hedef,
o gün başlayan yangının nihai yanmış pikselleridir; yalnız başlangıç hücresi
değildir. İncelenen değerlendirmede negatif örnekleme vardır. Bu hedef ve
oran farkları nedeniyle yayımlanan F1 bizim doğal hücre-gün dağılımımızın
doğrudan başarı beklentisi olamaz.
[GRL tam metin](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2022GL099368) [R04].

**İlk tespit ve olay düzeltmesi — Mesogeos.** EFFIS olay sınırları ve MODIS
hotspot'ları eşleştirilerek ilk gözlenen tarih/başlangıç konumu çıkarılır.
Büyük yangın odaklı görev ve kaynak kapsamı bizim bütün uygun yeni olay
hedefimizden farklıdır. Ancak “ilk tespiti kullanmak”, “hotspot'ları olaya
dönüştürmek” veya “Akdeniz günlük veri küpü” tek başına özgünlük değildir.
[NeurIPS tam metin](https://proceedings.neurips.cc/paper_files/paper/2023/file/9ee3ed2dd656402f954ef9dc37e39f48-Paper-Datasets_and_Benchmarks.pdf) [R05].

**Operasyonel aktif yangın — ECMWF PoF.** Günlük aktif yangın gözlemlerini,
meteoroloji/yakıt/tutuşma bilgileriyle modelleyen mevcut bir sistemdir.
Sistem hedefi aktif tespit içerdiğinden bizim yeni olay ayrımımız ayrıca
önemlidir. Ancak hava tehlikesinden olay olasılığına geçişi veya yanlış
alarmları azaltmayı ilk öneren çalışma olduğumuz söylenemez.
[Birincil makale](https://www.nature.com/articles/s41467-025-58097-7) [R07].

**Aynı il ve aynı ufuk — Mersin çalışması.** Akdagli'nin 2026 yayını,
alan ağırlıklı ERA5 üzerinden ertesi gün yüksek FWI koşulunu modeller.
Hedef meteorolojik endeks eşiğidir; bağımsız yeni yangın kaydı değildir.
Bu çalışma yakın coğrafi/zamansal karşılaştırmadır, fakat farklı hedef
nedeniyle bildirilen başarı bizim yangın etiketi başarımızla eşitlenmez.
[Yayıncı özeti](https://www.nature.com/articles/s41598-026-68923-7) [R09].

**Türkiye'de açıklanabilir haritalama.** Adana/Mersin, İzmir ve Türkiye'nin
yangına yatkın bölgelerinde uzaktan algılama, makine öğrenmesi ve SHAP
çalışmaları bulunur. Bunların incelenen özetleri mekânsal yatkınlığa odaklanır;
bütün tam yöntemler açık olmadığından günlük hedefin yokluğu kesin bir
ispat olarak kullanılmaz. “İzmir'de SHAP” veya “Türkiye'de VIIRS ile model”
iddiası yenilik sayılamaz.
[Iban–Aksu](https://www.mdpi.com/2072-4292/16/15/2842) [R11],
[Tonbul–Veraverbeke](https://link.springer.com/article/10.1007/s00477-025-03136-4) [R12].

**Eksik etiket de daha önce çalışılmıştır.** Song ve arkadaşları algılama
mekanizmasına bağlı eksik etiketleri California yangın örneğinde ele alır;
Shirazi ve arkadaşları pozitif–etiketsiz öğrenme kullanır. “Tespit yok,
yangın yok demek değildir” gerekçesi yerleşik bir sorundur. PU yönteminin
varsayımları ayrıca sağlanmadan bütün bilinmeyenlerden doğru olasılık
elde edildiği ileri sürülemez.
[Song ve arkadaşları](https://arxiv.org/abs/2103.13555) [R21],
[Shirazi ve arkadaşları](https://www.frontiersin.org/journals/earth-science/articles/10.3389/feart.2021.622307/full) [R22].

**Yeni mimari/ölçüt tek başına yeterli değildir.** Becker ve arkadaşları
zamansal modelleri ve açıklamaları karşılaştırır. Gopakumar–Pannozzo'nun
2026 ön baskısı, yayılım görevinde ölçüt seçiminin model sıralamasını
değiştirmesini inceler; Funk'ın ön baskısı bölgesel belirsizlik değerlendirmesi
sunar. Bunlar hakemli sonuçlarla aynı kanıt düzeyinde değildir, fakat yalnız
“kalibrasyon” veya “yanlış alarm ölçümü” söylemiyle yenilik kurulamayacağını
gösterir.
[Becker ve arkadaşları](https://publikationen.bibliothek.kit.edu/1000192822/180149145) [R06],
[Gopakumar–Pannozzo](https://arxiv.org/abs/2609.22191) [R33],
[Funk](https://arxiv.org/abs/2605.03148) [R34].

## Seçilmiş kaynak karşılaştırma matrisi

Tam İngilizce başlık, DOI/URL, yayın durumu, erişim düzeyi ve çalışma ailesi
makine okunur sicildedir. Burada kısa görev ve çıkarım yer alır. Bir indeks/
özet kaydı, tam metin deney denetimi sayılmaz.

| Kimlik / birincil kaynak | Yazar / yıl | Görev / alan | Bu projeye etkisi |
|---|---|---|---|
| [R01](https://doi.org/10.1139/er-2020-0019) | Jain ve ark., 2020 | Alan taraması | Farklı yangın görevlerini ayırır; tek bir genel başarı ölçütü kullanmak uygun değildir. |
| [R02](https://doi.org/10.1016/j.isprsjprs.2025.06.002) | Xu ve ark., 2025 | Alan taraması | Uydu ve çevresel verilerin derin öğrenmede birleştirilmesi yerleşik bir araştırma alanıdır. |
| [R03](https://publications.beyond-eocenter.eu/DISASTERS/Estimating_Next%20Day_s%20Forest%20Fire%20Risk.pdf) | Apostolakis, Girtsou, Giannopoulos, Bartsotas ve Kontoes, 2022 | Günlük yangın oluşumu; Yunanistan, 500 m | Eğitim örneklemesi ile doğal dengesiz değerlendirme ayrılır; günlük karar desteği doğrudan yakın çalışmadır. |
| [R04](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2022GL099368) | Kondylatos ve ark., 2022 | Yeni başlayan yangının nihai yanmış pikselleri; Yunanistan, 1 km | Zamansal ayrım ve çoklu veri vardır; ilk hücre hedefimizle ve doğal sınıf oranımızla sayısal sonuçlar eşdeğer değildir. |
| [R05](https://proceedings.neurips.cc/paper_files/paper/2023/file/9ee3ed2dd656402f954ef9dc37e39f48-Paper-Datasets_and_Benchmarks.pdf) | Kondylatos, Prapas, Camps-Valls ve Papoutsis, 2023 | Akdeniz, günlük 1 km; büyük yangın başlangıcı ve alanı | EFFIS sınırları MODIS ilk tespitleriyle düzeltilir; ilk tespiti kullanmak tek başına yenilik değildir. Küçük yangın kapsamı farklıdır. |
| [R06](https://publikationen.bibliothek.kit.edu/1000192822/180149145) | Becker, Natel ve Nowack, 2026 | Mesogeos üzerinde büyük yangın tehlikesi | 30 günlük geçmiş ve açıklamalar karşılaştırılır; karmaşık model veya SHAP eklemek bağımsız yenilik değildir. |
| [R07](https://www.nature.com/articles/s41467-025-58097-7) | Di Giuseppe, McNorton, Lombardi ve Wetterhall, 2025 | Küresel aktif yangın; ECMWF PoF | Meteoroloji, yakıt ve tutuşma bilgileriyle günlük aktif yangın tahmini yapılır. Aktif tespit hedefi yeni olayın ilk tespitiyle aynı değildir. |
| [R08](https://www.weforum.org/publications/the-next-frontier-in-fighting-wildfires-fireaid-pilot-and-scaling/) | World Economic Forum ve FireAId proje ortakları, 2023 | Türkiye; Güney Ege ve Batı Akdeniz | 24 saatlik risk haritası ve kaynak planlama zaten sunulmuştur. Kurumun başarı oranı bağımsız karşılaştırılabilir ölçüm sayılmaz. |
| [R09](https://www.nature.com/articles/s41598-026-68923-7) | Akdagli, 2026 | Mersin; yüksek FWI koşulu | 2003–2025 meteoroloji serisinde ertesi gün FWI eşiği modellenir; bağımsız yeni yangın olayı hedefi değildir. |
| [R10](https://doi.org/10.1016/j.ecoinf.2022.101647) | Iban ve Sekertekin, 2022 | Adana–Mersin; mekânsal yatkınlık | Uzaktan algılama ve CBS tabanlı yerel yangın yatkınlığı çalışması vardır; günlük ilk olay hedefi özette doğrulanmadı. |
| [R11](https://www.mdpi.com/2072-4292/16/15/2842) | Iban ve Aksu, 2024 | İzmir; mekânsal yatkınlık | MODIS ve SHAP ile yerel açıklanabilir haritalama yapılmıştır; SHAP eklemek özgün katkı olarak sunulamaz. |
| [R12](https://link.springer.com/article/10.1007/s00477-025-03136-4) | Tonbul ve Veraverbeke, 2026 | Türkiye yangına yatkın bölgeleri; VIIRS 2013–2022 | VIIRS, çevresel faktörler ve SHAP bizim kapsamla örtüşür. Özette açık 24 saatlik ilk olay hedefi doğrulanmadı. |
| [R13](https://iforest.sisef.org/contents/?id=ifor4321-016) | Göltaş, Ayberk ve Küçük, 2024 | Güneybatı Türkiye; coğrafi oluşum yatkınlığı | Geçmiş olaylarla MaxEnt ve sonraki dönem konum doğrulaması kullanılır. Günlük zaman sözleşmeli ilk olay tahminiyle görev ayrıdır. |
| [R14](https://www.nature.com/articles/s41598-026-52395-w) | Radhi ve Ibrahim, 2026 | Türkiye FIRMS ve IoT; tespit/tahmin | Sensör tabanlı sınıflandırma ve dengeli örnekleme bulunur. Okunan bölümlerde gelecekteki yeni olay için açık 24 saat sözleşmesi kurulmadı. |
| [R15](https://arxiv.org/abs/2112.02447) | Huot, Hu, Goyal, Sankar, Ihme ve Chen, 2022 | ABD; mevcut yangının ertesi gün yayılımı | Önceden yanan alan girdisiyle yayılım tahmini, henüz başlamamış olayın ilk tespitini tahmin etmekten ayrıdır. |
| [R16](https://papers.nips.cc/paper_files/paper/2023/file/ebd545176bdaa9cd5d45954947bd74b7-Paper-Datasets_and_Benchmarks.pdf) | Gerard, Zhao ve Sullivan, 2023 | ABD; VIIRS ve meteoroloji, devam eden yangın | 375 m yangın görüntüleri ve çoklu veriyle yayılım izlenir. Bulut/duman etiket sorunları belirtilir; yeni olay hedefi değildir. |
| [R17](https://www.ijcai.org/proceedings/2019/0636.pdf) | Radke, Hessler ve Ellsworth, 2019 | Mevcut yangının çevresinde yayılım | CBS ve CNN ile ilerleme tahmini yapılır; yangın başlamadan risk haritası problemimizle aynı etiket değildir. |
| [R18](https://www.nature.com/articles/s41597-025-06271-3) | Zhao, Gerard ve Ban, 2025; ön baskı 2024 | Uydu zaman serisi; tespit, izleme ve tahmin | Çok görevli zaman serisi veri kaydıdır. İncelenen yangın izleme/yayılım hedefleri günlük yeni olayla eşdeğer sayılmaz. |
| [R19](https://arxiv.org/html/2603.09042v1) | Yang, Zafari, Duan ve Swindlehurst, 2026 | WildfireSpreadTS; kısmi gözlem altında yayılım | Eksik gözlemi yeniden kurma ve tahmin yaklaşımı vardır. Eksiklikle çalışmak yeni değildir; bizim ilk olay etiketi sorunumuz farklıdır. |
| [R20](https://www.nature.com/articles/s43247-026-03692-9) | Kang, Lee, Cho ve Im, 2026 | Küresel FWI; 1 derece | ERA5 ve SEAS5 ile ileri FWI tahmini yapılır. Uzun ufukta meteorolojik tehlike, yerel yeni yangın olasılığı değildir. |
| [R21](https://arxiv.org/abs/2103.13555) | Song, Raskutti ve Willett, 2021 | Algılanmayan yangın etiketleri; California örneği | PU-OMM olay ve algılama olasılığını birlikte ele alır. Eksik etiketi modellemek daha önce çalışılmıştır; varsayımlar ayrıca incelenmelidir. |
| [R22](https://www.frontiersin.org/journals/earth-science/articles/10.3389/feart.2021.622307/full) | Shirazi, Wang ve Bondur, 2021 | Güneydoğu Çin; yangına uygun koşullar | Pozitif–etiketsiz öğrenme yaklaşımı kullanılır; negatiflerin belirsizliği bizim projeye özgü keşif değildir. |
| [R23](https://proceedings.mlr.press/v258/teisseyre25a.html) | Teisseyre, Martens, Bekker ve Davis, 2025 | Seçim yanlılığı olan PU öğrenme | Kalibrasyon/karar eşikleri algılanma mekanizmasına bağlıdır; etiketsiz kayıtlar güvenilir negatiflere kendiliğinden dönüşmez. |
| [R24](https://geog.umd.edu/node/10891) | Schroeder, Oliva, Giglio ve Csiszar, 2014 | VIIRS 375 m aktif yangın ürünü | Algoritma ve sensör tespiti temeli; tespit zamanı gerçek tutuşma zamanı kabul edilemez. |
| [R25](https://essd.copernicus.org/articles/11/529/2019/) | Andela ve ark., 2019 | Küresel MODIS yanmış alanından olaylar | Olay gruplaması ve başlangıç çıkarımı vardır; uydu tabanlı olay sınırı bağımsız saha tutuşma kaydı değildir. |
| [R26](https://nsojournals.onlinelibrary.wiley.com/doi/10.1111/ecog.02881) | Roberts ve ark., 2017 | Bağımlı veride doğrulama yöntemi | Rastgele satır ayrımı zamansal/mekânsal genellemeyi olduğundan iyi gösterebilir; bloklu doğrulama metodolojik temeldir. |
| [R27](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0118432) | Saito ve Rehmsmeier, 2015 | Dengesiz sınıflandırma değerlendirmesi | Nadir olay için PR değerlendirmesi önemlidir; accuracy tek başına uygun başarı iddiası değildir. |
| [R28](https://proceedings.mlr.press/v70/guo17a.html) | Guo, Pleiss, Sun ve Weinberger, 2017 | Olasılık kalibrasyonu | Yüksek sınıflandırma başarısı kalibre olasılık demek değildir. Sinir ağı bulguları bütün modeller için otomatik garanti vermez. |
| [R29](https://forest-fire.emergency.copernicus.eu/applications/data-and-services) | Copernicus Emergency Management Service, ECMWF, 2026 | Avrupa yangın hava tehlikesi ve veri hizmetleri | FWI tahmin ve haritaları hazırdır; aynı tarihli ürün/sürüm karşılaştırılmalı, FWI olay olasılığı diye adlandırılmamalıdır. |
| [R30](https://arxiv.org/abs/2111.02736) | Prapas ve ark., 2021 | Günlük yangın tehlikesi | Kondylatos 2022 ile ilişkili araştırma ailesidir; bağımsız tekrar deney gibi sayılmaz. |
| [R31](https://zenodo.org/records/6475592) | Prapas, Kondylatos ve Papoutsis, 2022 | Yunanistan günlük 1 km veri küpü | Kondylatos/Prapas çalışma ailesinin veri kaydıdır; veri küpü oluşturmak tek başına özgünlük değildir. |
| [R32](https://ieeexplore.ieee.org/document/10149031/) | Shams Eddin, Roscher ve Gall, 2023 | FireCube; konuma uyarlanmış normalizasyon | Model mimarisi düzeyinde iyileştirmeler zaten vardır; farklı mimari etiketi özgün bilimsel sonuç yerine geçmez. |
| [R33](https://arxiv.org/abs/2609.22191) | Gopakumar ve Pannozzo, 2026 | WildfireSpreadTS; operasyonel ölçüt karşılaştırması | AP ve eşik tabanlı ölçütlerin model sıralamasını değiştirmesi incelenir. Yanlış alarm odaklı değerlendirme tek başına yeni değildir. |
| [R34](https://arxiv.org/abs/2605.03148) | Funk, 2026 | WildfireSpreadTS; bölgesel belirsizlik ve kalibrasyon | Yangın çevresinde değerlendirme ve belirsizlik ele alınır; bilinmeyen alanı göstermek veya kalibrasyon tek başına yenilik değildir. |

## Kullanılmayacak özgünlük iddiaları

- İlk yapay zekâ ile yangın tahmini, ilk 24 saat tahmini veya ilk Türkiye ürünü.
- İlk uydu–meteoroloji birleşimi, ilk VIIRS veri kümesi ya da ilk SHAP haritası.
- İlk olay gruplaması, ilk tespit etiketi, ilk eksik gözlem farkındalığı.
- İlk kalibrasyon, ilk mekânsal doğrulama veya ilk yanlış alarm değerlendirmesi.
- Bir makaledeki accuracy değerini geçince bütün literatürden üstün olma.
- Yeni bir dashboard, model adı veya bulut altyapısını araştırma bulgusu sayma.

Bu bileşenler gereksiz değildir; iyi araştırmanın araçlarıdır. Özgünlük,
hangi sorunun hangi karşılaştırmayla çözüldüğü ve sonucun ne kadar
genellenebildiği üzerinden gerekçelendirilmelidir.

## Önerilen katkı: ölçülebilir yöntem ve yerel benchmark

**Birinci öncelik: etiket güvenilirliğinin sonuç üzerindeki etkisi.**
Olay gruplaması, sınır günleri ve gözlem yeterliliği için gerekçeli sürümler
karşılaştırılmalı. Aynı incelenmiş değerlendirme çekirdeğinde model başarısı,
dahil edilen hücre-gün kapsamı ve örneklem bileşimi birlikte ölçülmeli.
Seçim yanlılığı yüzünden daha kolay örnekleri tutmanın etkisi, yöntem
iyileşmesi diye sunulmamalı. Yeni protokol olmadan bilinmeyenler sıfır yapılmaz.

**İkinci öncelik: aynı bütçede kaç yeni olay bulunabilir?** İncelenebilecek
günlük hücre sayısı sabitken olay yakalama, yanlış uyarı ve harita alanı
birlikte raporlanmalı. Kapasite düzeyi ve eşiği doğrulamada seçilmeli.
Bu, ürünün karar desteğiyle bağlantısını kurar; gerçek operasyonel kullanıcı
faydası ayrıca kullanıcı/kurum değerlendirmesi gerektirir.

**Üçüncü öncelik: maliyetli özelliklerin gerçek ek değeri.** Meteoroloji,
arazi/örtü ve NDVI/NDMI grupları aynı hedef, aynı kayıtlar ve aynı ayrımlarla
çıkarılıp eklenmeli. Uydu verisinin artısı yoksa bu sonuç saklanmamalı;
daha sade modelin yeterliliği de araştırma bulgusudur.

**Dördüncü öncelik: il/yıl aktarımı ve kalibrasyon.** Training içinde bölgesel
blok ve ileri yıl deneyleri yapılmalı; olasılık hatası, mevsim/il bazlı
başarısızlıklar ve güven aralıkları raporlanmalı. SHAP gerekçelendirmeyi
destekler; model açıklaması nedensel kanıt değildir.

Bu dört önceliğin tamamı yeni bir genel algoritma iddiası değildir.
Potansiyel katkı, dört ilde aynı zaman sözleşmesi altında **olay ve gözlem
politikalarının etkisini, veri kapsamı kaybını ve uyarı yükünü birlikte
ölçen tekrarlanabilir deneydir**. Bu tarama aynı tasarımın dünyada hiç
yapılmadığını kanıtlamaz. Deney başlamadan en yakın kaynakların ekleri/kodları
ve atıf zincirleri incelenip katkı cümlesi daraltılmalıdır.

## Mevcut projeye etkisi ve sınırlar

Uydu kuyruğu ile bitki örtüsü verileri bu sorular için aday veri sağlar.
Hesaplama bitmesi, gözlem yeterliliği veya güvenilir negatif etiketi otomatik
kanıtlamaz. Güncel yerel/uzak ilerleme ayrı [STATUS](../STATUS.md) kaydındadır.

5 km tahmin hücresi, 375 m sensör pikseli veya ekran zoom düzeyiyle aynı şey
değildir. Son ürün ayrıntılı uydu taban haritası gösterebilir; model riskinin
5 km çözünürlüğü ve bilinmeyen alanlar görünür kalmalıdır. Harita bu
literatür sorusunu çözmez, kabul edilmiş modeli sunar.

Mevcut ERA5-Land geçmiş deneyleri operasyonel hava tahmini değildir.
Gelecek hava koşullarının tahmin anında yayımlanmış arşivi olmadan gerçek
zamanlı 24 saat olay tahmini iddiası kurulmaz. Retrospektif benchmark ve
operasyonel ürün iki ayrı kabul aşamasıdır. Yol/yerleşim/yıldırım kaynakları
yararlı olabilir; mevcut aday setinde yoklarsa kullanılmış gibi anlatılmaz,
kapsam ve erişim değerlendirmesinden sonra önerilir.

Eğitim **2018–2023**, doğrulama **2024**, kapalı final test **2025** korunur.
Kaynaklarda 2025 sonuçlarının okunması, bizim 2025 verimizin açılması değildir.
`daily_observation_status=unknown`, `negative_label_permitted=false` ve
`model_ready=false` bu belgeyle değiştirilmez. Çalışan VM/paket, kod,
hash bağlı yöntem ve checkpoint'lere müdahale yapılmadı.

## Sonraki araştırma kararı

[Deney protokolü](ARTICLE_RESEARCH_PROTOCOL_2026-10-12.md) hipotezleri,
karşılaştırmaları, metrikleri ve kabul kapılarını ayrıntılandırır.
[Danışman özeti](ADVISOR_LITERATURE_BRIEF_2026-10-12.md) görüşmeye götürülebilir.

Öncelik yeni mimari geliştirmek değil, etiket denetimi için bağımsız/uzman
incelenmiş bir referansın uygulanabilirliğini belirlemektir. OGM olay kayıtları
gibi kaynaklar erişim/izin gerektirebilir; elde edilmiş sayılmaz. EFFIS sınırları
yardımcı olabilir ama küçük olay kapsamını veya gerçek tutuşma saatini otomatik
doğrulamaz. Bu kapı çözülemezse çalışma kapsamı gözlenen tespitlerin sıralanması
ve belirsizlik analizi olarak daraltılmalıdır; kesin yangın oluşma olasılığı
başarı iddiası yapılmamalıdır.

Makale için çalışma başlığı önerisi:
**“Gözlem ve Olay Tanımındaki Belirsizliğin 24 Saatlik İlk Yangın Tespiti
Tahminine Etkisi: Türkiye'nin Dört İlinde Bir Karşılaştırma”**.
Bu, proje/ürün adını değiştiren karar değildir. Makale yazılabilirliği,
özgünlük gerekçesi, veri/etiket kalitesi ve deney kanıtlarıyla danışman
tarafından değerlendirilecek; yayın veya destek garantisi verilmez.
