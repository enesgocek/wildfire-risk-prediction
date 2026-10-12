# Literatür kaynaklarının varlık ve yazar denetimi

Kontrol tarihi: **12 Ekim 2026**. Kapsam: önceki literatür sicilindeki **34 kayıt**.
Amaç, hayalî başlık/yazar veya yanlış yayın kimliği üzerinden proje kararı
verilmesini önlemek. Bu belge önceki [incelemenin](LITERATURE_REVIEW_2026-10-12.md)
ikinci kontrolüdür; yeni model deneyi veya bağımsız bilimsel tekrar değildir.

## Sonuç

34 kaydın tamamı için gerçek bir yayın, ön baskı, veri kümesi, resmî ürün
veya kurum kaydı bulundu. Başlık, bildirilen yazar/kurum ve yayın kimliği
eşleşmelerinde **uydurma kayıt veya başka makaleye ait DOI saptanmadı**.

- 23 kaydın dergi/konferans DOI kimliği Crossref ile eşleşti.
- Bunlara ek yedi kayıt DataCite DOI siciliyle eşleşti; toplam **30 kayıt**
  kayıt sistemlerinden de kontrol edildi. Bazılarında her iki sicil kullanıldı.
- Dört kayıt (R08, R16, R23, R29) resmî kurum/konferans/ürün sayfaları ve
  ikinci kayıt kanalıyla denetlendi; DOI olmaması hayalî çalışma demek değildir.
- **İki yayın durumu güncellendi, üç DOI tamamlandı, bir çalıştay kabul
  kaydının kanıt düzeyi daha açık yazıldı.** İlk inceleme kusursuz kabul edilmedi.

Bu sonuç, 34 ayrı orijinal yangın tahmin projesi olduğu anlamına gelmez.
Liste derlemeler, yöntem çalışmaları, veri setleri, kurumsal belgeler ve
ön baskılar da içerir. Her birinin rolü kaynak sicilinde ayrıdır.

## İkinci kontrol nasıl yapıldı?

1. Sicildeki DOI'ler açık Crossref API'ye soruldu. Başlık, tam yazar listesi,
   yayıncı/dergi, tarih ve varsa kamusal ORCID bilgisi alındı.
2. arXiv/Zenodo kayıtları DataCite metadata ile eşleştirildi. FireCube için
   ayrıca gerçek Zenodo kayıt API'si ve bir kamusal dosya kaydı görüldü;
   büyük veri dosyası indirilmedi.
3. DOI metadata, yayıncı/konferans veya yazar/kurum kaydıyla karşılaştırıldı.
   Başlık eşleşmesinde büyük/küçük harf, aksan ve tire farkları ayrıldı.
   Yazar soyadları/ortak yazarlar kontrol edildi; kısaltılmış “ve ark.”
   ifadelerinin tam listeleri aşağıya eklendi.
4. FireAId için WEF yanında Koç Holding duyurusu; ECMWF için makale yanında
   kurumun yazarları isimlendiren duyurusu; başka örneklerde KIT, KTH,
   Bonn, ICS PAS veya yazar yayın/depo kayıtları kullanıldı.
5. Yayın durumunu güncelleyen bilgiler önceki kayıtları sessizce değiştirmek
   yerine bu tarihli düzeltme listesine bağlandı.

Crossref/DataCite, yayıncı ve yazarların metadata bildirimlerini tutar.
İki kayıt kanalı, aynı deneyi iki bağımsız ekibin doğruladığı anlamına
gelmez. “Gerçek kişi” kontrolü, akademik kayıtta bu yazarın adıyla çalışmanın
yer alması ve varsa kurum/ORCID bağlantısıyla desteklenmesidir; biyografik
kimlik denetimi veya bütün yazarların her deney adımını bizzat yaptığının
incelemesi değildir. İsim benzerliği tek başına kullanılmadı.

İlk API okumalarında iki hız sınırı yanıtı vardı; sonraki sorgular başarılı
oldu. Bazı yayıncı sayfaları erişim sınırı/çerez yönlendirmesi verdi; bunlarda
yayıncı indeks kaydı veya kurumsal kopya kullanıldı. Sayfanın araçla
açılamaması, makalenin bulunmadığı diye yorumlanmadı.

## Açık düzeltmeler ve tamamlamalar

| Kayıt | Önceki bilgi | İkinci kontrolde doğrulanan bilgi |
|---|---|---|
| R18 — TS-SatFire | 2024 arXiv sürümü; dergi durumu doğrulanmamıştı | **Scientific Data**, 19 Kasım 2025; Yu Zhao, Sebastian Gerard, Yifang Ban; DOI 10.1038/s41597-025-06271-3 |
| R32 — Location-Aware Adaptive Normalization | arXiv sürümü; yayın yeri doğrulanmamıştı | **IEEE TGRS 61**, 2023; Mohamad Hakam Shams Eddin, Ribana Roscher, Juergen Gall; DOI 10.1109/TGRS.2023.3285401 |
| R15 — Next Day Wildfire Spread | Dergi sürümünün DOI alanı boştu | DOI **10.1109/TGRS.2022.3192974** |
| R17 — FireCast | DOI alanı boştu | DOI **10.24963/ijcai.2019/636** |
| R21 — Eksik etiket yöntemi | Konferans kaydı vardı; DOI alanı boştu | DOI **10.1109/SSP49050.2021.9513750** |
| R30 — Günlük tehlike çalıştayı | Kabul edilmiş çalıştay olarak kaydedilmişti | Kabul bilgisi arXiv **Comments** alanındaki yazar bildirimidir; ayrı konferans programı kontrol edilmedi |

R18'de 2024 ön baskı yılı silinmedi; `preprint_year` ile korundu, ana
bibliyografik yıl hakemli yayın için 2025 yapıldı. R32'nin ön baskısı 2022,
incelenen sonraki sürümü ve hakemli yayını 2023'tür. Ön baskı URL'leri korunur.
R05 için NeurIPS'teki **Spyridon** ve arXiv'deki **Spyros Kondylatos** ad
varyantı ayrıca kaydedildi; başlık ve ortak yazar listesi eşleşir.
R29 tek bir makale başlığı değildir: iki resmî servis sayfası için sicilde
kullanılmış birleşik ürün etiketi olarak açıklandı.

Doğrudan yayın kanıtları:
[TS-SatFire yayıncı kaydı](https://www.nature.com/articles/s41597-025-06271-3),
[LOAN IEEE kaydı](https://ieeexplore.ieee.org/document/10149031/),
[LOAN Bonn yayın listesi](https://rs.ipb.uni-bonn.de/publications/index.html).

## Projenin gerçekten uygulanmasına ilişkin somut örnekler

Bibliyografik kayıt dışında görülebilen bazı dayanaklar:

- **FireAId:** [WEF](https://www.weforum.org/impact/artificial-intelligence-wildfire-prediction-and-prevention/)
  ve [Koç Holding](https://www.koc.com.tr/medya-merkezi/haberler/2023/koc-holding-orman-yanginlariyla-mucadele-projesiyle-davos-zirvesine-damga-vurdu)
  aynı pilotu kurumsal olarak duyurur. Bunlar bağımsız performans raporu değildir.
- **Yunanistan günlük risk çalışması:** [BEYOND hizmeti](https://riskmap.beyond-eocenter.eu/)
  ilgili makaleyi referanslayan gerçek araştırma ekibi hizmet kaydıdır.
- **ECMWF:** [Kurum duyurusu](https://www.ecmwf.int/en/about/media-centre/news/2025/scientists-present-new-ml-tool-improved-fire-prediction)
  Di Giuseppe, McNorton, Lombardi ve Wetterhall'u makalenin yazarları olarak isimlendirir.
- **WildfireSpreadTS:** [Resmî NeurIPS kaydı](https://papers.nips.cc/paper_files/paper/2023/hash/ebd545176bdaa9cd5d45954947bd74b7-Abstract-Datasets_and_Benchmarks.html)
  ile [yazarın deney deposu](https://github.com/SebastianGer/WildfireSpreadTS)
  aynı çalışmayı gösterir. Kodun varlığı bu denetimde deneyin yeniden çalıştırıldığı anlamına gelmez.
- **Becker/Natel/Nowack:** [KIT kurumsal kaydı](https://publikationen.bibliothek.kit.edu/1000192822)
  çalışmayı, yazarları ve kurum birimlerini birlikte listeler.
- **Teisseyre ve arkadaşları:** [PMLR](https://proceedings.mlr.press/v258/teisseyre25a.html)
  ve [ICS PAS yazar yayın listesi](https://home.ipipan.waw.pl/p.teisseyre/PUBLICATIONS/index.html)
  başlık/yazar/yıl eşleşmesini destekler.

## 34 kaydın yazar ve kanıt tablosu

“Kayıt” kaynak/yayıncı/yazar kaydına; “Eşleştirme” ikinci metadata veya kurum
kanalına gider. API bağlantıları makine okunur JSON açabilir. DOI'nin çalışma
tipi de kontrol edilmiştir: arXiv DOI'si hakemli dergi DOI'si sayılmaz.
Ayrıntılı ek URL'ler [makine okunur denetimdedir](literature_identity_audit_2026-10-12.json).

| Kayıt | Doğrulanan yazar / kurum | Kimlik / yayın | Birincil kayıt | İkinci kayıt kanalı |
|---|---|---|---|---|
| R01 | Piyush Jain; Sean C.P. Coogan; Sriram Ganapathi Subramanian; Mark Crowley; Steve Taylor; Mike D. Flannigan | 10.1139/er-2020-0019; 2020 | [Kayıt](https://doi.org/10.1139/er-2020-0019) | [Eşleştirme](https://api.crossref.org/works/10.1139%2Fer-2020-0019) |
| R02 | Zhengsen Xu; Jonathan Li; Sibo Cheng; Xue Rui; Yu Zhao; Hongjie He; Haiyan Guan; Aryan Sharma; Matthew Erxleben; Ryan Chang; Lincoln Linlin Xu | 10.1016/j.isprsjprs.2025.06.002; 2025 | [Kayıt](https://doi.org/10.1016/j.isprsjprs.2025.06.002) | [Eşleştirme](https://api.crossref.org/works/10.1016%2Fj.isprsjprs.2025.06.002) |
| R03 | Alexis Apostolakis; Stella Girtsou; Giorgos Giannopoulos; Nikolaos S. Bartsotas; Charalampos Kontoes | 10.3390/rs14051222; 2022 | [Kayıt](https://publications.beyond-eocenter.eu/DISASTERS/Estimating_Next%20Day_s%20Forest%20Fire%20Risk.pdf) | [Eşleştirme](https://api.crossref.org/works/10.3390%2Frs14051222) |
| R04 | Spyros Kondylatos; Ioannis Prapas; Michele Ronco; Ioannis Papoutsis; Gustau Camps‐Valls; María Piles; Miguel‐Ángel Fernández‐Torres; Nuno Carvalhais | 10.1029/2022gl099368; 2022 | [Kayıt](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2022GL099368) | [Eşleştirme](https://api.crossref.org/works/10.1029%2F2022GL099368) |
| R05 | Kondylatos, Spyros; Prapas, Ioannis; Camps-Valls, Gustau; Papoutsis, Ioannis | 10.48550/arxiv.2306.05144; 2023 | [Kayıt](https://proceedings.neurips.cc/paper_files/paper/2023/file/9ee3ed2dd656402f954ef9dc37e39f48-Paper-Datasets_and_Benchmarks.pdf) | [Eşleştirme](https://api.datacite.org/dois/10.48550%2FarXiv.2306.05144) |
| R06 | Pauline Becker; Carolina Natel; Peer Nowack | 10.1088/3049-4753/ae5aa0; 2026 | [Kayıt](https://publikationen.bibliothek.kit.edu/1000192822/180149145) | [Eşleştirme](https://api.crossref.org/works/10.1088%2F3049-4753%2Fae5aa0) |
| R07 | Francesca Di Giuseppe; Joe McNorton; Anna Lombardi; Fredrik Wetterhall | 10.1038/s41467-025-58097-7; 2025 | [Kayıt](https://www.nature.com/articles/s41467-025-58097-7) | [Eşleştirme](https://api.crossref.org/works/10.1038%2Fs41467-025-58097-7) |
| R08 | World Economic Forum; Koç Holding / KoçDigital; Deloitte | World Economic Forum report / official impact page; 2023 | [Kayıt](https://www.weforum.org/publications/the-next-frontier-in-fighting-wildfires-fireaid-pilot-and-scaling/) | [Eşleştirme](https://www.koc.com.tr/medya-merkezi/haberler/2023/koc-holding-orman-yanginlariyla-mucadele-projesiyle-davos-zirvesine-damga-vurdu) |
| R09 | Ali Akdagli | 10.1038/s41598-026-68923-7; 2026 | [Kayıt](https://www.nature.com/articles/s41598-026-68923-7) | [Eşleştirme](https://api.crossref.org/works/10.1038%2Fs41598-026-68923-7) |
| R10 | Muzaffer Can Iban; Aliihsan Sekertekin | 10.1016/j.ecoinf.2022.101647; 2022 | [Kayıt](https://doi.org/10.1016/j.ecoinf.2022.101647) | [Eşleştirme](https://api.crossref.org/works/10.1016%2Fj.ecoinf.2022.101647) |
| R11 | Muzaffer Can Iban; Oktay Aksu | 10.3390/rs16152842; 2024 | [Kayıt](https://www.mdpi.com/2072-4292/16/15/2842) | [Eşleştirme](https://api.crossref.org/works/10.3390%2Frs16152842) |
| R12 | Hasan Tonbul; Sander Veraverbeke | 10.1007/s00477-025-03136-4; 2026 | [Kayıt](https://link.springer.com/article/10.1007/s00477-025-03136-4) | [Eşleştirme](https://api.crossref.org/works/10.1007%2Fs00477-025-03136-4) |
| R13 | M Göltas; H Ayberk; O Kücük | 10.3832/ifor4321-016; 2024 | [Kayıt](https://iforest.sisef.org/contents/?id=ifor4321-016) | [Eşleştirme](https://api.crossref.org/works/10.3832%2Fifor4321-016) |
| R14 | Ahmed A. Radhi; Abdullahi A. Ibrahim | 10.1038/s41598-026-52395-w; 2026 | [Kayıt](https://www.nature.com/articles/s41598-026-52395-w) | [Eşleştirme](https://api.crossref.org/works/10.1038%2Fs41598-026-52395-w) |
| R15 | Fantine Huot; R. Lily Hu; Nita Goyal; Tharun Sankar; Matthias Ihme; Yi-Fan Chen | 10.1109/tgrs.2022.3192974; 2022 | [Kayıt](https://arxiv.org/abs/2112.02447) | [Eşleştirme](https://api.crossref.org/works/10.1109%2FTGRS.2022.3192974) |
| R16 | Sebastian Gerard; Yu Zhao; Josephine Sullivan | NeurIPS Datasets and Benchmarks; 2023 | [Kayıt](https://papers.nips.cc/paper_files/paper/2023/file/ebd545176bdaa9cd5d45954947bd74b7-Paper-Datasets_and_Benchmarks.pdf) | [Eşleştirme](https://papers.nips.cc/paper_files/paper/2023/hash/ebd545176bdaa9cd5d45954947bd74b7-Abstract-Datasets_and_Benchmarks.html) |
| R17 | David Radke; Anna Hessler; Dan Ellsworth | 10.24963/ijcai.2019/636; 2019 | [Kayıt](https://www.ijcai.org/proceedings/2019/0636.pdf) | [Eşleştirme](https://api.crossref.org/works/10.24963%2Fijcai.2019%2F636) |
| R18 | Yu Zhao; Sebastian Gerard; Yifang Ban | 10.1038/s41597-025-06271-3; 2025 | [Kayıt](https://www.nature.com/articles/s41597-025-06271-3) | [Eşleştirme](https://api.datacite.org/dois/10.48550%2FarXiv.2412.11555) |
| R19 | Yang, Chen; Zafari, Mehdi; Duan, Ziheng; Swindlehurst, A. Lee | 10.48550/arxiv.2603.09042; 2026 | [Kayıt](https://arxiv.org/html/2603.09042v1) | [Eşleştirme](https://api.datacite.org/dois/10.48550%2FarXiv.2603.09042) |
| R20 | Yoojin Kang; Sihyun Lee; Dongjin Cho; Jungho Im | 10.1038/s43247-026-03692-9; 2026 | [Kayıt](https://www.nature.com/articles/s43247-026-03692-9) | [Eşleştirme](https://api.crossref.org/works/10.1038%2Fs43247-026-03692-9) |
| R21 | Hyebin Song; Garvesh Raskutti; Rebecca Willett | 10.1109/ssp49050.2021.9513750; 2021 | [Kayıt](https://arxiv.org/abs/2103.13555) | [Eşleştirme](https://api.crossref.org/works/10.1109%2FSSP49050.2021.9513750) |
| R22 | Zeeshan Shirazi; Lei Wang; Valery G. Bondur | 10.3389/feart.2021.622307; 2021 | [Kayıt](https://www.frontiersin.org/journals/earth-science/articles/10.3389/feart.2021.622307/full) | [Eşleştirme](https://api.crossref.org/works/10.3389%2Ffeart.2021.622307) |
| R23 | Paweł Teisseyre; Timo Martens; Jessa Bekker; Jesse Davis | AISTATS / PMLR 258; 2025 | [Kayıt](https://proceedings.mlr.press/v258/teisseyre25a.html) | [Eşleştirme](https://home.ipipan.waw.pl/p.teisseyre/PUBLICATIONS/index.html) |
| R24 | Wilfrid Schroeder; Patricia Oliva; Louis Giglio; Ivan A. Csiszar | 10.1016/j.rse.2013.12.008; 2014 | [Kayıt](https://geog.umd.edu/node/10891) | [Eşleştirme](https://api.crossref.org/works/10.1016%2Fj.rse.2013.12.008) |
| R25 | Niels Andela; Douglas C. Morton; Louis Giglio; Ronan Paugam; Yang Chen; Stijn Hantson; Guido R. van der Werf; James T. Randerson | 10.5194/essd-11-529-2019; 2019 | [Kayıt](https://essd.copernicus.org/articles/11/529/2019/) | [Eşleştirme](https://api.crossref.org/works/10.5194%2Fessd-11-529-2019) |
| R26 | David R. Roberts; Volker Bahn; Simone Ciuti; Mark S. Boyce; Jane Elith; Gurutzeta Guillera‐Arroita; Severin Hauenstein; José J. Lahoz‐Monfort; Boris Schröder; Wilfried Thuiller; David I. Warton; Brendan A. Wintle; Florian Hartig; Carsten F. Dormann | 10.1111/ecog.02881; 2017 | [Kayıt](https://nsojournals.onlinelibrary.wiley.com/doi/10.1111/ecog.02881) | [Eşleştirme](https://api.crossref.org/works/10.1111%2Fecog.02881) |
| R27 | Takaya Saito; Marc Rehmsmeier | 10.1371/journal.pone.0118432; 2015 | [Kayıt](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0118432) | [Eşleştirme](https://api.crossref.org/works/10.1371%2Fjournal.pone.0118432) |
| R28 | Guo, Chuan; Pleiss, Geoff; Sun, Yu; Weinberger, Kilian Q. | 10.48550/arxiv.1706.04599; 2017 | [Kayıt](https://proceedings.mlr.press/v70/guo17a.html) | [Eşleştirme](https://api.datacite.org/dois/10.48550%2FarXiv.1706.04599) |
| R29 | Copernicus Emergency Management Service / JRC; ECMWF | Copernicus / ECMWF official service documentation; 2026 | [Kayıt](https://forest-fire.emergency.copernicus.eu/applications/data-and-services) | [Eşleştirme](https://confluence.ecmwf.int/spaces/CEMS/pages/382667784/CEMS-Fire%2BData%2Baccess) |
| R30 | Prapas, Ioannis; Kondylatos, Spyros; Papoutsis, Ioannis; Camps-Valls, Gustau; Ronco, Michele; Fernández-Torres, Miguel-Ángel; Guillem, Maria Piles; Carvalhais, Nuno | 10.48550/arxiv.2111.02736; 2021 | [Kayıt](https://arxiv.org/abs/2111.02736) | [Eşleştirme](https://api.datacite.org/dois/10.48550%2FarXiv.2111.02736) |
| R31 | Prapas, Ioannis; Kondylatos, Spyros; Papoutsis, Ioannis | 10.5281/zenodo.6475592; 2022 | [Kayıt](https://zenodo.org/records/6475592) | [Eşleştirme](https://api.datacite.org/dois/10.5281%2Fzenodo.6475592) |
| R32 | Mohamad Hakam Shams Eddin; Ribana Roscher; Juergen Gall | 10.1109/tgrs.2023.3285401; 2023 | [Kayıt](https://ieeexplore.ieee.org/document/10149031/) | [Eşleştirme](https://api.datacite.org/dois/10.48550%2FarXiv.2212.08208) |
| R33 | Gopakumar, Arin; Pannozzo, Marco | 10.48550/arxiv.2609.22191; 2026 | [Kayıt](https://arxiv.org/abs/2609.22191) | [Eşleştirme](https://api.datacite.org/dois/10.48550%2FarXiv.2609.22191) |
| R34 | Funk, Jonas V. | 10.48550/arxiv.2605.03148; 2026 | [Kayıt](https://arxiv.org/abs/2605.03148) | [Eşleştirme](https://api.datacite.org/dois/10.48550%2FarXiv.2605.03148) |

## Bu kontrolün doğrulamadığı şeyler

- Bütün deney sonuçlarının bağımsız yeniden üretimi, saha faydası veya veri doğruluğu.
- Kurumların bildirdiği başarı yüzdelerinin bizim hedefimizle karşılaştırılabilirliği.
- Ön baskıların hakemli kabulü: R19/R33/R34 için kabul doğrulanmadı.
- Bütün çalışmaları bizim yeni olay/24 saat hedefimizle aynı problem sayma.
- Projemizin otomatik olarak özgün olduğu, başarılı olacağı veya yayın kabulü alacağı.

Bu nedenle en yakın hakemli çalışmalar ve gerçek kurum uygulamaları
araştırma yönünü gerekçelendirmek için kullanılabilir. Ön baskılar ayrı
kanıt düzeyinde tutulur. Önceki etiket, ayrım ve bağımsız referans kapıları
bu bibliyografik kontrolle açılmaz.

## Yerel kayıt ve denetim kapsamı

Ham kamu metadata kontrolleri `outputs/reports/literature/2026-10-12/`
altında tutulur: `crossref_identity_check.json`,
`registry_details_identity_check.json`, `publication_status_corrections.json`
ve `zenodo_identity_check.json`. Metadata dosyaları özel proje verisi
içermez; Git'e yalnız küçük kaynak/denetim belgeleri alınır.

[Kaynak sicili](literature_sources_2026-10-12.json) ve
[ilk arama kaydı](literature_search_log_2026-10-12.json) birlikte kullanılır.
İkinci kontrol canlı VM/kuyruk veya bilimsel üretim değişikliği değildir.
