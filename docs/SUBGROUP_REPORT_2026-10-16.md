# İl, mevsim ve gözlem desteğiyle hata raporu hazırlığı

Tarih: 16 Ekim 2026. Durum: gerçek etiketsiz yöntem pilotunda payda sayımı
ve ayrı sentetik skor provası. Gerçek model hata analizi yapılmadı; model,
kalibratör veya etiket kabulü yoktur.

## Rapor sözleşmesi

Yeni `subgroup_report` katmanı, sayıları ve ölçütlerin hesaplanma durumunu
aynı tabloda gösterir. Açık kapsam seçimi zorunludur: gerçek etiketsiz
yöntem pilotu veya `synthetic_` kimlikli oyuncak skorlar. Bu sürüm gerçek
etiketli model değerlendirmesini uygulamaz. Her iki kapsam da yalnız
2018–2023 UTC gece yarısı anahtarlarını kabul eder; 2024/2025 açılmaz.

[Yapılandırmada](../configs/error_analysis_v1.json) beş bölüm vardır:
genel toplam, birincil il, takvim mevsimi, nominal destek durumu ve il×mevsim.
İller Antalya, Muğla, İzmir ve Mersin; mevsimler UTC tahmin ayının
DJF/MAM/JJA/SON ayrımıdır. Birincil il mevcut pilot atamasıdır; sınır hücreleri
bütün kesişen illerde tekrar sayılmaz. Bu çalışma il geometrisini yeniden
doğrulamaz. Mevsim adı tahmin tarihiyle uyuşmazsa kayıt reddedilir.

Her raporda **28 satır** bulunur: 1 + 4 + 4 + 3 + 16. Boş gruplar da
açıkça yer alır. Her bölümün toplamı aynı ana kohorta eşittir; bölümler
birbirinin farklı kesimleridir ve bütün satırlar üst üste toplanamaz.
Hücre-gün, farklı hücre ve farklı tarih sayıları birbirine karıştırılmaz.
Ham Z/+00:00 yazımı farklı aynı UTC anahtar ikinci satır olarak kabul edilmez.

## Bilinmeyenler ve hesaplanamayan ölçütler

Her grupta toplam birim, bilinen hedef, kabul edilmiş pozitif/negatif,
belirsiz hedef ve mevcut/eksik tahmin sayıları tutulur. Hedef/tahmin
çaprazlaması da dört ayrık sayımdır: ikisi mevcut, yalnız hedef mevcut,
yalnız tahmin mevcut, ikisi eksik. Toplamları grup büyüklüğüne eşittir.
Bilinen hedefler içindeki pozitif oranı kendi paydasıyla adlandırılır;
belirsiz hedefler bu orana negatif olarak girmez.

Gerçek pilotta hedef ve tahminlerin tamamı boş olmalıdır; sahte sabit
olasılık eklenmesi veya sıfır hedef atanması reddedilir. Tahmin eksik sayısı
bu kapsamda model çalıştırılmadığını gösterir; çalışan modelin hatası değildir.
Sıfır pozitif/negatif sayısı da yangın yokluğunu değil, kabul edilmiş hedef
bulunmadığını ifade eder. Gözlem unknown ve üç etiket kabul bayrağı false kalır.

Sentetik kapsamda bile bir grubun herhangi bir hedefi veya tahmini eksikse
tamamlanmış alt küme sessizce seçilmez; o grubun bütün başarı ölçütleri boş
kalır ve nedeni yazılır. Tam sentetik grupta mevcut değerlendirme çekirdeğiyle
AP, trapez PR-AUC, ikili Brier, log-loss ve ROC-AUC hesaplanır. Tek sınıflı
grupta sıralama ölçütleri tanımsız/boştur; Brier ve log-loss aritmetiği
hesaplanabilir. Boş grup hiçbir zaman sıfır hata veya kusursuz başarı almaz.

Asgari birim/bağımsız olay eşiği ve güven aralığı yöntemi seçilmedi.
İstatistiksel destek `not_assessed`, bağımsız olay sayısı ve güven aralığı
boştur. Çok küçük örnekte sayısal hesap bulunması güvenilir model başarısı
sayılmaz. Birbirine bağlı hücre-günlerden bağımsız olay sayısı türetilmez.

Gelecekte iki model karşılaştırılırken aynı anahtar/hedef evreni koşulu
ayrıca uygulanmalıdır; farklı grupların AP değerleri doğrudan üstünlük
kanıtı değildir. Bu sürüm model seçmez, anlamlılık testi yapmaz veya çoklu
grup karşılaştırmalarından doğrulanmış araştırma sonucu çıkartmaz.

## Nominal destek, etiket kabulü değildir

Yeni sayısal alan eşiği seçilmedi. Mevcut `nominal_land_fraction` yalnız
eksik, sıfır veya pozitif olarak betimlenir. Pozitif değer tam günlük
gözlem, bulut/duman yokluğu, yeterli algılama veya güvenilir negatif değildir.
Hedef penceresindeki bu tanı bir model özelliği olarak eklenmedi.

Önceki tanılardaki 1e-8 sayısal tolerans korunur. 1'den tolerans içinde
büyük değerler ayrıca sayılır, kaynak dosya veya değerler kırpılmaz.
Eksik destek ayrı gruptur; sıfıra doldurulmaz. Geçersiz sayılar, sonsuz
değerler, metinle yazılmış sayılar ve boolean destekler reddedilir.

## Gerçekleşen pilot sayımları

Kaynak, 15 Ekim'de üretilen sabit **156 amaçlı hücre-gün**, **117 farklı
hücre** ve **12 eğitim tarihidir**. Tarihler 2018, 2021 ve 2023 içindedir;
bu rastgele örneklem veya bütün eğitim evreni değildir. Önceki bağlı CSV
hash'i tekrar kontrol edilip `target_day` açık UTC tahmin anahtarına çevrildi.
İlk yangın tespit zamanı bu dönüşümde kullanılmadı.

| Birincil il | Birim | Belirsiz hedef | Kabul edilmiş hedef |
|---|---:|---:|---:|
| Antalya | 42 | 42 | 0 |
| Muğla | 26 | 26 | 0 |
| İzmir | 44 | 44 | 0 |
| Mersin | 44 | 44 | 0 |

Mevsim paydaları kış 31, ilkbahar 42, yaz 40, sonbahar 43'tür. Nominal
destek 7 birimde sıfır, 149 birimde pozitiftir; bu tabloda destek alanı
eksik birim yoktur. 57 değerin 1'in biraz üzerinde fakat mevcut tolerans
içinde olduğu ayrıca kaydedildi. Bunların hiçbiri etikete çevrilmedi.
**156 hedef boş, gerçek başarı skoru sayısı sıfırdır.** Bu sayımlardan
yangın sıklığı, il risk sıralaması veya etiket doğruluğu çıkarılamaz.

## Ayrı sentetik prova ve doğrulama

Sekiz açık sentetik birimde yedi bilinen hedef ve yedi tahmin vardır;
ikisinin birlikte mevcut olduğu altı birim bulunur. Genel toplamı bu
altıya daraltıp skor üretme denemesi engellendi. Dört tam Mersin örneğinde
elle hesaplanabilir AP 5/6'dır; bu bir oyuncak aritmetik sonucudur. Tek
negatifli grupta Brier 0,04 bulunurken AP tanımsız kaldı. Bunlar gerçek
Mersin/Muğla başarısı veya eğitilmiş model çıktısı değildir.

**35 yeni davranış vakası dahil 253 ilgili test** Deprecation/Future
uyarıları hata sayılarak geçti. Üç yeni Python dosyasında lint/format geçti.
Sınamalar anahtar ve mevsim uyuşmazlığını, eksik/boş/tek sınıflı grupları,
metin/boolean/sonsuz giriş reddini, kaynak değişmezliğini, sıra değişmezliğini,
nullable sayıları ve belirsiz hedefin negatife dönüşmemesini kapsar.
Otomatik kontrol insan incelemesi veya bağımsız olay doğrulaması değildir.

Çevrimdışı betik önceki planın 52 girdisini/beş çıktısını yeniden hash ile
kontrol etti. Önceki rapor/kapanış ve yeni dört kaynakla **63 girdi/dört
çıktı** bağlandı. Gerçek ve sentetik tablolar ayrı CSV'de tutulur. Ağ/bulut
işi, sınıflandırıcı/kalibratör fit, gerçek skor veya nihai birleştirme yok.
Ham uydu geometrileri yeniden işlenmedi; gerçek etiketli veri üretilmedi.
Diskteki CSV'ler tekrar okundu; gerçek il/mevsim sayımları kaynak tablodan
ayrı pandas sayımıyla uzlaştırıldı, boş gerçek ölçütler ve sentetik AP
geri okunduğunda da korundu.

Çıktı: `outputs/reports/dataset/subgroup_report_v1/20261016T134755Z_0c95a351/`.
Readback SHA-256:
`df7fb636008606108342dc0fafe8fe164bbc96f1b940ae915ad59008a19893f7`.
Kapanış SHA-256:
`e9504caffd059d925bcaafc67f97a10d1a2a627f6d8beedfa220d03b808f3b6b`.

## Sonraki adım ve sınır

Araştırmacının seçtiği 2018–2022 temel fit, 2023 kalibrasyon, 2024
karşılaştırma hazırlık yönü korunur; gerçek takvim/etiket uygunluğu halen
açıktır. Model hatası analizi için önce kabul edilmiş hedefler ve aynı
anahtarlara bağlı gerçek model tahminleri gerekir. Bu rapor nihai parçaların
son kabul kontrolü veya kullanıcının birleştirme onayı yerine geçmez.
Sonraki hazırlık, kalan veri kabul bağımlılıklarını ve yapılabilecek işleri
tek güncel envanterde toplamaktır.
