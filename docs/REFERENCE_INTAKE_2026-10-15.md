# Bağımsız olay kayıtlarının alım kontrolü

Tarih: 15 Ekim 2026. Durum: normalleştirilmiş kayıtlar için yerel kontrol
katmanı hazırlandı ve mevcut kamu bağlamında denendi. OGM'den olay verisi
veya yeni teknik yanıt alınmış değildir. Etiket veya nihai birleştirme yapılmadı.

## Hazırlanan işlem

Kurumsal yanıt geldiğinde kayıtların konum, zaman, köken ve kullanım
koşulları incelenmeden uydu eşleştirmesine geçilmemesi amaçlanır.
`reference_intake.audit_intake`, önceki olay şablonunun 19 alanıyla çalışır.
Sağlayıcının dosyasını kendiliğinden bu şemaya çevirmez; gerçek dosya ve
alan açıklamaları geldikten sonra eşleme ayrıca incelenecek. Kaynak dosya
korunacak, dönüşüm yeni sürümde ve açık kanıtla yapılacaktır.

Girdi alanları metin olarak okunur; olay numaralarının başındaki sıfırlar
korunur. Bu katmanda boş değerler sıfır değildir. Girdi dışı kişisel bilgi
sütunları, tekrarlı başlık veya eksik şema satır alımından önce reddedilir.
Bu durum sağlayıcıda o alanların bulunamayacağı anlamına gelmez; kişisel
alanlar kontrolsüz biçimde çalışma tablosuna taşınmaz.

Her normalleştirilmiş kayıt üç durumdan birinde raporlanır:

- `invalid_record`: tarih/saat/sayı biçimi, eğitim dönemi, yarım koordinat
  veya tekrarlı kimlik gibi giderilmesi gereken sorun vardır.
- `needs_source_review`: kayıt yapısı işlenebilir; konum, saat standardı,
  bağımsızlık, kapsam veya kullanım incelemesi eksiktir.
- `ready_for_matching_review_only`: yalnız sonraki eşleştirme incelemesine
  hazırlık koşulları sağlanmıştır. Pozitif veya negatif etiket kabulü değildir.

Hatalı satır sonraki sağlam satırın tanısını kaybettirmez. Yinelenen
`reference_id` veya aynı kaynak içindeki `source_record_id` için etkilenen
bütün satırlar tutulur ve engellenir; sessiz tekilleştirme yapılmaz.
Farklı kaynaklarda aynı sicil numarası otomatik aynı olay sayılmaz.

## Zaman konum ve kaynak korumaları

Tarih 2018–2023 eğitim sınırında olmalıdır. Kullanılacak UTC zaman
sınırları açık, sıralı ve eğitim döneminde olmalıdır. Saat dilimi
belirsiz yerel saat UTC'ye çevrilmez; ilk ihbar gerçek tutuşma veya ilk
uydu tespiti sayılmaz. Yerel saat metninin saat/dakika biçimi ayrıca
denetlenir; saatin anlamı ve dönüşüm doğruluğu kaynak incelemesi gerektirir.

Bu sürüm yalnız açık `EPSG:4326` boylam/enlem alanlarını eşleştirme
incelemesine hazırlayabilir. Başka CRS koordinatları boylam/enlem kabul
edilmez ve dönüştürülmez. Koordinat çifti, aralık ve konum belirsizliği
kontrol edilir. İdari yer adı başlangıç noktasına çevrilmez. Dört il
adının kontrolü geometrik AOI veya hücre üyeliğini kanıtlamaz; gerçek
konumlar geldiğinde geometri ve belirsizlik ayrıca değerlendirilecektir.

Kaynak belge SHA-256 değeri yerelde doğrulanmış belge siciline bağlanır.
Kullanım koşulları, bağımsızlık, olay kaydına erişim, koordinat referansı
ve zaman tanımı için açık boolean inceleme alanları gerekir; `"True"`
metni veya sayısal 1 onay sayılmaz. Bu alanlar otomatik kurum/uzman onayı
veya bağımsız doğruluk kanıtı üretmez. Gerçek alımda inceleme dayanakları
ayrıca raporlanacak; bugün hepsi beklemededir.

Tanı çıktısında yalnız satır numarası, sabit neden kodları ve kapalı
kabul bayrakları bulunur. Ham açıklama, kişi adı, olay kimliği veya
koordinatlar hata mesajına kopyalanmaz. Geçersiz kayıtlardaki bilinmeyen
değerler silinmiş kaynak yerine geçmez; özgün dosya korunmalıdır.

## Gerçek yerel deneme ve sonuç

Önceki [referans hazırlığının](INDEPENDENT_REFERENCE_PLAN_2026-10-15.md)
rapor/kapanış ve çıktı hash'leri ile 15 miras girdisi yeniden kontrol edildi.
Değişmemiş 12 kamu bağlam kaydı yalnız 19 alanlı kontrol tablosuna
uyarlandı. Belge sayfa/satır kimliği bağımsız olay sicili sayılmadı.
İl/koordinat/saat dilimi gibi bilinmeyen alanlar doldurulmadı.

**12 kaydın tamamı kaynak incelemesi bekleyen durumda kaldı; eşleştirmeye
hazır kayıt sıfırdır.** Toplam 15 farklı eksiklik kodu her kayıtta görüldü;
bunlar 180 ayrı yangın veya 180 bağımsız hata değildir. Doğrulanmış PDF'nin
elde bulunması, kaynağın olay/koordinat/lisans kabulünü sağlamadı.

Boş olay şablonu da gerçek dosyadan okundu: sıfır girdi, sıfır olay tanısı,
sıfır etiket. Bu kontrol, kayıt alınmamasını yangın yokluğu örneğine çevirmedi.
Sentetik tam kayıtların testte yalnız eşleştirme incelemesine geçebilmesi
gerçek saha verisinin kabul edildiği anlamına gelmez.

Çıktı dizini:
`outputs/reports/dataset/reference_intake_v1/20261015T195625Z_e277865f/`.
Beş çıktı: `context_intake_diagnostics.json`, `reason_counts.csv`,
`pending_source_reviews.json`, `empty_template_receipt.json`,
`input_manifest.json`. İşlem sonunda 25 bağlı girdinin hash'i yeniden
kontrol edildi; çıktı hash'leri de kapanış sonrası geri okundu.

Readback SHA-256:
`1f6fef07264e955725793e0bc8da4ba817741d0a13b4478981580f9c7fb8c0e1`.
Kapanış SHA-256:
`dccd6ded041b6a2cb1eea0b4a643840e876d50e9387a42d6de81999475308600`.

**40 yeni davranış vakası dahil 85 ilgili test** Deprecation/Future
uyarıları hata sayılarak geçti. Üç Python dosyasında lint/format geçti.
Yeni ağ/bulut işi yok; özel yazışma veya yeni sağlayıcı dosyası okunmadı.
Önceki hash ile bağlı `reference_readiness` kodu/çıktıları değiştirilmedi.

## Kalan kararlar

Bu teknik hazırlık bağımsız olay verisi ihtiyacını ortadan kaldırmaz.
Yanıt geldiğinde hangi kayıtların paylaşılabildiği, gerçek kayıt kapsamı,
izin koşulları, zaman anlamı ve konum belirsizliği değerlendirilecek.
Eşleştirme toleransı veya negatif etiket politikası gerçek kaynak görülmeden
seçilmedi. Alan veya yöntem kararı gerektiğinde araştırmacıya gerekçeli
seçeneklerle sunulacak. `daily_observation_status=unknown`, boş hedefler,
pozitif/negatif kabulün kapalılığı ve nihai birleştirme onayı koşulu korunur.
