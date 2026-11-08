# İzmir, Muğla ve Mersin için olay saati ve konum incelemesi — 8 Kasım 2026

Üç ilde yayımlanmış yangın başlangıçları, iki ayrı konum referansıyla
yerel VIIRS aday kataloğunda tarandı. Köy, koy kıyısı, mevki ve araştırma
alanı koordinatları kaynaklarındaki anlamlarıyla saklandı. Her vaka
için iki konumun karşılaştırılması, koordinat seçiminin aynı olay için
çıkarımı ne kadar değiştirdiğini ölçmeyi amaçlar.

## Kaynak saatleri ve konumlar

- **İzmir, Tırazlı, 18 Ağustos 2019.** Saha haberi yaklaşık 13.00
  Türkiye saati bildiriyor. OGM açıklaması olay gününü destekliyor.
  MGM çalışması köy koordinatını veriyor. Diğer makalenin koordinatı
  ise yanmış alan araştırmasındaki çalışma alanını tanımlıyor. İki
  referans noktası 9,17 km uzaklıkta. MGM'nin 10.30 UTC kaydı MSG
  görüntüsünde yangın etkisinin belirginleştiği zamandır.
  [AA saha haberi](https://aa.com.tr/tr/turkiye/izmirdeki-orman-yangininin-nedeni-arastiriliyor/1562221) · [OGM](https://www.ogm.gov.tr/tr/haberler/izmir-karabaglar-yeniden-ormanlastiriliyor) · [MGM çalışması](https://www.mgm.gov.tr/FILES/genel/makale/izmirtirazli.pdf) · [Yanmış alan makalesi, bölüm 2.1](https://dergipark.org.tr/tr/download/article-file/2025556).
- **Muğla, Marmaris, 21 Haziran 2022.** OGM yaklaşık 20.02 başlangıç
  ve 20.10 ilk müdahale bildiriyor. Valilik yaklaşık 20.00 veriyor.
  GEKA envanterindeki iki Küfre Koyu kıyı noktası arama için kullanıldı.
  Noktalar 488 m aralıklı. Saha haberinde başlangıç alanının adli
  incelemeyle bulunduğu bildiriliyor. İncelenen haberde bu konumun
  koordinatı verilmedi. [OGM](https://www.ogm.gov.tr/tr/haberler/marmaris-orman-yangiyla-mucadelemiz-tum-hiziyla-devam-ediyor) · [Muğla Valiliği](https://www.mugla.gov.tr/marmaris-orman-yangini-basin-aciklamasi2) · [GEKA envanteri, satır 35](https://geka.gov.tr/uploads/pages_v/marmaris-deniz-turizmi-envanteri-2013.pdf) · [AA saha haberi](https://www.aa.com.tr/tr/gundem/marmaristeki-yanginin-basladigi-alani-hassas-burnuyla-kadro-tespit-etti/2621994).
- **Mersin, Gülnar, 7 Eylül 2022.** Bakanlık 07.13 başlangıç ve
  07.20 ilk müdahale bildiriyor. Belediye yaklaşık 07.30 veriyor.
  Saha incelemesinde Karadere mevkii belirtiliyor. Karadere mevki
  temsili ve Büyükeceli mahalle merkezi iki ayrı nokta olarak kullanıldı.
  Aralarında 4,19 km var. [Bakanlık](https://www.tarimorman.gov.tr/Haber/5402/Soma-Ve-Gulnardaki-Orman-Yanginlari-Kontrol-Altinda) · [Belediye](https://www.mersin.bel.tr/haber/buyuksehir-ekipleri-gulnarda-gorev-basinda-1662623158) · [TMMOB saha raporu](https://www.tmmob.org.tr/icerik/tmmob-mersin-ikk-orman-yangini-raporu) · [Karadere mevkii](https://mapcarta.com/28061940) · [Büyükeceli merkezi](https://harita.org/mersin/gulnar/buyukeceli/).

## Yerel katalog karşılaştırması

Başlangıç saatleri UTC'ye çevrildi. UTC 00.00 tahmini için aynı
`(T,T+24h]` ve onu izleyen pencere ayrı sayıldı. Başlangıç öncesi
ve sonrası kayıtlar ayrıldı. Her konum için WGS84 mesafesiyle 2, 5
ve 10 km yarıçaplar kullanıldı. Sayılar seçili katalog tespitlerine
aittir. Aynı tespit iki konumun çevresinde bulunabileceğinden
sütunlar toplanmaz.

| Vaka | Kullanılan UTC başlangıç | 2 km içinde aynı gün başlangıç sonrası, konum A / B | 2 km içinde ertesi pencere, konum A / B |
| --- | --- | ---: | ---: |
| Tırazlı, köy / çalışma alanı | 18 Ağustos 10.00, yaklaşık | 0 / 28 | 1 / 38 |
| Marmaris, iki kıyı noktası | 21 Haziran 17.02, yaklaşık | 1 / 2 | 8 / 11 |
| Gülnar, Karadere / Büyükeceli | 7 Eylül 04.13 | 45 / 39 | 2 / 0 |

Tırazlı köyü için aynı gün 2 km içinde kayıt sıfır, 5 km içinde 48.
Çalışma alanı noktasında 2 km içindeki ilk kayıt 23.34 UTC. Bu fark
başlangıç hücresi yerine çalışma alanı koordinatı kullanılmasının
sonucu değiştirebildiğini gösteriyor. Marmaris'te 2 km çevrede iki
referansın da ilk aynı gün kaydı 23.22 UTC. Gülnar'da bu saat 09.58
UTC ve yayımlanan iki başlangıç saatinden de sonra. Bu sonuçlar yakın kayıtların olay
kimliğini veya ilk algılanma gecikmesini doğrulamaz.

Üç vaka, zaman ve yer bağlamı olarak kayıt altına alındı. Özgün
başlangıç geometrisi ve temsil edici kayıt kapsamı açık. Hedef
alanları boş, günlük gözlem `unknown`, pozitif ve negatif etiket
izinleri `false` kaldı.

Üretici `python scripts/quality/review_three_province_start_context.py`.
Yerel makbuz `outputs/reports/dataset/three_province_start_context_v1/20261108T024231Z_67d3f799/readback.json`.
SHA-256 `f0d86451068aa0ec86aa7f2967eb31fdeb713f9776404f7786c6ad493cb4da09`.
18 senaryoda sayılar ve en erken kayıt saatleri ikinci yöntemle
doğrulandı. 51 ilgili test geçti.
