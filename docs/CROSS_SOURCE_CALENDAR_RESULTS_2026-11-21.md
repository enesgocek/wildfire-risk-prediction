# Ayrı Mersin takviminde sabit modellerin sonucu

21 Kasım 2026. Araştırmacı [ayrı Mersin takvimi ve sabit-model
sınamasını](CROSS_SOURCE_CALENDAR_PROPOSAL_2026-11-21.md) A yönüyle
açıkça seçti. **2.383 satırın özellik hazırlığı, ayrı geri okuması
ve dokuz mevcut modelle puanlama tamamlandı. Yeni fit yapılmadı.**
Farklı kaynakta günlük ayrım zayıf kaldı; sonuç risk doğrulaması
olarak sunulmayacak.

## Tamamlanan veri hazırlığı

81 eski kaynak-merkezi günü, 78 hücre–yıl–ay ve 11 takvim ayında
2.383 uygun tarih korundu. 336 günün 672 yerel dosyası güncel içerik
hash'i ve geçmiş pencereyle incelendi. 2.323 satırda 27 özellik ve
15 dinamik alan tam; 60 eksik satır silinmedi. 81 kaynak gününün
79'unda dinamik alanlar tam. 318 eski X/QA kaydı, iki önceki
snapshot'la birebir aynı; iki snapshot'ın kendi kesişimi nedeniyle
83 ve 245 eşleşmenin toplamı tekil 318 değildir.

Asıl 87 coğrafi U ve genel 2.048 U/ağırlıkları değişmedi. Yeni
takvimin diğer tarihlerine yangın yok yazılmadı. Korunan WF1538
hücre-günü kaynak grubuna yeniden eklenmedi. Gerçek hedef ve kabul
edilmiş L boş; günlük gözlem unknown kaldı.

Ayrı okuyucu bütün anahtarları, kaynak üyeliğinin yalnız önceki
81 kayıttan geldiğini, standart UTC/geçmiş hava/bitki örtüsü
pencerelerini, 318 X/QA eşitliğini ve aylık makbuzları kontrol etti.
Bu ikinci okumada 672 ham günlük dosya tekrar hash edilmedi;
hazırlık onları güncel içerikleriyle doğrulamıştı. En geniş mevcut
2 km/72 saat gözlenen grafiğinde eski fit anahtarlarıyla yeni
2022 takvimi arasında ortak blok 0; gerçek fiziksel olay
bağımsızlığı veya tüm bağımlılıkların çözümü anlamına gelmez.

## Farklı kaynağa günlük aktarım

Yeni X'lere aynı dokuz doğrusal model ve aynı fit-only ölçek
uygulandı. Ölçek/coef öğrenilmedi. Kayıtlı model skoru ayrı doğrusal
matris hesabıyla, aynı hücre–yıl–ay çiftleri ayrı grup döngüsüyle,
45 ölçü skaler kredi hesabıyla karşılaştırıldı. Model dosyaları ve
bellek durumları önce/sonra aynı kaldı.

| 2022 Mersin kaynak bağlamı | Dokuz modelde çift AUC aralığı | Çift |
|---|---:|---:|
| Aynı hücre–yıl–ay, iki tarafta 15 alan tam | 0,522542–0,540575 | 2.329 |
| İki tarih 1–3 gün aralıklı | 0,450000–0,465909 | 440 |
| İki tarih 4–30 gün aralıklı | 0,539439–0,558497 | 1.889 |
| Karşı tarih kaynak tarihinden önce | 0,579200–0,613600 | 1.250 |
| Karşı tarih kaynak tarihinden sonra | 0,451344–0,464319 | 1.079 |

Bu ölçü yardımcı kaynak-bağlamı sıralamasıdır; gerçek yangın AP'si,
olasılığı, yüzde doğruluk veya bağımsız kör test değildir. Aynı gün
birden fazla çiftte bulunabilir. Kaynak koordinatının rolü/hata
sınırı, saat standardı, olayın gerçekten yeni oluşu, yerel örtü ve
kayıt kapsamı açıklığa kavuşmadı. Bu yüzden zayıf sonuç yalnız
model hatası veya kaynağın yanlışlığı diye açıklanamaz. Ancak
uydu adaylarında görülen ayrımın farklı kaynakta güçlü biçimde
tekrarlandığı da söylenemez. 2022 önceden incelenmiş keşif yılıdır.

Somut örnek: aynı yerde kaynağın yangın günü dediği tarih ile iki
gün sonraki bilinmeyen tarihin hava/bitki örtüsü puanını sıralamak,
bu modellerde güvenilir bir günlük uyarı temeli oluşturmadı.
Kaydın konumu/tarihi belirsizken bunu kesin yanlış tahmin veya
doğru yangın sayısına dönüştürmek de doğru olmaz.

## Yerel kayıt ve makbuzlar

SQLite önce yedeklendi; 45 ölçünün adları/değerleri yerel MLflow'da
birebir geri okundu. Yeni model/registry, indirme veya bulut yok.
MLflow run: `53d6ab6f261d4998b7b0a0f1454552d9`.

Yollar `outputs/reports/dataset/` altındadır:

| İş | Makbuz ve SHA-256 |
|---|---|
| Özellikler | `cross_source_calendar_feature_review_v1/20261121T180737Z_c322d93c/readback.json` — `d32b99e6581c6a2412ba6013af727d4220d19d8e2d03666f8ebb48634d3ce0f6` |
| Ayrı X/QA/grafik okuması | `cross_source_calendar_feature_audit_v1/20261121T181138Z_4f2974b7/readback.json` — `30e8a26839d83349e77f5dbed0f4059e912113b603a4a8fb9957e3bba9bcc163` |
| Sabit-model ve ayrı hesaplar | `cross_source_fixed_model_run_v1/20261121T181438Z_bc972c9e/readback.json` — `a4fb83beea02226eca149c5ca8a0383326a1db0143b2ca395adbc50a1e6ab6f9` |

İlk klasörün `snapshot_b1df1055/` dizininde özellik/provenance/rol
CSV'leri; son klasörde dokuz incelenebilir skor CSV'si ve
`source_calendar_comparisons.csv` bulunur. Skor CSV'sinde eksik
60 gün, kaynak-bağlamı alanları ve boş gerçek etiketler korunur.
Bu dosyalar nihai etiketli eğitim verisi değildir.

## Sonuç ve bundan sonraki öncelik

Onaylı farklı-kaynak sınaması tamam. Yakın tarihlerdeki ayrımın
zayıflığı nedeniyle sıradaki iş daha çok modeli aynı göstergede
denemek olmayacak. Araştırma planında zaten bulunan FWI/resmî
meteorolojik yangın tehlikesi referansının veri ve zaman uygunluğu
inceleniyor. Bu referans da gerçek tutuşma olasılığı değildir;
mevcut etiket boşluğunu sihirli biçimde kapatmaz. Ama öğrenilmiş
skorları yerleşik meteorolojik tehlike yaklaşımıyla karşılaştırmaya
yardımcı olabilir. Henüz FWI hesaplanmadı veya ana modele eklenmedi.

Ana 24 saatlik hedef, bilimsel kaynak/PU kabulü, kapalı yıllar ve
rapora bağlı nihai birleştirme onayı koşulları korunur.

Son birleşik ilgili koşuda **57 test** geçti; bu aşamanın dört
betik/üç test dosyasının **yedi Python dosyası** kod/biçim kontrolü
geçti. Makbuzlardaki üretici ve sonuç dosyaları son kez güncel hash
ile doğrulandı. Testler FWI sağlayıcı dosyasının kabulü değildir;
o dosya henüz yok.
