# Taşınabilir deneysel inceleme paketi

24 Kasım 2026. Güncel v3 ekranı, mevcut ayrı veri/model parçaları ve
sonuç ekleri tek yerel teslimde toplandı. Bu, nihai etiketli veri
birleştirmesi veya ana yangın hedefinin kabulü değildir. Önceki
arşivler değiştirilmedi; yeni eğitim/tahmin/etiket/yıl veya yayın yoktur.

## Güncel açılış

Teslim kökü:
`outputs/reports/dataset/portable_research_release_v1/20261124T190220Z_58fe285c/`.

Bu bilgisayarda `package/index.html` başlangıç sayfası açılır.
Arşiv başka klasöre taşınacaksa `research_release.zip` dosyasının
**tamamı çıkarılır**, sonra çıkarılan klasördeki `index.html` açılır.
Klasör yerleşimi korunur. Kod, kullanıcı girişi, internet veya
model eğitimi çalıştırmak gerekmez; bu cümle kayıtlı verinin incelemesi
içindir, ham kaynaklardan yeniden eğitim için değildir.

Başlangıç sayfası haritaya/12 örneğe, ana CSV'ye, ayrı üyelik ve
kaynak dosyalarına, model/veri kartlarına ve mevcut karşılaştırma
grafiklerine bağlanır. Satır sayıları aynı yerde açıklanır:

- Ana deneysel özellik tablosu: 44.082 farklı hücre–gün, 822 hücre,
  27 alan; 2018–2022 kaynakla seçilmiş takvimdir, nüfus paneli değildir.
- Varsayılan dört-il 2022 ekranı: 6.573 kayıt / 4.841 puanlanabilir / 185 hücre.
- Ayrı Mersin: 2.383 / 1.929 / 68 hücre.
- Dört-il ekranında Mersin il ek filtresi: 2.038 kayıt; ayrı kaynak takvimiyle aynı seçim değildir.
- İki ekran birlikte: 8.956 takvim üyeliği, 8.711 farklı anahtar,
  244 farklı hücre. Takvimler örtüşür; bağımsız yangın sayısı değildir.

## İçerik ve korunan parçalar

Paket **499 dosya**, ZIP **24.032.305 bayt** içerir. 272 mevcut
izlenen Markdown belgesinin anlık görüntüsü `documents/` altında
korundu. Bunlar destekleyici tarihsel kaynaklardır; hepsini okumak
ekranı kullanmanın ön koşulu değildir. Yeni kısa başlangıç sayfası
güncel açılışı ve temel ayrımları doğrudan gösterir.

Önceki denetlenmiş yerel v2 paketten 191 üye byte olarak aynen
korundu. Özellik/üyelik/kaynak dosyaları, dokuz model, eski ölçüler
ve kanıtlar bu korunan parçalardandır. Eski v2 arayüzünün yerini
mevcut v3 dosyaları aldı; eski arşiv yerinde kaldı.

`interface/review_data.js`, hesap çekirdeği, harita/uygulama kodu,
geometri ve HTML v3 ile aynı byte'tır. Yalnız yardımcı
`research_context.js` içindeki üç belge yolunun adresi paket içindeki
karşılığına çevrildi. Örnekler, sayı aralıkları ve kanıt belge hash'leri
aynı kaldı. Son kaynak-örtüşmesi ve örnek incelemesi tabloları/şekilleri
`results/` altında ayrı ektir; bilimsel CSV'ler elle düzeltilmedi.

`target`/kabul edilmiş L boş, gözlem unknown ve negatif etikete izin
false kaldı. 41.358 tam 27-alan satırı ve 2.724 eksik satır korundu.
Nihai etiketli eğitim tablosu oluşturulmadı. Paketleme bu kapının onayı değildir.

## Yapılan kontroller

1. Önceki paketin ve yeni kaynak makbuzlarının güncel hash'leri doğrulandı.
2. Yeni dizin ve ZIP envanteri, dosya boyutları, SHA-256, ZIP üye
   tekilliği/CRC ve byte eşliği kontrol edildi.
3. Başlangıç ve arayüz HTML'inde 20 yerel dosya/bölüm bağlantısı,
   ayrıca üç dinamik kanıt bağlantısı paket içinde çözüldü.
4. Ayrı denetleyici 191 eski üye, v3 bilimsel/UI byte kopyaları,
   44.082 benzersiz anahtar/822 hücre/27 alan, 41.358 tam satır,
   boş Y/L ve unknown/false koşullarını geri kontrol etti.
5. ZIP, özgün teslim ve prototip konumundan farklı, yeni ve yalıtılmış
   bir klasöre çıkarıldı. Bütün dosyalar yeniden hash'lerle eşleşti;
   belge bağlantıları yalnız çıkarılan dosyalarla çözüldü.
6. Çıkarılan arayüz dosyalarıyla 14 çevrimdışı DOM etkileşim testi
   yeniden geçti. Test aracı depodaki mevcut Node/jsdom kurulumunu
   kullanır; arayüz dosyaları ve kanıt hedefleri çıkarılan klasördendir.

Bu devamda sekiz yeni yerel bağlantı davranışı, üç mevcut arşiv
bütünlüğü ve 28 hedef/nihai birleştirme kapısı dahil **39 Python testi**
geçti. Yer değiştirme nedeniyle 14 DOM testinin tekrarı gerekliydi;
bilimsel hesap/öğrenme tekrarlanmadı. Başka klasöre taşınmış dosyaların
DOM işlevleri doğrulandı; gerçek tarayıcı CSS/görsel render kontrolü
yapıldığı iddia edilmez. Kullanıcıya rutin teknik test görevi verilmedi.

272 belge tarihsel özgün depo/ham veri yollarını da içerir. Bu eski
bağımlılıkların hepsi taşınabilir arşive dahil değildir. Özellikle ham
kaynaklardan tam yeniden eğitim, özgün depo ve makbuzların bağladığı
girdileri gerektirir. Doğrulanan taşınabilir kapsam, güncel başlangıç/
inceleme ekranı, üç ana kanıt hedefi, ayrı veri/model/sonuç dosyalarıdır.

## Makbuzlar

- Teslim makbuzu: `portable_research_release_v1/20261124T190220Z_58fe285c/readback.json`.
  SHA-256 `ddb18f8e05f17b1113b05ca73230cef44441f261d032ac861f8cf5c65db7a677`.
- Ayrı yer-değiştirme denetimi:
  `portable_release_relocation_audit_v1/20261124T190302Z_3f11f732/readback.json`.
  SHA-256 `d1aeee73dfbba7266d9872865c99318e22a89929732563aae07d350828a10d3a`.
- Manifest SHA-256 `3f53aa69098bc61fa282434e3cfeb2f40f0076eff9a2b375874bc1d9dae0af1a`.
- ZIP SHA-256 `ccf80db1ece274288d7f9d4a41e888a0d1bc23931f13217c57f8922a8424122b`.

Arşiv, veri ve model dosyaları yereldir; GitHub'a kod ve belgeler
gönderilir. Dış veri yayını veya yeni bulut işi başlatılmadı.

## Projeye katkısı ve açık konu

İnceleme için birbirinden farklı çıktı klasörlerini bulma ve özgün
proje dizinine bağlı belge yolu sorunu giderildi. Güncel araştırma
sürümüne tek dosyadan başlanabilir. Kaynak-bağlam skorunun gerçek
yeni yangın riskine aktarımı ve günlük hassasiyetin bilimsel sınırı
aynı durumdadır; taşınabilir teslim bunları doğrulamış sayılmaz.
