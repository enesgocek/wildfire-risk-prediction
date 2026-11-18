# Gülnar–Silifke başlangıç ve yayılma bağlamı — 18 Kasım 2026

Araştırmacının iki örtü ön notundan sonra, WF1578 ve WF1579 satırlarının
başlangıç/yayılma rolleri kamuya açık kurum kayıtlarıyla karşılaştırıldı.
Arşivde iki satır da 7 Eylül 2022 ve 07.13 bildiriyor. Noktalar WGS84
elipsoidi üzerinde 3.483,07 m aralıklı ve iki ayrı proje hücresinde.

## Olay zaman çizelgesi

| Kaynak | Bildirilen zaman | Kaynaktaki anlam |
|---|---|---|
| Belediyenin 7 Eylül duyurusu | 07.12 | Gelen ihbar |
| Bakanlığın 8 Eylül duyurusu | 07.13 | Önceki günün yangın başlangıcı |
| Aynı Bakanlık duyurusu | 07.20 | İlk müdahale |
| Belediyenin 8 Eylül duyurusu | Yaklaşık 07.30 | İtfaiye yetkilisinin ertesi günkü başlangıç anlatımı |
| AFAD'ın 7 Eylül 22.20 bülteni | Akşam durumu | Müdahalenin sürmesi |

İhbar, bildirilen başlangıç ve müdahale zamanları ayrı anlamlarla saklandı.
07.12 ihbarının 07.13 başlangıcından önce görünmesi, saatleri tek bir
kesin tutuşma dakikasına dönüştürmeyi desteklemiyor. Yaklaşık 07.30
ifadesi de kayıtlı bir hata aralığı sağlamıyor. Bu dört sabah saati hem
Türkiye saati hem UTC olarak denendiğinde sekiz senaryoda hedef günü
7 Eylül 2022 kalıyor. Bu vaka saat standardını bütün arşiv için doğrulamıyor.
[Belediye aynı gün](https://www.mersin.bel.tr/haber/mersin-buyuksehir-ilgili-tum-birimleriyle-yangin-bolgesinde-1662554680),
[Bakanlık](https://www.tarimorman.gov.tr/Haber/5402/Soma-Ve-Gulnardaki-Orman-Yanginlari-Kontrol-Altinda),
[Belediye ertesi gün](https://www.mersin.bel.tr/haber/buyuksehir-ekipleri-gulnarda-gorev-basinda-1662623158),
[AFAD bülteni](https://www.afad.gov.tr/mersin-gulnarda-meydana-gelen-yangin-hk).

## Yer ve yayılma kanıtı

Bakanlık Büyükeceli'de başlayan yangını anlatıyor. Saha raporu başlangıcı
Karadere ile ilişkilendirip Silifke'ye yayıldığını bildiriyor. Bu anlatımlar,
iki idari satırın aynı yangının farklı kayıtları olması olasılığını destekliyor.
Yayımlanan metinlerde bu satırlara bağlanan özgün ortak olay kimliği veya
ölçülmüş tutuşma koordinatı görülmedi. Bu ilişki bir çıkarım olarak tutuldu.
[Bakanlık duyurusu](https://www.tarimorman.gov.tr/Haber/5402/Soma-Ve-Gulnardaki-Orman-Yanginlari-Kontrol-Altinda),
[TMMOB saha raporu](https://www.tmmob.org.tr/icerik/tmmob-mersin-ikk-orman-yangini-raporu).

Raporun 4. ve 5. sayfaları görüntüye çevrilerek incelendi. Haritalardaki
işaretler etkilenen bölgeleri ve orman/mülkiyet bağlamını gösteriyor.
WF1578 veya WF1579'u açıkça tutuşma noktası ilan eden bir işaret
görülmedi. İki noktaya başlangıç/yayılma rolü atanması açık kaldı.
[Kaynak PDF](https://www.tmmob.org.tr/sites/default/files/tmmob_mersin_ikk_gulnar_orman_yangini_raporu-son.pdf).

## Uydu kayıtlarının zaman bağlamı

07.13 Türkiye saati varsayımıyla başlangıç 04.13 UTC olarak alındı.
Bu andan 8 Eylül 00.00 UTC'ye kadar belirtilen nokta çevrelerindeki
FIRMS kayıtları sayıldı. İlk tespit gerçek tutuşma saati olarak kullanılmadı.

| Arşiv noktası | Yarıçap | Katalog tespiti | İlk tespit UTC |
|---|---:|---:|---|
| WF1578 | 250 m | 5 | 7 Eylül 09.58 |
| WF1578 | 1 km | 32 | 7 Eylül 09.58 |
| WF1579 | 250 m | 0 | Yok |
| WF1579 | 1 km | 17 | 7 Eylül 10.49 |

İki 1 km çevrede ilk tespitler 51 dakika aralıklı. Bunlar farklı sensör
geçişleri olduğundan fark, yayılma süresi olarak kullanılamaz. İncelenen
başlangıç yorumundan önceki 24 saatte aynı dört çevrede katalog kaydı
bulunmadı. Bu katalog yokluğu günlük gözlem yeterliliği sağlamaz.

## Aşama sonucu ve doğrulama

İki örtü ön notu, kaynakların bildirdiği olay akışı ve uydu zamanları
birlikte kayıtlı. Satırların özgün olay kimliği ve gerçek başlangıç
koordinatı açık. Birinci aşama sürüyor. Günlük gözlem `unknown`, negatif
etiket izni `false`; yeni etiket oluşturulmadı.

Beş kaynağın ham HTML/PDF dosyaları yerelde saklandı. AFAD metni web
aracıyla incelendi; yerel kopya alma denemesi SSLError verdi. TLS
doğrulaması korunarak bu erişim eksikliği kaydedildi. Kaynak listesi
`outputs/reports/dataset/gulnar_public_timeline_sources_v1/20261118T202337Z_1a001542/readback.json`.
SHA-256 `1f515069670f5a412d400eaf8c93ee9491896778797c1ef3280cfdf32787f288`.

`python scripts/quality/audit_gulnar_start_context.py` kaynak kopyalarını,
arşivi, katalog ve araştırmacı notlarını doğrular. Zamanlar metin olarak
sıralanmaz; UTC tarih/zaman değerleri karşılaştırılır. Sekiz zaman/pencere
senaryosu ve dört mesafe/zaman sayımı üretildi. 36 ilgili test ve Ruff geçti.
Yerel makbuz
`outputs/reports/dataset/gulnar_start_context_v1/20261118T202632Z_4cec399a/readback.json`.
SHA-256 `e0987d551527c21ff1e738837686ae1cb14a19aff2cb5cfab70348290ef59cd2`.
