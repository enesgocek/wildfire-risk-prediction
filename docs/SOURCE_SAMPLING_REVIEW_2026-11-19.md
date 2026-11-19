# Kaynak seçimini inceleme örneklemi — 19 Kasım 2026

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
