# Deney hazırlık kaydı ve dosya izlenebilirliği

Tarih: 16 Ekim 2026. Durum: yerel hazırlık kaydı ve ayrı sentetik prova.
Gerçek deney, etiket kabulü, model eğitimi veya nihai birleştirme yapılmadı.

## Amaç ve kayıt kapsamı

Ön işleme istatistikleri tek başına hangi kaynakların ve hangi ayrımın
kullanıldığını tam tanımlamaz. Yeni `experiment_record` katmanı, açıkça
belirtilmiş dosyaların göreli yollarını, baytlarını ve SHA-256 değerlerini;
ölçüt/ön işleme yapılandırmalarını; kapalı etiket protokolünü aynı kayda bağlar.
Kaydın gövdesi sabit JSON sırasıyla hash'lenir. Aynı girdiler aynı `record_id`
verir; çıktı klasörünün oturum tarihi/nonce'u deney kimliğine karıştırılmaz.

Bu kayıt **çalıştırılabilir bir eğitim talimatı değildir**. Gerçek model,
hiperparametre, örnekleme, kalibrasyon, nihai parça incelemesi ve kullanıcı
onay makbuzu `null` kalır. `labels_accepted`, `model_ready`,
`training_authorized` ve `final_merge_performed` false'tur. Beş ileri yıl
takvim taslağı tutulur; gerçek embargo/olay/blok politikaları seçilmediğinden
bunlar yürütülebilir fold değildir. AP ana/trapez PR-AUC yardımcı kararı
mevcut yapılandırmadan okunur; eski başlangıç YAML'ı değiştirilmedi.

Asgari bağlı dosyalar: yeni kayıt kodu, ölçüt ve ön işleme yapılandırmaları,
ayrım/ön işleme/özellik yardımcıları, mevcut hedef kabulü ve nihai birleştirme
kapısı, `pyproject.toml` ve `uv.lock`. Önceki hazırlık raporları ve bağlı
dosyaları ayrıca kaydedilir. Bu bir dosya kapsamı kaydıdır; bütün deponun
veya bütün ham kaynakların yeniden denetlendiği anlamına gelmez.

Dosyalar yalnız açık listeyle okunur; klasör taraması, `.env` okuma veya
MLflow bağlantısı yapılmaz. Mutlak/gezinmeli yollar, gizli dizinler,
kimlik bilgisi adları ve sembolik bağlantı bileşenleri reddedilir.
Bu yol kontrolleri genel bir gizlilik garantisi değildir; giriş listesi
bilinen eğitim hazırlığı dosyalarıyla sınırlı tutulmalıdır. Hash kontrolleri
kapsamın bilimsel yorumunu veya kişisel bilgi bulunmadığını kanıtlamaz.

## Sentetik ayrım kaydı

Yalnız `synthetic_` önekli ve bölüm başına en fazla 1.000 satırlı oyuncak
girdiler bu sürümün ayrım bağlama fonksiyonuna alınır. Bu teknik sınır gerçek
veriyi otomatik olarak anonimleştirmez; gerçek ayrım kabulü uygulanmadı.
Eğitim ve dışarıda tutulan tarafın anahtar/zaman/olay/blok koşulları mevcut
ayrım denetleyicisinden geçirilir. Ön işleme yalnız eğitimde öğrenilir.

Kayıt şu bilgileri bağlar: iki tarafın normalize edilmiş UTC anahtarlarıyla
olay/blok metadata hash'leri, özgün özellik değerlerinin hash'leri, öğrenilen
istatistikler ve iki dönüştürülmüş matrisin hash'leri. Eksikler hash hesabında
açık `null` olarak gösterilir. Sütun sırası özellik sözleşmesinden gelir;
satır sırası değişikliği yeni bir ayrım gibi gösterilmez. Değerlendirme
özellikleri değişirse kayıt değişir, eğitim istatistikleri değişmez.

Sentetik prova 2018→2019 ve 2021→2022 takvimlerinde, her birinde ölçekleme
açık/kapalı olmak üzere dört ayrım içerir. Bölüm başına altı eğitim/dört
dışarıda tutulan satır ve üç aday özellik kullanıldı. Sıfır saat ek aralık,
medyan doldurma, boş sütunda durdurma ve adlandırılmış ayrık bloklar yalnız
bu oyuncak denemelerin ayarlarıdır. Gerçek yöntem tercihi değildir.

## Geri kontrol ve sınamalar

Kayıt JSON'dan geri okunduğunda bağlı dosyalar yeniden hash'lenir; geçerli
politika ve kapalı kabul alanlarıyla kayıt yeniden oluşturularak karşılaştırılır.
Bir dosyanın, bayt bilgisinin veya kayıt alanının değişmesi yeni kayıt
gerektirir. Hazırlığa `training_authorized=true` ekleyip gövde hash'ini
yeniden hesaplamak da bu sürümün geri kontrolünden geçmez.

Bu mekanizma imza, kimlik doğrulaması veya bağımsız bilimsel kabul değildir.
Sentetik hash'ler gerçek olay doğruluğunu kanıtlamaz. Mevcut
`final_merge_gate.require_final_merge_approval` değiştirilmedi; gerçek
nihai birleştirici güncel parça kontrolü ve açık kullanıcı onayını ayrıca
uygulamalıdır. Bu çalışmada böyle bir makbuz oluşturulmadı veya kabul edilmedi.

**35 yeni davranış vakası dahil 193 ilgili test**, Deprecation/Future
uyarıları hata sayılarak geçti. Üç yeni Python dosyasında lint/format geçti.
Testler JSON geri okumasını, sıra değişmezliğini, değer/olay/blok/ayar
değişimlerini, aynı uzunlukta değiştirilmiş dosyayı, kayıt oynanmasını,
yanlış yolları, eksik/tekrar girdileri ve gerçek kimlik/2025 reddini kapsar.
Otomatik sınamalar insan etiketi incelemesi veya saha doğrulaması değildir.

Çevrimdışı gerçek çalıştırmada önceki ön işleme raporunun 33 girdisi ve dört
çıktısı tekrar kontrol edildi. Önceki rapor/kapanış ve yeni kaynaklar dahil
**44 bağlı girdi/dört çıktı** kapanışı geçti. İki kayıt diske yazıldı ve
yeniden okunarak doğrulandı. Gerçek özelliklere fit/dönüşüm, gerçek hedef
atama, sınıflandırıcı/kalibratör fit, 2024/2025 veri erişimi ve ağ/bulut işi yok.

Çıktı: `outputs/reports/dataset/experiment_preparation_v1/20261016T013115Z_9990881e/`.
Mevcut hazırlık kimliği:
`78e221dd3e3b1946273d8e6e433e54dbe2709aa39933c0f401c728c958992db7`.
Sentetik hazırlık kimliği:
`6369ba848761e2e436c49bf5d90eae1451ca055f1397f0d81c42cb693fe2dc0c`.
Readback SHA-256:
`20d367d95f0ea330adacf5d678a72bb0f79c724b0bc4edd0383b114f4535983e`.
Kapanış SHA-256:
`c141e033ba254f348d9858f262bd9fa5a78effae83cab4ba3ebad3ccd869b071`.

## Sonraki aşama

Gerçek deney girişini bağlamadan önce olay/negatif kabulü, son parça
kontrolleri ve kullanıcı onayı gerekir. Kurumsal yanıtlar beklenirken
örnekleme/sınıf ağırlıkları ile kalibrasyonun hangi veri rollerinde
öğrenileceğine ilişkin karşılaştırma planı hazırlanabilir. Bu politikalar
veri incelenmeden seçilmiş veya uygulanmış gibi raporlanmayacaktır.
