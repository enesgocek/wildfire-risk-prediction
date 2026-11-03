# Gözlemden güvenilir etikete geçiş: karar noktası — 4 Kasım 2026

## Sonuç ve yapılan iş

Gözlem alanı/zaman tanıları ile etiket doğruluğunun aynı bilgi olmadığı
netleştirildi. Önceki gözlem, seçim etkisi ve referans alım raporlarının
güncel baytları ve bağlı çıktıları geri okundu. Üç donmuş rapor ve
çıktıları/kod dahil **21 kimlik** doğrulandı; yeni bilimsel gözlem,
yangın kaçırma oranı veya etiket üretilmedi.

İncelenen sicilde 156 amaçlı hücre-gün / 117 hücre / 12 gün var;
60 birimde termal tanık, 96 birimde tanık yok. Bunlar kabul edilmiş
60 yeni orman yangını ve 96 gerçek negatif değildir. İncelenen 12 kamu
bağlam kaydının eşleştirmeye hazır olanı sıfır; kurumsal olay tablosu yok.
Bu sayım yeni gelen bütün dosyaların bağımsız envanteri değil, belirtilen
önceki raporların doğrulanmış geri okumasıdır.

Eski amaçlı pilotta yalnız açıklayıcı %95 kesimiyle günlük destek
koşulu, tekrarlı destek ve dört dilim koşulu; termal tanıksız aynı 96
birimin sırasıyla 72/49/9'unu tutuyordu. Bu eski bulgu burada yeni deney
sonucu diye sunulmadı. Koşulu değiştirmek örnek seçimini değiştirir;
bu sayılardan hangi etiketin doğru olduğu veya kaç yangının kaçırıldığı
hesaplanamaz. Tam dönem için yeni gözlem koşulu seçilmedi.

## Birincil kaynak kontrolü

4 Kasım'da şu kaynakların içerikleri doğrulandı:

1. **NASA FIRMS Fire Alert Notes:** geçişler arasında başlayıp biten
   yangınlar ve bulut/duman/ağaç örtüsü nedeniyle tespit kaçırılabileceği
   açıklanıyor. Daha geniş günlük geometrik alanın gerçek yangın yokluğunu
   tek başına kanıtlamadığı yorumu, kaynak ve yerel pilotun birlikte
   değerlendirilmesidir. [NASA](https://firms.modaps.eosdis.nasa.gov/alerts/notes.php).
2. **Elkan ve Noto, KDD 2008:** pozitif–belirsiz (PU) öğrenmede etiketli
   pozitifler ve pozitif/negatif karışımı belirsiz küme kullanılır. Basit
   olasılık düzeltmesi, gerçek pozitiflerin sabit olasılıkla etiketlenmesi
   ve etiketli kümenin gerçekten pozitif olması varsayımlarına dayanır.
   Bu, bizim verimizde sağlanmış varsayım değildir.
   [Yazarın makalesi](https://cseweb.ucsd.edu/~elkan/posonly.pdf).
3. **Bekker ve Davis, PMLR 94:8–22, 2018:** etiketlenme olasılığının
   bazı özelliklere bağlı olmasına izin veren SAR yaklaşımı önerilir;
   bu da varsayımsız öğrenme değildir. [Yayınevi kaydı](https://proceedings.mlr.press/v94/bekker18a.html).
4. **Bekker ve Davis, Machine Learning 109:719–760, 2020:** PU yöntemlerinin
   dağılım/etiketleme varsayımları ve sınıf oranı tahmini koşulları incelenir.
   [Hakemli derleme](https://doi.org/10.1007/s10994-020-05877-5).

Bu makaleler gerçek yöntem kaynaklarıdır; yangın uygulamamızda başarı
veya uygunluk deneyi olarak sunulmadı. Uygulamaya aktarım değerlendirmesi
bu çalışmanın önerisidir; kaynakların bizim projeyi doğruladığı iddia edilmez.

## Neden yeni bir algoritma otomatik çözüm olmuyor?

Yalnız açıklayıcı, gerçek verimizden ölçülmemiş bir örnek: yanlış pozitif
olmadığını varsayalım. Aynı %2 gözlenen pozitif sıklığı, gerçek %2 olay
sıklığı ve %100 yakalanma ile de, gerçek %4 olay sıklığı ve %50 yakalanma
ile de oluşabilir. Tespit mekanizması hakkında ek bilgi olmadan aynı
kayıttan hangisinin doğru olduğu çıkarılamaz.

Bulut, geçiş zamanı, örtü ve yangın özellikleri gözlenme olasılığını
etkileyebilir. Yerel pilotun farklı seçim sonuçları sabit/rastgele
etiketlenme varsayımının sağlandığını göstermez; varsayımı istatistiksel
olarak çürüttüğümüz de ileri sürülmez. PU'ya geçmek bu koşulları görünür
yapar, kendiliğinden doğrulamaz. Pozitif tarafta doğal örtü ve yeni olay
kontrolleri de hâlâ gereklidir. Bir termal kaydı doğrudan temiz pozitif
saymak PU'nun etiketli pozitif varsayımını karşılamaz.

Mükemmel veya bütün yangınları içeren bir mutlak kanıt beklentisi
oluşturulmamalıdır. Gereken, hedefin anlamına uygun bir protokol,
belgelenmiş hata/eksiklik ve sınama dayanağıdır. Uydu tespit modeli
olasılığını doğrulanmış gerçek yangın olasılığı diye adlandırmak da
bu sorunu çözmez. AP, Brier ve kalibrasyon sonuçları değerlendirme
etiketlerinin neyi ölçtüğüyle birlikte yorumlanmalıdır.

## Araştırmacıya sunulan iki çalışma yönü

| Yön | Somut sonraki iş | Yarar / sınır |
|---|---|---|
| **A — Önerilen: ana hedef + referans edinimi** | Üniversite aracılığıyla OGM'ye sınırlı kapsamlı talebi yeniden gündeme almak; gerekirse ilk etapta bir il/yıl için anonim olay ve kayıt kapsamı bilgisi istemek | Yöntem varsayımını dış bilgiyle sınama fırsatı; kullanılabilir kayıt/yanıt garantisi yok, gelen veri ayrıca incelenecek |
| **B — Kurumsal talep olmadan PU uygulanabilirliği** | Güvenilir pozitif tanımı, etiketleme mekanizması, sınıf oranı, değerlendirme/kalibrasyon ve örnek seçim varsayımlarını mevcut veride denetlemek | Belirsizleri zorla sıfır yapmadan yöntem araştırması; ek kanıt gerekebilir, hemen eğitim veya veri seti kabulü sağlamaz |

Öneri A'dır. Referansın tek mümkün kaynağı OGM değildir; aynı gereksinimleri
karşılayan başka bağımsız kaynak da incelenebilir. Talep daraltılabilir:
olay kimliği, koordinat ve belirsizliği, ihbar/başlangıç zamanının anlamı
ve saat standardı; ayrıca hangi dönem/bölgede hangi olayların kayda
alındığı, eksikler ve kullanım koşulları. Olay listesindeki yokluk, liste
kapsamı bilinmeden negatif sayılmayacak. Üniversite kanalı resmî talep
yoludur; danışmanın her yöntem kararını incelemesi şartı getirilmez.

Önceki CİMER/üniversite talep hazırlıkları korunuyor; yeni ileti
gönderilmedi. Kullanıcının 21 Ekim'de bu yolu şimdilik planlamadığı
tercihi otomatik aşılmadı. Yeni bilimsel yön seçimi soru olarak sunuldu,
yanıt gelmeden A veya B kabul edilmiş yöntem olarak uygulanmıyor.
Ana hedef katalog var/yok hedefine dönüştürülmedi.

## Yerel kapanış ve açık durum

Üretici: `scripts/quality/audit_label_evidence_readiness.py`.
Çıktı: `outputs/reports/dataset/label_evidence_readiness_v1/20261103T222738Z_905d7dae/readback.json`.
SHA `1e25e550f76acebc859978816c9b2f2dfa78c0c9fd7a6abe5060194480de37d6`.
UTC tarihli klasörün Türkiye çalışma tarihi 4 Kasım'dır.

21 kaynak/kod/çıktı hash'i işlem öncesi/sonrası kontrol edildi;
rapor soy bağı, 156 sabit birim, eşleştirme hazırlığı sıfır kaydı ve
kapalı bayraklar uzlaştırıldı. JSON ve lint/format geçti. Önceki
562 ham/ara girdi veya tüm kaynak dizileri yeniden denetlenmedi.
Literatür erişimi yapıldı; yeni uydu verisi, bulut işi, gerçek model
deneyi, yeni insan incelemesi, etiket veya nihai birleşme yapılmadı.
`daily_observation_status=unknown`, `negative_label_permitted=false` sürer.
