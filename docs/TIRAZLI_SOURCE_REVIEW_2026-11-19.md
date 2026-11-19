# Tırazlı ve Muğla: yeni birincil kaynak incelemesi — 19 Kasım 2026

WF1538 incelemesi kapanınca, mevcut pozitif önerilerine yeni kaynak
dayanağı ekleyebilecek açık belgeler araştırıldı. Aynı ham çiftlerin
kontrolü tekrarlanmadı. Bu incelemenin sonucu yeni bir kaynak kaydıdır;
yeni yangın veya L üyeliği değildir.

## Belge ve inceleme

Enes Karadeniz'in Fırat Üniversitesi için hazırladığı 2020 yüksek lisans
tezi, yazarın [açık tam metin sayfasından](https://www.researchgate.net/publication/395273286_Forest_fire_risk_modeling_and_fire_simulation_in_the_southeast_of_Urla_peninsula_Seferihisar-Menderes)
indirildi. DOI `10.13140/RG.2.2.32357.67049`. Platformun 2025 yükleme
tarihi, tezin 2020 yılı ve olayın 18 Ağustos 2019 tarihi ayrı tutuldu.
Üniversite/YÖK kopyası doğrulanmadı; dosya adına dayanarak tez numarası
ilan edilmedi. Yazar yüklemesi, kurumun özgün olay sicili değildir.

PDF **157 sayfa, 13.556.563 bayt**. SHA-256:
`c22d4f5b13a7d5f3b894c1d43a3f5e5de95d1d4e275dcd73f646e26f319676cf`.
Doğrudan istek 403 verdi; sonraki açık tarayıcı indirmesi başarılı oldu.
Giriş bilgisi kullanılmadı, kullanıcıdan tekrar indirme istenmedi.
Özgün PDF ve türetilen görüntüler yerelde korunuyor; Git'e gönderilmiyor.

Yazar basılı s. 113'te başlangıç noktasını OGM'den aldığını belirtiyor.
Basılı s. 102'de OGM kaynaklı, başlangıçtan 15 dakika sonrası olarak
sunulan bir fotoğraf var. Bunlar **kaynak beyanları**; özgün koordinat
dosyası veya bağımsız ikinci saha ölçümü alınmış sayılmadı.

Asistan PDF s. 119, 130, 132 ve 133'ü görüntüleyerek inceledi.
Harita 29'da MTT yolları ve yanık alan sınırları, Harita 30'da simüle
varış zamanı sınıfları görüldü. Ayrı etiketlenmiş bir başlangıç simgesi
belirlenemedi. Bu sonuç bütün tezde veya bütün açık kaynaklarda koordinat
bulunmadığının kanıtı değildir. Metin çıkarımı tek başına harita kabulü
olarak kullanılmadı. Görüntülemede font uyarıları oluştu; incelenen sayfalar
okunabildi. Araştırmacı/bağımsız uzman görsel onayı alınmış sayılmadı.

PDF s. 119'daki asıl fotoğrafın gömülü JPEG kopyası **656 × 400 piksel**;
Pillow ile EXIF alanı ve GPS IFD bulunmadı. Özgün fotoğrafın metadata
durumu bilinmiyor. Kamera konumu bulunsa bile tutuşma konumu yerine
kullanılamaz. Simülasyonun en erken 0–1000 dakika bandı, yol yakınsaması
ve duman merkezi başlangıç koordinatına çevrilmedi.

## Veri hazırlığına katkı ve açık koşul

Tırazlı için başlangıç girdisinin kökenini açıklayan ek bir belge elde
edildi. Ancak mevcut köy/çalışma alanı konumlarından birini gerçek
başlangıç diye seçmeye yeterli yeni geometri çıkarılmadı. Kaynak bağlamı
olarak korunuyor; eşleştirmeye veya L'ye otomatik geçirilmedi. Aynı 2019
vakasına ait ek belge, seçili vaka sayısını veya il-yıl kapsamını artırmaz.

İki önceki olası L önerisinin, WF1538 A kararının ve **2.048 U anahtarının**
dosya kimlikleri yeniden doğrulandı; içerikleri değiştirilmedi. Dokuz
kaynak dosyası hash ile bağlandı, sayfa sırası ve fotoğraf metadata sonucu
geri okundu. Bu dosya/metadata denetimi, kaynak yorumunu otomatik
doğrulayan bir bilimsel test değildir; yeni model testi çalıştırılmadı.

Sonraki kabul ilerlemesi için açık başlangıç geometrisi veya başka
gerekçeli olay bağlantısı gerekir. PU seçilme/karışım varsayımları ve
değerlendirme dayanağı ayrıca açık. Yeni yazışma başlatılmadı; ana hedef
değiştirilmedi. Gözlem `unknown`, pozitif/negatif izinleri kapalı; yeni
etiket, eğitim ve nihai birleştirme yok. Birinci aşama tamamlanmış değil.

## Aynı devamda Muğla'nın yayımlanmış başlangıç verisi izi

Baltacı ve Yıldırım'ın 2021 tarihli [birincil makalesi](https://dergipark.org.tr/en/pub/ogmoad/article/708385)
de kontrol edildi: DOI `10.17568/ogmoad.708385`, 11 sayfa.
Yöntem s. 3, sonuç haritası s. 10 ve girdi kaynağı s. 11 görüntüden
okundu; bütün sayfaların metni incelendi. Makale başlangıç noktalarıyla
çalışıldığını belirtiyor ve OGM 2020b veri tabanına atıf yapıyor. Erişilen
yayın, tarih–koordinat eşli olay satırlarını sağlamadı; PDF'ye gömülü
ek dosya sayısı sıfır. Bundan başka hiçbir açık kopyanın bulunamayacağı
sonucu çıkarılmadı. Yayımlanan risk haritası yangın gerçekleşme etiketi
veya günlük gerçek risk olasılığı sayılmadı. OBM kapsamı Muğla ilinden
ayrı tutuldu. Yeni iletişim kurulmadı.

Bu ikinci kaynakta altı yerel dosyanın kimliği ve 11 sayfalık metin
kapsamı geri okundu. PDF 4.841.583 bayt; SHA-256
`0035be84d60eee08f5bc711a2e2dafc9cfbf5723e55170998d48c88055b87edd`.
[Yapılandırılmış Muğla kaynak notu](research/mugla_2010_2019_source_evidence_2026-11-19.json).
Yerel makbuz `outputs/reports/dataset/mugla_2010_2019_source_v1/20261119T191429Z/readback.json`,
SHA-256 `7f5fd7eeba72f07f5fc605a3b3466b7b950bca9f0199f404ef5c8d72cea6c404`.

İki yeni kaynak incelemesi tamamlandı. İkisi de şu aşamada kaynak bağlamı;
mevcut iki olası L ve 2.048 U değişmedi. Engeli daha fazla dosya kontrolü
değil, hedefe bağlanabilir yeni olay kanıtı kapatabilir. Yeni bir kaynak
aynı toplu tabloyu veya simülasyonu yineliyorsa etiket kabulünde ilerleme
sayılmayacak; açık başlangıç geometrisi ve tarih/kayıt anlamı sunan
belgelere öncelik verilecek.

## Tırazlı izlenebilirliği

- [Yapılandırılmış kaynak ve görsel inceleme notu](research/tirazli_source_evidence_2026-11-19.json).
- Yerel doğrulama: `outputs/reports/dataset/tirazli_source_review_v1/20261119T191017Z_620fe98a/readback.json`.
- Makbuz SHA-256: `18fe67cecf4d5087e1fd6b477f2415bec07c94c68a83748be08e94fce415ea47`.
- Yerel tekrar kontrolü: proje kökünde `.venv/Scripts/python.exe outputs/reports/dataset/tirazli_primary_source_v1/20261119T185740Z/verify_source.py`.
  Bu komut ağ erişimi veya etiket üretimi yapmaz; yeni makbuz oluşturur.
