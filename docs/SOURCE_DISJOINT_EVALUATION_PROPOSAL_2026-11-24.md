# Aynı hücre–gün örtüşmesini ayıran değerlendirme önerisi

24 Kasım 2026. **Hazırlık ve örneklem denetimi tamam; önerilen yeni
başarım hesabı çalıştırılmadı.** Araştırmacının yöntem kararı beklenir.
Bu, önceki koşullu prototip yönünü yeniden sormaz; değerlendirme
örnekleminin hangi alt kesitleriyle yeni ölçüm yapılacağına ilişkindir.

## Sınanabilecek soru

Ana araştırma hedefi, dört ilde sonraki 24 saatlik yeni orman/çalılık
yangınıdır. Mevcut modeller kaynak/aday bağlamını sıralamaktadır.
Bu önerinin daha dar sorusu: **ayrı Mersin takvimindeki mevcut sonuç,
dört-il uydu adaylarıyla aynı hücre ve gündeki kaynak kayıtlarına
ne ölçüde bağlıdır?** Bu bir kaynak-örtüşmesi duyarlılık kontrolüdür;
gerçek yangın hedefine aktarımı tek başına doğrulayamaz.

Üç farklı sorun birbirinden ayrılır:

1. Kaynak takvimlerinin aynı hücre–gün üyeliğini paylaşması: mevcut
   anahtarlarla denetlenebilir; aşağıdaki protokol bunu sınar.
2. Aynı gerçek olayın komşu hücre/günlerde görünmesi: yalnız anahtar
   ayrılığıyla çözülmez; yeni bağımsız olaylar varmış gibi yorumlanmaz.
3. Kaynak koordinatı/zamanı/kapsamının gerçek yeni yangını temsil etmesi:
   mevcut kayıtların açık belirsizliğidir; yeni yardımcı ölçü bunu kapatmaz.

Salur'un 2021 bağlamı mevcut modellerin öğrenme dönemindedir; kör
2022 doğrulama örneği gibi kullanılamaz. Marmaris 2022'de yayımlanan
işaret/sınır ve üç/dört başlangıç uyuşmazlığı, Gülnar'da iki kaynak
noktasının olay/başlangıç rolü daha önce açıklığa kavuşmamıştır.
Bu örnekler sırf öneriyi tamamlamak için kesin Y etiketine çevrilmedi.
Mevcut [PU bilgi gereksinimi](PU_METHOD_REVIEW_2026-11-19.md),
[Marmaris](MARMARIS_SOURCE_MARKER_2026-11-19.md) ve
[Gülnar](GULNAR_START_CONTEXT_2026-11-18.md) kanıtları esas alındı;
bu devamda yeni dış kaynak incelemesi veya iletişim yapılmadı.

## Ölçülmüş hazırlık bulgusu

Ayrı Mersin takviminde 81 kaynak-gün önerisi vardır. 65'i mevcut
ana tam-alan meteoroloji ve eksiksiz 15 dinamik girdi koşulunu geçer.

| Kaynak gününün dört-il takvimindeki aynı anahtarı | Tüm kaynak günleri | Puanlamaya uygun |
|---|---:|---:|
| En az bir uydu senaryosunda S önerisi | 6 | 6 |
| Kayıt var; bütün senaryolarda atamasız | 3 | 3 |
| Dört-il takviminde bu hücre–gün yok | 72 | 56 |
| Toplam | 81 | 65 |

“Yok”, yalnız bu kaynakla seçilmiş takvimde anahtar bulunmadığıdır;
uydu gözlemi yok, tespit yok veya gerçek yangın yok anlamına gelmez.
16 uygun olmayan kaynak günü silinmez; bu kesitlerde çift üretmez.

## Önerilen üç iç içe kesit

| Kesit | Tüm kaynak günü | Uygun gün / katkı veren hücre | Genel çift / model-ayar | 1–3 gün çifti / model-ayar |
|---|---:|---:|---:|---:|
| G0: özgün kaynak takvimi, mevcut referansı aynen geri oku | 81 | 65 / 56 | 1.921 | 363 |
| G1: herhangi bir uydu senaryosunda aynı anahtarda S önerisi olan altı günü kaynak listesinden çıkar | 75 | 59 / 54 | 1.744 | 332 |
| G2: dört-il takviminde aynı anahtarı hiç bulunmayan kaynak günleri | 72 | 56 / 51 | 1.656 | 314 |

G2, G1'in; G1, G0'ın alt kümesidir. Bağımsız testler veya bağımsız
örneklemler değildir. Anahtar örtüşmesizliği, kaynakların bütünüyle
bağımsız ölçümler olduğu anlamına gelmez. G1'de ayara göre 23–25,
G2'de 23–24 kaynak gününün hücresi model öğrenmesinde görülmüştür.
Dolayısıyla G2 de mekânsal kör test değildir.

## Karşılaştırma sözleşmesi

- Dokuz önceden sabit ayarın ve üç mevcut skorun tamamı kullanılır:
  ana tam-alan XGBoost, önceki geniş meteoroloji XGBoost ve
  dondurulmuş doğrusal skor. Yeni tahmin çağrısı veya yeniden fit yoktur.
- Her kaynak günü, **özgün Mersin takviminde** aynı hücre/ayda bulunan
  uygun atamasız günlerle karşılaştırılır. G1/G2'den çıkarılan kaynak
  günleri kontrol listesine alınmaz. Böylece dışlama gerçek negatif
  veya yeni atamasız üyelik üretmez; karşılaştırma tanımı değişmez.
- Önceki beş kesit korunur: aynı hücre/ayın tümü, 1–3 gün, 4–30 gün,
  kaynak gününden önce ve sonra. Saat/tarih daha iyi skor için kaydırılmaz.
- Üstün sıra 1, eşitlik 0,5 krediyle, tam sayı kazanım/eşitlik ve
  mevcut yardımcı çift oranı raporlanır. Gerçek yangın AP'si, kalibrasyon,
  p-değeri veya güven aralığı üretilmez. Yeni risk kategorisi yoktur.
- En fazla **405 ölçü satırı**: 3 grup × 9 ayar × 3 skor × 5 kesit.
  G0'ın 135 satırı önceki Mersin sonucu ile tam eşleşmek zorundadır.
  Diğer 270 satır önerilen yeni ölçüdür; şu anda hesaplanmadı.
- Karşılaştırma kaydı aynı günleri dokuz modelde tekrar içerebilir;
  toplam satır sayısı bağımsız yangın/gün sayısı gibi kullanılmaz.
- Gözlem unknown, negatif etiket izni false, `target`/L boş kalır.
  2023–2025, yeni indirme/bulut ve nihai birleştirme kapsam dışındadır.

## Sonuç nasıl yorumlanacak?

G1/G2'de benzer yardımcı sıralama kalırsa, mevcut ayrımın yalnız altı
aynı-anahtar uydu adayına dayanmadığına ek destek olur. Bu, kaynak
kayıtlarının doğru tutuşma konumu/zamanı olduğunu kanıtlamaz.
Belirgin değişirse kaynak/örneklem duyarlılığı olarak raporlanır;
daha iyi sonuç veren kesit tek başına seçilmez. Olumlu/olumsuz bütün
ayarlar tutulur, mevcut veri ve raporlar geriye dönük düzeltilmez.

Bu öneri gözlenebilir, sınırlı bir soruyu çözer. Ana gerçek yangın
iddiasına ilişkin kanıt açığı **ek skor hesabıyla kapanmış sayılmaz**.
Yeni kaynak kullanmadan yapılabilecek bu küçük kontrolün önerilme
nedeni, mevcut iki takvimin farkını ölçülebilir biçimde tamamlamasıdır.

## Durma ve kaynak sınırı

Girdi hash'i değişirse, G0 eski ölçüleri geri üretmezse, karşılaştırma
günleri değişirse veya toplam 900 saniye aşılırsa durulur; dosyalar
korunur ve kabul edilmiş sonuç ilan edilmez. Desteksiz kesit varsa
çift sayısı sıfır, ölçü boş tutulur; başarı sıfır yazılmaz. İyileşme
olmadığında yeni parametre araması ya da ilave grup kesimleri açılmaz.
Yürütme için ayrı araştırmacı yöntem kararı gerekir; hazırlık JSON'u
bir yürütme veya nihai birleştirme onay makbuzu değildir.

## Hazırlık doğrulaması ve dosyalar

Anahtar/üyelik/kalite envanteri hazırlandı; yeni skor ölçüsü hesaplanmadı.
Eski referansın beş kesitteki çift sayısı 27 model/ayar satırının
her birinde geri doğrulandı. Kaynak gününün dışarıda bırakılmasının
onu kontrol gününe çevirmediği, eksik günün silinmeden korunduğu ve
gelecek yıl/çift anahtar/senaryoya göre değişen Mersin kaynağının
reddedildiği üç davranış testi geçti. 28 mevcut hedef/birleştirme
kapısı testiyle bu devamda toplam **31 ilgili test** geçti.

Ayrı denetleyici; plan yardımcısını veya arayüz payload'ını kullanmadan,
önceki `Mersin_source_anchor_overlap.csv` ve modelin CSV anahtar/kalite
alanlarından 81 kaynak ve 15 plan desteğini geri kurdu; eşleşti.

- Açık öneri: `configs/source_disjoint_evaluation_proposal_v1.json`.
- Hazırlık: `outputs/reports/dataset/source_disjoint_evaluation_preparation_v1/20261124T030406Z_9554fb98/`.
  Kaynak envanteri, 15 destek satırı, 27 görülen/görülmeyen hücre
  destek kaydı ve `execution_proposal.json` içerir.
- Plan makbuzu SHA-256:
  `c20b988ba0ab1387f4e4121efeabe6a6939e30eac2bedbf7c6ba9cfbafffa45f`.
- Ayrı audit: `source_disjoint_preparation_audit_v1/20261124T030456Z_26cc1be8/readback.json`;
  SHA-256 `8b8064f890449a626a25cbd3cb3c9063cdfe83f67405c558cafa2aa090cc9e23`.

## Araştırmacıya sunulan karar

**A önerisi:** bu sınırlı kaynak-örtüşmesi sınamasını mevcut skorlarla
çalıştır; bütün üç kesit ve ayarları raporla. Yeni eğitim/indirme yok,
900 saniye yerel sınır; gerçek yangın kabulü sağlamaz.

**B:** bu ek sınamayı atla; mevcut ölçüler ve sınırlamalarla prototip/
teslim hazırlığını ilerlet. Zaman kazanılır, fakat aynı-anahtar
örtüşmesinin sonuca katkısı yeni ölçüyle ayrılmamış kalır.

Bu seçim araştırma örneklemi ve yeni değerlendirme kapsamını belirler;
rutin teknik ekran testi veya eski prototip yönünün yeniden onayı değildir.
