# Dört ilde belirsiz örneklerin özellikleri ve incelenebilir PU paketi — 20 Kasım 2026

## Tamamlanan somut hazırlık

Önceki pilot yalnız Mersin ile alan kesişimi olan 503 U anahtarının
özelliklerini içeriyordu. Bu devamda **önceden seçilmiş aynı 2.048 U
anahtarının tamamı** 27 özellik ve ayrı kaynak/zaman bilgileriyle
hazırlandı. Yeni örnek seçilmedi; tohum, anahtar, örnekleme olasılığı,
ağırlık veya U'nun belirsiz anlamı değişmedi. U gerçek negatif değil.

1.477 farklı hücrede, 2018–2022 içindeki 1.241 farklı günün **2.482
günlük dosyası** içerik hash'iyle ve gün/hücre/şema/geçmiş pencere
kontrolleriyle okundu. Kaynakların sonradan yayımlanması ayrı kaldı:
tarihsel yayın erişimi bilinmiyor; ERA5-Land retrospektif girdi.
2023/2024/2025 değerleri açılmadı. İşlem 533,437 saniye sürdü; bu
yalnız bu örneklemin hazırlık süresi, tam veri seti veya eğitim tahmini değil.

| İnceleme kesiti | U anahtarı | 27 özelliği tam | En az bir eksik |
|---|---:|---:|---:|
| Antalya alanıyla kesişen | 679 | 609 | 70 |
| İzmir alanıyla kesişen | 423 | 363 | 60 |
| Mersin alanıyla kesişen | 503 | 428 | 75 |
| Muğla alanıyla kesişen | 471 | 387 | 84 |
| **Farklı U anahtarları toplamı** | **2.048** | **1.763** | **285** |

İl üyeliği hücre AOI'sinin il poligonuyla **pozitif alan kesişimi**.
28 U anahtarı iki il alanıyla kesiştiğinden il satırları toplanarak
genel toplam yapılmaz. Bir sınır hücresi en yakın ile zorlanmadı.
Salt sınır dokunuşu il desteği sayılmadı. Eski Mersin kesitinin 503
anahtarındaki özellikler önceki dosyayla birebir aynı çıktı.

U'nun 140 anahtarında meteoroloji ailesi, 154'ünde 30 günlük, 39'unda
60 günlük bitki özellikleri eksik. Sayılar örtüşebilir; 333 veya daha
fazla eksik satır gibi toplanmaz. Gerçek eksik satır sayısı 285.
Eksikler doldurulmadı, sıfır yapılmadı veya örnekler elenmedi.

## Artık açılıp incelenebilen paket

Yeni U tablosuyla eski Mersin kaynak incelemesinin **374 merkez
hipotezi**, yalnız araştırma incelemesi amacıyla aynı ekranda sunuldu.
Bu 374 anahtar, 380 kaynak kaydını temsil ediyor; aynı anahtardaki
çoğul kayıtlar kimlik eşlemesinde korunuyor. Önceki 424 satırlık kaynak
çerçevesi ve WF1538 kararı değişmedi. Bunlar dört ilde doğrulanmış
pozitifler veya 380 bağımsız yangın değildir.

| Paket özeti | Sayı |
|---|---:|
| Belirsiz U | 2.048 |
| Kaynak merkezi hipotezi | 374 |
| Farklı inceleme anahtarı | **2.422** |
| 27 özelliği tam | **2.125** |
| Eksikleriyle korunan | **297** |
| Atanmış gerçek yangın hedefi Y | **0** |

Paket klasörü:
`outputs/reports/dataset/PU_inspection_bundle_v1/20261120T001043Z_80623e41/`.

- **`inceleme.html`**: internet/giriş gerektirmeyen yerel inceleme
  ekranı. İl, yıl, kaynak/U ve eksiklik filtreleri; hücre/tarih araması,
  sayfalama, satıra tıklayınca 27 özelliğin açıklamaları ve ayrı
  kaynak/zaman alanları hazırlandı. Risk rengi veya model tahmini yok.
- **`inceleme.csv`**: aynı 2.422 anahtarın tam hassasiyetli verileri.
  İnceleme grubu, il kesişimi, örnekleme/kaynak kayıt sayısı ve boş
  hedefler model girdisi değil. Model X sütunları ayrı sözlükte açık.
- **`kaynak_izleri.csv`**: aynı anahtarlarda ayrı kaynak/kalite/zaman
  kayıtları; tahmin gününün gözlem durumu girdiye karıştırılmadı.
- `ozellik_sozlugu.json`, `kaynak_kayit_eslemeleri.json`,
  `il_alan_kesisimleri.csv`, `README.txt` ve dosya hash manifesti.
- **`inceleme_paketi.zip`**: aynı dosyaların hash/CRC kontrolü yapılmış
  2.096.705 baytlık arşivi. Yeni, kabul edilmiş etiketli veri seti değil.

Bu paket bir **örneklem incelemesidir**. Ana 72 aylık aday arşivi
2.422 satıra indirgenmedi; bütün günlük 2.889 hücre panelleri burada
yeniden üretilmedi. Dört ilde U bulunduğu halde kaynak adaylarının
yalnız Mersin'den gelmesi, bütün tabloyu source/U sınıflandırıcısına
vererek dört il yangın modeli kurmayı gerekçelendirmez. Böyle bir
eğitim yapılmadı. Nihai etiketli birleştirme ve onay kapısı korundu.

### Tarayıcı kontrolü sınırı

Dosya/CSV/JSON/ZIP kontrolleri tamamlandı. Otomatik tarayıcıyla görsel
ve etkileşim doğrulaması **tamamlanmadı**. Uygulama içi tarayıcı yerel
sunucuya erişemedi; yerel tarayıcıda açık adres güvenilir belirlenemediği
için bilgisayar kontrol aracı UI işlemini durdurdu. Alternatif otomasyonla
bu engel aşılmadı; geçici yalnız-yerel sunucu kapatıldı.

Bu nedenle “ekran görüntüden incelendi” veya “filtreler tarayıcıda
doğrulandı” iddiası yok. Araştırmacının dosyayı kendi tarayıcısında açıp
başlangıçta 2.422 satır, U+Mersin filtresinde 503 satır gördüğünü ve bir
satırın ayrıntılarının açıldığını bildirmesi istenebilir. Bu UI kontrolü
yangın etiketi, model başarısı veya nihai veri kabulü değildir.

**Aynı gün sonraki araştırmacı kontrolü:** araştırmacı başlangıçtaki
2.422 satırı, U+Mersin filtresindeki 503 satırı ve satır ayrıntılarının
açılmasını kendi tarayıcısında doğruladığını bildirdi. Bu sınırlı
etkileşim kontrolü insan bildirimidir; yukarıdaki otomatik tarayıcı
engeli geriye dönük başarı yapılmadı. Ayrı `researcher_ui_check.json`
makbuzu paket readback/HTML hash'lerine bağlandı. Bu bildirim bilimsel
yangın etiketi, yöntem/eğitim veya nihai birleştirme onayı değil.

## Yüzde gerektirmeyen değerlendirme hazırlığı

Mevcut olasılık değerlendirme çekirdeği [ayrı](EVALUATION_CORE_2026-10-16.md)
korundu. Yeni `ranking_metrics.binary_rank_metrics`, negatif veya
1'den büyük **sonlu sıralama skorlarıyla** AP, yardımcı trapez PR-AUC ve
ROC-AUC aritmetiğini hazırlıyor. Skor yüzdeye/olasılığa çevrilmiyor;
Brier/log-loss veya kalibrasyon hesaplanmıyor. Tüm eşit skorlar aynı
eşik grubu; satır sırası sonucu değiştirmiyor. Her iki üyelik sınıfı
bulunmuyorsa sıralama sonucu açıkça tanımsız.

Bu sürüm yalnız **sentetik Y** veya açıkça belirtilen **gözlenen kaynak
S** anlamını kabul ediyor; gerçek yangın hedefi kabulünü kendi başına
açamıyor. Gerçek belirsiz hedefler hata veriyor; sessizce sıfıra veya
bilinen alt kümeye çevrilmiyor. Bu devamda gerçek kaynak AP'si veya
yangın AP'si hesaplanmadı. İleride gerçek hedef değerlendirmesi için
uygun bilimsel kabul/PU değerlendirme protokolü ayrıca bağlanacak.

13 yeni sıralama testi; küçük dizilerde 14 karma ikili hedef vektörü
ve 81 skor düzeninin **1.134 tam kesirli** AP/çift-AUC karşılaştırması,
pozitif monoton dönüşüm altında eşitlik, eşit skor, sayısal uçlar,
eksik/tek sınıf/yanlış anlam korumalarını içeriyor. Bunlar sentetik
matematik kontrolleri; gerçek yangın veya PU varsayımı doğrulaması değil.

## Ana hedef için çalışma sırası

Renklerle göreli risk yönü geçerli. Yeni gözlenen sonuçlar bu yönü
kalibre edilmiş yüzde zorunluluğundan ayırıyor; kaynak–gerçek hedef
ilişkisi ve geçerli değerlendirme ihtiyacını kaldırmıyor.

1. **Bu devamda kapanan hazırlık:** aynı U örnekleminin dört ilde
   özellikleri, eksiklikleri, kaynak zamanları ve incelenebilir dosyaları;
   yüzde gerektirmeyen sıralama aritmetiği.
2. **Bilimsel olarak açık:** kaynak ölçüm/seçilme hatasıyla 24 saatlik
   yeni orman/çalılık yangını sıralaması arasındaki PU varsayımları ve
   değerlendirme dayanağı. Kusursuz 0/1 etiket veya her U için gerçek
   negatif istemek bu protokolün ön koşulu yapılmadı. Yardımcı kaynak
   skoru hedef riski diye yeniden adlandırılmayacak.
3. **Daha sonra:** kabul edilmiş protokol/uygun eğitim yetkisiyle model
   karşılaştırması; veri rolünü koruyan kategori eşik politikası ve
   risk arayüzü. Aynı girdiler için güncel son parça denetimi ve rapora
   bağlı kullanıcı onayı olmadan nihai etiketli birleştirme yapılmayacak.

Yeni model kurulmadı; eski yardımcı modeller/168 skor ve ilk deney
değişmedi. Birinci aşama tamamlandı veya 26–29 Kasım'da kesin
tamamlanacak denmedi. Şu an insan kontrolü istenebilecek somut ürün,
bilimsel etiket yerine **inceleme ekranının açılması ve filtreleridir**.

## Tekrarlanabilirlik ve ayrı doğrulama

- U hazırlığı: `scripts/quality/prepare_full_u_feature_review.py`.
  `outputs/reports/dataset/full_U_feature_review_v1/20261120T000956Z_1a58d019/readback.json`;
  SHA-256 `5aa2791fd0c810d669df003f7481f52350be5bf3091db590b6bddf254f3f4cd2`.
- Aynı klasör `separate_readback.json` SHA-256
  `a070914efd59e2de43542c8100db0ef05e624abc43b2e7072db0c88b67ce17f3`:
  standart CSV/datetime ile özgün 2.048 anahtar/sıra/ağırlık/boş hedef,
  geçmiş hava/bitki zamanları, eksiklik ve 503 eski U değeri kontrol edildi.
- Paket üreticisi `scripts/quality/build_pu_inspection_bundle.py` ve
  `pu_inspection_template.html`. Paket `readback.json` SHA-256
  `1b27ad6d4d428cc504cf11eae6246a5ff0fae14d268107bffcc2e841c4fd7b66`.
- Paket `separate_readback.json` SHA-256
  `52b3ad731fa6ced3c1991afe6c5a17cb14611cbef471eb2dbadecba6ed3ce37f`:
  2.422 farklı anahtar/boş Y, 2.125 tam/297 eksik satır, gömülü JSON
  ve ZIP üyelerinin içerik hash'leri ayrı geri okundu. Bu görsel UI testi değil.
- Sentetik sıralama makbuzu:
  `outputs/reports/dataset/relative_rank_evaluation_v1/20261120T000956Z_82aca507/readback.json`;
  SHA-256 `da8c8c40afed8e5cf0a9c2cf4771459139f6e302459f5ee263490f948a6562e4`.
- Yeni davranış testleri: altı U inceleme, yedi paket, 13 sıralama.
  Önceki ilgili kontrollerle birlikte son koşuda **228 test geçti**;
  bu bütün depo testlerinin çalıştırıldığı iddiası değil. Altı Python
  dosyasında Ruff ve biçim kontrolü geçti.
  Açıklamalar ve ayrı kontroller otomatik/asistan işi; bağımsız saha veya
  araştırmacı görsel onayı olarak yazılmadı. Ham/ara tablolar, HTML ve ZIP
  yerel kalır; Git'e yalnız kod ve araştırma belgeleri gönderilir.
