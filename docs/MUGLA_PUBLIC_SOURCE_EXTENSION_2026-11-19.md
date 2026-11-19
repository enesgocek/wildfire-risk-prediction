# Muğla açık kaynak devamı — 19 Kasım 2026

Araştırmacının yeni yazışma açmadan ilerleme kararı uygulandı. Üç temel
kaynak ve iki ek kaynak adayı incelendi; dosyalar ve iki PDF sayfasının görsel kopyaları
yerelde hash ile bağlandı. Çalışma yeni olay etiketi veya birinci aşama
kabulü sağlamadı. İncelenen kaynaklar bütün açık kaynakların tarandığı
iddiası değildir.

## Yeni kaynakların sağladığı bilgi

MGM bildirisinin 10. PDF sayfasında işletme/şeflik, tarih ve alan
tabloları var; başlangıç koordinatı ve saat yok. Muğla 2021 için
Köyceğiz, Milas/Karacahisar ve Marmaris Milli Parklar satırları seçildi.
Tablonun bölgesel kapsamında Aydın da bulunuyor. Dalaman tarihi
`06.10.2021` basılı; çevredeki Temmuz–Ağustos anlatımıyla uyuşmazlığı
çözülmeden korundu ve bu satır seçkiye eklenmedi.
[MGM, tablo 2–3](https://www.mgm.gov.tr/FILES/genel/makale/ormanyangin.pdf).

Muğla Belediyesinin 30 Temmuz 2022 açıklaması, 29 Temmuz İçmeler
olayında **15.41 ilk ihbar**, **15.46 müdahale** bildiriyor. Başlangıç
228. sokak üstünde tarif ediliyor; etkilenen otel başlangıç noktası
yapılmadı. Metnin özetindeki başlangıç ifadesi yerine gövdedeki ihbar
anlamı ayrı kaydedildi. Saat standardı ve konum hatası açık değil.
[Belediyenin özgün kaydı](https://www.mugla.bel.tr/haber/buyuksehir-itfaiyesinden-marmaris-yanginina-aninda-mudahale).

Türkiye Ormancılar Derneği kitabındaki *Orman Yangınlarının Sayısal
Analizi* bölümü, basılı s. 30'da 2008 Taşağıl–Karabük/Serik–Akbaş
örneğinin tek yangının iki idari kayda bölünmesi olduğunu belirtiyor.
Bu, yazarların yayımlanmış incelemesi olarak atfedildi; bütün OGM
satırlarının bağımsız denetimi sayılmadı. Örnek eğitim dönemi dışında
ve Mersin'deki belirli iki satırın aynı yangın olduğunu kanıtlamıyor.
[Kitap, 53. PDF sayfası](https://www.ormancilardernegi.org/Documents/49acadea-ce7d-44c5-a42b-93c8b8b164e5.pdf).

## Yerel kaynak siciline katkı

Üç MGM satırı ve bir belediye anlatımı, önceki 23 kaydın değiştirilmediği
yeni bir inceleme siciline eklendi. **27 seçili kaynak kaydı**, dört ilin
2018–2023 dönemindeki **24 il-yılının 14'ünde** bağlam içeriyor; önceki
sicilde bu sayı 13'tü. Yeni temsil edilen kesit Muğla 2021. Bunlar
27 bağımsız gerçek yangın veya 14 il-yılda eksiksiz kayıt anlamına gelmiyor.
MGM'nin OGM kökenli tabloyu yeniden yayımlaması ikinci bağımsız saha
ölçümü sayılmadı. Hiçbir hücreye 0 veya 1 atanmadı.

Kaynak kaydındaki tarih, otomatik olarak olayın ilk uydu tespit tarihi
yapılmadı. İdari birim adı tek bir hücrenin merkezi olarak kodlanmadı.
Yeni kayıtların özgün başlangıç geometrisi, olay kimliği, ilk tespit
penceresi ve olay tarihindeki orman/çalılık örtüsü halen açık.

## Erişim ve kontrol sınırı

Yatağan için Avcı ve arkadaşlarının 2024 söndürme çalışması da incelendi.
Gerçek arazi haritası üzerinde tanımlanan başlangıç, varsayılan bir
planlama senaryosuna ait; tarihli gözlenmiş yangın kaydı sayılmadı.
Üniversite arşivindeki tam metin, PDF s. 12–13'ten bu ayrım doğrulandı.
[Yayın ve DOI](https://doi.org/10.1016/j.ejor.2024.03.005).

Belediyenin 25 Haziran 2022 Bördübet duyurusu haritalı rapordan söz
ediyor. Alınan HTML'de ilgili rapor/harita dosyasının bağlantısı bulunmadı;
duyurudan başlangıç geometrisi çıkarılmış sayılmadı. Önceki Marmaris
bağlamı ikinci ayrı olay olarak eklenmedi.
[Duyuru](https://www.mugla.bel.tr/haber/buyuksehirden-marmaris-yangini-raporu).

14 Ekim'de PDF bağlantısı bulunamayan Muğla 2021 duyurusu yeniden
alındı; HTML gövdesinde rapor adı var, ilgili belge bağlantısı yok.
Yayımlanmış bir kaynakçadan eski resmî PDF adresi bulundu. O adrese
yerel istek bağlantı hatası verdi; tek olası yeni yerleşim adresi 404
verdi. İkinci adresin taşınmış gerçek belge adresi olduğu varsayılmadı.
Bu raporun içeriği okunmuş sayılmadı; yeni bir yazışma başlatılmadı.

Yeni kaynak dosyaları anonim HTTPS GET ile alındı; hesap veya kimlik
bilgisi kullanılmadı. MGM ve kitap sayfaları PDF becerisinin görsel
inceleme akışıyla kontrol edildi. Bu asistan destekli incelemedir,
araştırmacının manuel onayı olarak kaydedilmedi. Ham PDF/HTML/PNG
dosyaları Git'e eklenmez. Kamuya açık olma, yeniden dağıtım izni
varsayımı olarak kullanılmadı; kaynaklara kısa olgusal notlarla atıf yapıldı.

## Yeniden üretim ve devam sınırı

`python scripts/quality/audit_mugla_public_extension.py`, beş kaynak ve
iki sayfa görselinin hash'ini, önceki sicil kimliğini, dört yeni kaydın
eğitim dönemini, benzersiz inceleme anahtarlarını, kapsam sayımlarını ve
kapalı etiket izinlerini kontrol ediyor. Bunlar belge/işlem kontrolleri;
anlamsal yangın doğruluğu testi değil. Ruff ve biçim kontrolü geçti.

Sonuç:
`outputs/reports/dataset/mugla_public_extension_v1/20261119T002147Z_990adb00/readback.json`.
SHA-256 `671a6958e3b72b87b19dab944b85f48d911889b78a0a908dc8e7199bde75a83a`.
[Kaynak kimlikleri ve ayrıştırılmış notlar](research/mugla_public_extension_2026-11-19.json).

Yeni kaynaklar konum/saat/kayıt anlamı sorununu kapatmıyor. Yalnız bu
aynı satırları tekrar saymak birinci aşamayı tamamlamayacak. Sonraki
anlamlı kaynak işi, bu seçili olaylardan birine özgün başlangıç haritası
veya açıklanmış olay kaydı eklemek. Böyle bir kanıt bulunmadan kesin
etiket üretimi, PU kabulü, model eğitimi ve nihai birleştirme açılmadı.
Yerel 2024/2025 dosyaları okunmadı; gözlem `unknown` kaldı.
