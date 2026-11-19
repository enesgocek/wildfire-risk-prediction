# Kaynak seçimini inceleme örneklemi — 19 Kasım 2026

**Aynı gün sonraki sonuç:** yedi yeni çift indirildi, sekiz kaydın ham
incelemesi tamamlandı. Önceki hazırlık kaydı aşağıda korunuyor.
[Sekiz sonuç, katalog saat bağlamı ve WF1538 takip adımı](SOURCE_SAMPLE_NATIVE_2026-11-19.md).

## Neden bu adıma geçildi?

Araştırmacının Marmaris A kararıyla C541/R878, 21 Haziran 2022 hücre-günü
için tek olası L üyeliği önerisi hazırlandı. Diğer iki ilk hücre atamasız,
M2 örtüsü belirsiz korundu. Önceki Salur önerisiyle birlikte iki kaynak
vakası için iki öneri inceleme dizininde izlenebiliyor. Hedefler boş;
bu dizin özellikleri veya nihai etiketli veri setini birleştirmiyor.

Bu iki ayrıntılı incelenmiş büyük yangın, hata içerebilen pozitif örneklem
veya dört ilde değerlendirme yeterliliği sağlamıyor. Sonraki rutin teknik
hazırlık, zaten yerelde bulunan Mersin arşivinden **uydu sonucuna bakmadan**
inceleme satırları seçmek oldu. Yeni veri talebi/yazışma açılmadı.

## Çerçeve ve dondurulan seçim

Kullanılan kaynak, 18 Kasım'da kimliği/sürümü kontrol edilen Zenodo
21455927 paketinin aynı SHA-256 ile korunan yerel kopyası:
`21bb776f1c4a4d96b25c15e72da2730eb0a4ca6472451c9f7f7a3dfb4246ae8a`.
Güncel yeni yayın sürümü araştırması yapılmadı.
[Önceki kaynak kontrolü](MERSIN_SOURCE_REFRESH_2026-11-18.md).

Örnekleme birimi yayımlanmış **coğrafi tablo satırı**, doğrulanmış bağımsız
yangın değil. Yalnız `archive_row` ve `year` alanları seçime girdi.
2018–2022 rolü dışında bilimsel değerler işleme alınmadı.

| Kaynak yılı | Coğrafi tablodaki fit-rolü satırı | Seçilen satır |
|---|---:|---:|
| 2018 | 71 | 2 |
| 2019 | 90 | 2 |
| 2020 | 84 | 2 |
| 2021 | 88 | 2 |
| 2022 | 91 | 2 |
| Toplam | 424 | 10 |

Her yılda sıralı kimlikler üzerinde, yerine koymadan PCG64 seçimi;
tohum `2026111901`. İki/yıl sayısı küçük iş akışı kontrolü için rutin
ayar, istatistiksel yeterlilik veya güç hesabı değil. Satırın kaynak/yıl
içindeki tasarım olasılığı `2/N_yıl`; bütün yangın nüfusunun seçilme
olasılığı değil. Program yalnız iki seçim sütununu kabul ediyor;
konum, son alan, kalite, örtü ve yangın sonucu sütunları verilirse reddediyor.

Seçilen kimlik dosyası **konum, saat ve son alan bağlamı okunmadan önce**
yazılıp hash ile sabitlendi. Önceki incelemelerde bazı kaynak kayıtları
görülmüştü; bu bir kör insan deneyi değil. Algoritmik seçim uydu sonucuna
bağlı değil. Arşivin kendi kayıt/seçilme yanlılığını, olay kimliğini veya
PU'nun ortak sınıf dağılımları varsayımını bu tasarım çözmüyor.

## Eksikleri çıkarıp örneklemi kolaylaştırmadık

| Kontrol durumu | Kaynak satırı | Yapılan |
|---|---|---|
| İki tablo arasındaki saat bağlantısı tekil değil | WF1342 | Örneklemde tutuldu; saat uydurulmadı |
| Koordinatın yayıncı QC değeri True, fakat nokta Mersin dışında | WF1556 | Örneklemde tutuldu; başka noktaya taşınmadı |
| Mevcut metadata ile bir hücre ve iki saat hipotezi kurulabiliyor | Diğer 8 satır | Yalnız ölçüm planı hazırlığına elverişli |

10 satırın hiçbiri kaldırılmadı veya değiştirilmedi. Sekiz satır bir
L örneklemi değil, mevcut metadata altında ölçüm aktarımı planlanabilen
alt grup. İki dosyada aynı `event_id` olduğu için olay eşitliği varsayılmadı;
tarih/yıl/ilçe/son alan imzasıyla geçici bağlantı yalnız tekil olduğunda
kullanıldı. Son alan bu bağlantı ve açıklayıcı bağlam için okundu;
seçim girdisi, tahmin özelliği veya kabul edilmiş yangın etiketi olmadı.

## İlk kontrol: WF1206

Sıra yıl/kimlik sırasıyla belirlendi. Metadata ile ölçülebilir ilk satır
WF1206, 24 Haziran 2018, bildirilen son alan 0,2 ha. Kaynak saatinin
UTC yorumu 14:12, Türkiye saati yorumu 11:12 UTC. Saat standardı ve
koordinatın gerçek başlangıç rolü henüz doğrulanmadı.

İki yorumdan da sonraki ilk kayıtlı **hücre tarama zarfı** seçildi:
SNPP, `2018175.2306`, tarama 113; kayıtlı zarf 23:09:22,529–23:09:23,093 UTC.
Bu adımda yangın, nominal kara veya kalite sayıları seçimde kullanılmadı.
Zaman/anahtar/nominal kaynak günü sütunları ayrıldıktan sonra seçim yapıldı.
Hücreye ait bir zarfın bulunması, arşiv noktasının ham taramada gerçekten
kapsandığını henüz kanıtlamıyor. Birincil hedefimizin ilk aktif uydu tespiti
zamanı bu arşiv saatine otomatik eşitlenmedi.

2018 Haziran kısmi ayının 23–25 Haziran günlük kabul edilmiş paketleri
hash ile okundu; ertelenmiş 13 Haziran paketi istenmedi. Aylık ZIP yerine
kabul edilmiş günlük teslimlerin kullanılması korundu. İlk hazırlıktaki
kaynak yolu ve zaman birimi kontrolleri düzeltilerek yeni çıktı üretildi.

CMR'den iki tam dosya kimliği/boyutu alındı. Hazırlığın tamamlanma
makbuzu kontrolü ilk eksik sürümü reddetti; doğru sırayla yazılmış yeni
makbuzlarla standart çalıştırıcı yüklemesi geçti. Önceki çıktı korundu;
aynı hash/query kontrollü kamu metadata yanıtları yeniden kullanıldı.
Yeni başarılı plan için ek CMR isteği gerekmedi.

Plan **175.717.496 bayt**, tek çift/işçi, 900 saniye; yerelde bu ham çift
yok. Ham indirme yapılmadı; araştırmacının özel Earthdata girişi gerekiyor.
İndirme sonrası nokta ve çevresinin gerçek ham taramadaki konum, maske,
kalite ve zaman durumu incelenecek. Söndürülme zamanı bilinmediği için
tespit bulunmaması gerçek yangın yokluğu veya yanlış arşiv kaydı sayılmayacak.

## Çıktılar ve sınırlar

- Marmaris önerisi: `outputs/reports/dataset/marmaris_L_proposal_v1/20261119T134021Z_5272c4bd/readback.json`;
  SHA-256 `89d0305b9f5c54809e6c1170a30c21fe1a0230da4afc65720d5eef5bc8c5f476`.
  Kaynak dizini iki öneri içeriyor; 2.048 U anahtarı değişmedi,
  iki önerinin mevcut U anahtarlarıyla kesişimi sıfır. Kesişim olsaydı
  sonucu gördükten sonra U'dan çıkarma yapılmayacaktı.
- Dondurulmuş örneklem: `outputs/reports/dataset/source_sampling_review_v1/20261119T133150Z_f94ebe6e/readback.json`;
  SHA-256 `9647a69248ac158aad6f7a864b48bfad8eb61860be08ff3250f8dc643cd4d453`.
  `frozen_selected_keys.csv` SHA-256:
  `e8dfaa9130658cc0072ded7834d473d24689ec616fd91c04aed6bf5fd5ea05dd`.
- İlk geçiş: `outputs/reports/dataset/source_sample_first_pass_v1/20261119T133541Z_a7fafe0c/readback.json`;
  SHA-256 `36d209d4c5c6b6c9b656c5c57f49b22a2f9736c65f9b150494f24c136c51faa3`.
- Yerel indirme planı: `outputs/reports/dataset/observation_core_transfer_v1/20261119T133754Z_a9bf9118/native_plan.json`;
  SHA-256 `7197276b8d097a1907b268b78e0772b4481c15691bcfe8d8787932e57bf3f996`.
- Kapanış: `outputs/reports/dataset/noisy_PU_source_review_closure_v1/20261119T134140Z_f85a8421/readback.json`;
  SHA-256 `85a25233821323d4439103ed5c77949dac4ce789cab8dd4cffc2659c7d73e30f`.

Yeni yapılandırmalar `configs/marmaris_L_proposal_v1.json` ve
`configs/source_sampling_review_v1.json`; komutlar
`scripts/quality/prepare_marmaris_L_proposal.py`,
`prepare_source_sampling_review.py`, `prepare_source_sample_first_pass.py`,
`prepare_source_sample_native_pair.py`. Ortak seçici
`src/wildfire_risk_prediction/source_review_sampling.py`.

Bu devamda **124 ilgili davranış testi** geçti. Kaynak/girdi/çıktı hash'leri,
öneri/atamasız hücre bölümleri, boş hedefler, değişmeyen U ve yerel plan
sınırları geri okundu. Bu kontrol örneklemi şimdilik yalnız Mersin'de;
dört ile genellenmedi. Yeni sınıf/hata oranı veya model başarısı ölçülmedi.
Gözlem `unknown`, etiket izinleri kapalı. Birinci aşamanın bilimsel kabulü,
eğitim ve nihai birleştirme açık onay/kanıt kapılarında kalıyor.

## Aynı gün WF1206 ham sonucu ve yedi çiftlik kuyruk

Araştırmacı özel Earthdata indirmesini tamamladı. Sonuç dosyasının tamamlanma
makbuzu, plan hash'i, 175.717.496 ham baytın iki dosya hash'i ve gerçek
InputPointer/boyut/zaman başlıkları yerelde doğrulandı. Bu bölüm önceki
indirme-bekliyor durumundan sonra elde edilen yeni sonuçtur.

### Tek geçişte gerçekten ne görüldü?

Ham çiftte **202 tarama** ayrı okundu. Kaynak noktası ve 1 km çevresini
kesen yerel yaklaşık destek yalnız tarama **113** içinde bulundu:
24 Haziran 2018 **23:09:22,529–23:09:23,093 UTC**. Tarama kalite alanı
0; `sensor_mode` ham değeri 5 ayrıca saklandı, yeni anlam ataması yapılmadı.

| İnceleme birimi | Yerel sonuç | Sınır |
|---|---|---|
| Kaynak noktası | Kapsayan yaklaşık pikseller maske 5, nominal kara | Gerçek tutuşma koordinatı olduğu doğrulanmadı |
| 250 m ve 1 km çevre | Yaklaşık destek ve maske 5 alanı yaklaşık %100; diğer maske sınıfları 0 | EPSG:6933 düzleminde komşu merkezlerden türetilmiş alan; resmî piksel köşeleri değil |
| En yakın ham merkez | Satır 3628, sütun 2004; maske 5, ham QA 0 | 191,51 m projeksiyon uzaklığı konum doğruluk ölçüsü değil |
| Merkezin 3×3 komşuluğu | Dokuz değerin tamamı maske 5 | Ayrı sınırlı ham okuma ile yeniden doğrulandı |
| Kaynak saatine göre fark | UTC yorumunda 537,38 dk; Türkiye yorumunda 717,38 dk | Tespit gecikmesi veya yangının sürdüğü süre değil |

Geometri aynı tarama içindeki komşu merkezlerden türetiliyor; kenar
satır/sütunları yeniden kurulmadı. Alanlar piksel örtüşmelerini toplayarak
değil birleşimlerini alarak hesaplandı. Kaydedilen yaklaşık 1 payındaki
10^-14 mertebesindeki kayan nokta farkları raporda elle düzeltilmedi;
kapanışta 10^-12 toleransla kontrol edildi. Bu tek geçişte, bu iki
yaklaşık çevrede yangın/bulut maske sınıfı bulunmadı.

**Bu sonuç negatif etiket değildir.** Bildirilen son alan 0,2 ha,
geçiş sırasındaki aktif alan değil. Söndürülme zamanı, saat standardı ve
koordinatın başlangıç rolü bilinmiyor. Geçişin bildirilen zamandan yaklaşık
9 veya 12 saat sonra olması da yokluğu yorumlamayı sınırlar. Kaynağı yanlış
ilan etmedik; yeni L önerisi veya Y=0/1 üretmedik. Günlük gözlem hâlâ
`unknown`, negatif/pozitif etiket izinleri kapalı.

### Kalan yedi satırın ölçüm hazırlığı

Yalnız dondurulmuş örneklemdeki metadata ile taşınabilir sekiz satırdan
ham incelemesi tamamlanan WF1206 ayrıldı. Kalanlar **WF1207, WF1300,
WF1351, WF1421, WF1431, WF1504 ve WF1538**. Saat bağlantısı belirsiz WF1342
ve Mersin dışı koordinatlı WF1556 örneklemde tutuluyor; yerlerine satır
alınmadı. 10 satırın biri ham incelendi; yedisi indirme bekliyor; ikisinin
kaynak metadata engeli sürüyor. Bunlar veri setinin tamamlanma yüzdesi değildir.

Her satır için iki saat yorumundan da sonraki ilk kayıtlı hücre geçişi,
en fazla 24 saatlik metadata aralığında seçildi. Yangın/kalite sayıları
seçim tablosundan ayrıldı; bu değerlere göre kolay geçiş seçilmedi.
Hücre taramasının bulunması noktanın gerçek ham kapsamasını kanıtlamıyor;
her satırda indirme sonrası ayrıca kontrol edilecek. Fit rolü 2018–2022
korundu; 2023 kalibrasyon, 2024 karşılaştırma ve 2025 kapalı test değerleri
bu devamda işlenmedi.

14 tam dosya için ürün başına gruplu **dört açık CMR metadata sorgusu**
yapıldı. Kimlik/boyut/zaman ve tek dosya URL politikaları doğrulandı;
ham veri ya da kimlik bilgisi istenmedi. Yedi plan standart tek-çift
çalıştırıcısıyla geri yüklendi. Toplam boyut **1.258.097.196 bayt**
(yaklaşık 1,26 GB / 1,17 GiB). Özel indirme henüz başlamadı.

Yeni küçük kuyruk mevcut tek-çift güvenli aktarıcıyı değiştirmeden çağırır:

- Özel giriş bir kez, yalnız terminalde; parola/token rapora veya komuta yazılmaz.
- Bir işçi; her çocuk 900 saniye. Özel giriş sonrası indirme kuyruğu 3.600
  saniye; 930 saniyelik rezerv kalmadan yeni çift başlatılmaz.
- İlk hata veya süre rezervinde durur; ham/kısmi dosyaları korur.
  Kendiliğinden yeniden deneme/başlatma veya dosya silme yok.
- Yeniden elle çalıştırıldığında yalnız tamamlanma makbuzu, plan ve
  yaşayan ham bayt hash'leri doğrulanan çiftler atlanır.
- Yalnız bayt/başlık kontrolü; mekânsal kabul, günlük gözlem, etiket,
  model eğitimi ve bulut işi başlatılmaz. Mekânsal inceleme sonra yerelde yapılır.
- `--run` verilmeden yalnız hazırlık kontrolü yapılır; indirme başlamaz.

Araştırmacının PowerShell'de çalıştıracağı komut:

```powershell
$yanginProje = 'C:\PROJELERIM\wildfire-risk-prediction'
Set-Location $yanginProje
& "$yanginProje\.venv\Scripts\python.exe" "$yanginProje\scripts\firms\run_source_review_queue.py" --plan "$yanginProje\outputs\reports\dataset\source_review_queue_v1\20261119T141303Z_9c1e2156\queue_plan.json" --run --prompt-login
```

Bitince yalnız genel durum ve sonuç klasörü paylaşılır; parola, token,
bağlantı veya terminal dökümü paylaşılmaz. Süre sınırına ulaşırsa yedi
çiftin tamamlandığı varsayılmaz; makbuzdan gerçek biten sayısı okunur.

### Yeni çıktı kimlikleri ve doğrulama

| Çıktı | Yerel dosya | SHA-256 |
|---|---|---|
| WF1206 indirme makbuzu | `outputs/reports/dataset/observation_core_native_v1/20261119T134819Z_b9d99fad/native_probe.json` | `a675b5c25b90b2a78fd1da70dfacca0697a3e2b61af0e4f90164cfe1d4e77d4c` |
| WF1206 nokta/çevre | `outputs/reports/dataset/source_sample_point_v1/20261119T140051Z_000dc2bf/readback.json` | `9970de0d18f2717c0f72294e35a61938f55af452d034d3f341e2ecc10edc7efa` |
| Kalan yedi metadata | `outputs/reports/dataset/source_queue_metadata_v1/20261119T140541Z_58ea114d/readback.json` | `5980e221bd3d74eff6ad6b17fd17fb11c48fe5e9aa6373eb1aaa30c2f88da04d` |
| İndirme kuyruk planı | `outputs/reports/dataset/source_review_queue_v1/20261119T141303Z_9c1e2156/queue_plan.json` | `dc6f2e51af888f7650a6a3652d50286f5c6d3b06becc91590a2929f246f27f01` |
| Ayrı geri okuma/kapanış | `outputs/reports/dataset/source_review_closure_v1/20261119T141502Z_a8204f2c/readback.json` | `548f9976667c22dd88a57bd009650e8aa972f38ba32b1e4f6d82c106f47c7776` |

Yeni komutlar: `audit_source_sample_point.py`, `prepare_source_queue_metadata.py`,
`prepare_source_review_queue.py`, `audit_source_review_closure.py` (quality)
ve `scripts/firms/run_source_review_queue.py`. Eski hash-bağlı aktarıcı,
geometri hesabı ve önceki çıktılar değiştirilmedi.

Bu devamda **154 ilgili test** geçti: kaynak örnekleme ve yeni kuyruk,
alan birleşimi/sınıf sınırı, L2 geometri, güvenli aktarım ve hedef kabul
testleri. Yeni 24 kuyruk testi kapsam/süre/etiket kapılarının genişletilmesini,
örnek değiştirmeyi, sonraki veri rollerini, giriş bilgilerinin kalıcılaşmasını,
ilk hatadan sonra ilerlemeyi ve süre rezervini kontrol ediyor.
Ayrı kapanışta ham 3×3 tanık/koordinat uzaklığı ve kod/girdi hash'leri
geri okundu; önceki iki olası L önerisi ve 2.048 U anahtarı değişmedi.

Bu kontrolün katkısı, ayrıntılı büyük yangın anlatılarıyla sınırlı kalmadan
kaynak satırlarının uydu ölçümüne nasıl taşındığını sınamak. Küçük, yalnız
Mersin'e ait 10 satırlık kontrol genellenebilir başarı, sınıf/hata oranı veya
PU kabulü sağlamaz. Önce kalan ölçümler, ardından birlikte yöntem koşulları
incelenecek; birinci aşamanın bilimsel kabulü hâlâ açık.
