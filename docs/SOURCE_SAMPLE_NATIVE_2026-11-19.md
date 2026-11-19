# Kaynak örneklemi: sekiz ham geçişin sonucu — 19 Kasım 2026

Araştırmacının yedi çiftlik özel indirmesi yerelde doğrulandı. Önceki
WF1206 ile birlikte, dondurulmuş 10 kaynak satırının metadata ile
taşınabilir sekizinde birer ham çiftin nokta/çevre incelemesi tamamlandı.
Saat bağlantısı belirsiz WF1342 ve Mersin dışındaki WF1556 korundu;
yerlerine kolay kayıt alınmadı. L/Y=1 veya negatif etiket kabulü yok.
[Örnekleme tasarımı ve önceki hazırlık](SOURCE_SAMPLING_REVIEW_2026-11-19.md).

## Tamamlanan kontrol

Yedi makbuz, tamamlanma hash'i, toplam **1.258.097.196 ham bayt**, plan
kimlikleri ve yaşayan dosyalar doğrulandı. Eski tek-nokta inceleyicisi
değiştirilmeden yerelde iki işçiyle yedi kayıt işlendi. WF1206 korundu.
Sekiz çiftte **1.617 ham tarama**, **13 yerel tarama bağlamı** incelendi;
her bağlamdaki 250 m/1 km çevre ayrı tutuldu. Bunlar bağımsız yangın
veya sürekli gözlem sayısı değil. 13 bağlamın merkez/aynı-tarama 3×3
komşuluğu, QA ve koordinat uzaklığı ayrı sınırlı okumayla doğrulandı.
Bu otomatik geri okuma bağımsız insan/uzman doğrulaması değildir.

Yaklaşık köşeler aynı taramadaki komşu merkezlerden türetildi; resmî
köşeler değil. Çevreler EPSG:6933 düzleminde, uzaklıklar konum hata
ölçüsü değil. Örtüşen alanların birleşimi kullanıldı. Tarama dışı alanlar
doldurulmadı; daha uygun görünen tarama seçilip diğeri atılmadı.

## Kayıt bazında bulgu

Saat farkları ilk yerel taramanın başlangıcından hesaplanan dakikadır:
önce kaynak UTC varsayımı, sonra Türkiye saati varsayımı. Bunlar
gerçek tespit gecikmesi veya yangının sürdüğü süre değildir.

| Satır | Kaynak günü | Ham tarama | Yerel bağlam | Noktadaki maske | Saat farkları (dk) |
|---|---|---:|---:|---|---|
| WF1206 | 2018-06-24 | 202 | 1 | 5: nominal kara | 537,38 / 717,38 |
| WF1207 | 2018-06-29 | 203 | 2 | 5: nominal kara | 670,86 / 850,86 |
| WF1300 | 2019-09-15 | 202 | 1 | 5: nominal kara | 345,06 / 525,06 |
| WF1342 | 2019-11-16 | — | — | Saat bağlantısı tekil değil | — |
| WF1351 | 2020-05-17 | 201 | 1 | 5: nominal kara | 197,47 / 377,47 |
| WF1421 | 2020-10-27 | 202 | 2 | 5: nominal kara | 48,25 / 228,25 |
| WF1431 | 2021-02-12 | 202 | 2 | 1: bowtie silinmiş; 4: bulut | 18,71 / 198,71 |
| WF1504 | 2021-10-10 | 203 | 2 | 5: nominal kara | 345,87 / 525,87 |
| WF1538 | 2022-05-27 | 202 | 2 | 5: nominal kara | 604,16 / 784,16 |
| WF1556 | 2022-07-05 | — | — | Nokta Mersin dışında | — |

WF1431'in ikinci taramasında 250 m çevrenin yaklaşık **%84,35'i bulut**;
bu, tek taramadaki yaklaşık alan payı, gün boyu bulut veya etiket hata
oranı değil. Diğer noktaların 1 km çevreleri de tam/nominal kabul edilmedi:
WF1421'in bir taramasında geometrik destek %93,08, nominal-kara payı
%68,99; komşu tarama ayrı korunuyor.

Sekiz çiftte noktayı kapsayan yaklaşık desteklerde ve incelenen iki
çevrede yangın maske sınıfı 7/8/9 bulunmadı. **Bu, sekiz gerçek negatif,
%0 yakalama başarısı veya yanlış arşiv oranı değildir.** Son alan geçiş
sırasındaki aktif alan değil; söndürülme zamanı, saat standardı ve gerçek
başlangıç koordinatı bilinmiyor. Hedefler boş, gözlem `unknown`; iki olası
L önerisi ve 2.048 U anahtarı değişmedi. Birinci aşamanın kabulü açık.

## Mevcut katalogda saat ve konum bağlamı

Yeni FIRMS indirmesi yapılmadı. Yerel AOI-filtreli SNPP/NOAA-20 kataloğunda,
sekiz kaynak satırının 250 m/1 km çevreleri için üç aralık incelendi:
kaynak UTC gününün `(00:00, ertesi 00:00]` penceresi ve iki kaynak saat
yorumundan sonraki kapalı 24 saatlik tanı aralıkları `[saat, saat+24h]`.
Tanı aralıkları ana T00 hedefi yerine geçirilmedi. Önce yıl/gün metadata
süzüldü; yalnız 2018–2022 değerleri okundu. 2023/2024/2025 değerleri açılmadı.
Katalog yokluğu günlük negatif değil; dosya bütün ham granüllerin eksiksiz
küresel gözlem envanteri değil.

48 satır/yarıçap/aralık karşılaştırmasında yalnız WF1538'in 1 km çevresinde
**tek farklı katalog kimliği** bulundu: `N20_815590_170090`, 27 Mayıs 2022
**10:30 UTC**, C642/R876. Kaynak noktasına projeksiyon uzaklığı **367,60 m**;
250 m çevrede değil. Aynı kayıt iki aralıkta bulundu; iki tespit sayılmadı.

Bu saat, UTC yorumundaki 12:47'den **137 dakika önce**; Türkiye yorumu
09:47 UTC'den **43 dakika sonra**. Uyuma bakarak saat standardı seçilmedi.
İlk ham çift 22:48'de başlıyor: iki saat yorumundan da sonraki ilk metadata
geçişi seçildiği için gündüz adayı ilk çiftte değildi. İlk sonuç değiştirilmedi.

Önceki CORINE 2018 kaynak-nokta bağlamında sekiz noktanın altısı orman/çalılık,
ikisi tarım sınıfında. Bunlar yeni örtü doğrulaması veya eşik değil;
güncel olay örtüsü ve yanmış kısım bilinmiyor. İki tarım bağlamlı satır da korundu.

## Sonraki somut iş: WF1538 gündüz ham adayı

Gerçek ham koordinat, maske/QA ve yaklaşık piksel alanının kaynak
noktasıyla ilişkisi incelenecek. NOAA-20 `2022147.1030` tek ek çifti hazır:
**186.934.166 bayt**, bir işçi, 900 saniye, yerel özel Earthdata girişi.
İki tam dosya kimliği açık CMR metadata yanıtlarıyla doğrulandı.

Bu **katalog sonucuna göre seçilmiş takip incelemesi**; sonuçtan bağımsız
ilk-geçiş örneklemi diye sunulmayacak. Kaynak örneklemi ve ilk sekiz sonuç
değişmedi. FIRMS adayı bağımsız yangın kanıtı değil; aynı olay, kaynak
saati veya gerçek tutuşma konumu bu adımla kabul edilmeyecek. Yeni L,
eğitim ve nihai birleştirme yok.

```powershell
$yanginProje = 'C:\PROJELERIM\wildfire-risk-prediction'
Set-Location $yanginProje
& "$yanginProje\.venv\Scripts\python.exe" "$yanginProje\scripts\firms\run_observation_core_pair.py" --plan "$yanginProje\outputs\reports\dataset\observation_core_transfer_v1\20261119T175711Z_78d19310\native_plan.json" --run-one --prompt-login
```

Yalnız genel sonuç mesajı ve sonuç klasörü paylaşılır; giriş bilgileri
yalnız terminalde kalır. Sonrasında nokta ve katalog merkezi ayrı ham
incelenecek; örtü yorumu gerekirse somut görüntüyle araştırmacıya sorulacak.

## Çıktı kimlikleri ve doğrulama

| Çıktı | Yerel dosya | SHA-256 |
|---|---|---|
| Yedi çift indirme | `outputs/reports/dataset/source_review_queue_v1/20261119T173352Z_c8a31d03/readback.json` | `121eb4daadcb2edcd2e606cb47a5ed6a310925f3e7fbd916d85a98cc1d084ebd` |
| Yedi ham inceleme | `outputs/reports/dataset/source_sample_batch_v1/20261119T175033Z_022ebedd/readback.json` | `fb5eb9a9fb00a126864e698633cc6642069792045f7e0862826d2b3fe1059e1d` |
| Sekiz ham sonuç/10 satır | `outputs/reports/dataset/source_sample_native_summary_v1/20261119T175128Z_e277cfc3/readback.json` | `bf56b8ed36b6a12ac5c2e9c36f8ba7235013854a79cd0f93a4aaed8e3da107a0` |
| Katalog ve eski örtü bağlamı | `outputs/reports/dataset/source_sample_catalog_context_v1/20261119T175521Z_e371683f/readback.json` | `ce513b9d644f49c8f9dca46fa6962816e8e92705412aad8bbc9f2f01d7364817` |
| Tek takip planı | `outputs/reports/dataset/observation_core_transfer_v1/20261119T175711Z_78d19310/native_plan.json` | `187a1afe064b18c3226ce5f62791b8e5353deb9654b75442b8af6d3e40d97dc4` |

Yereldeki küçük tablolar `source_rows.csv` ve `scan_contexts.json`.
Yeni dört kalite komutu ve davranış kontrolleri kayıtlı. Bu devamda
**167 ilgili test** geçti: stale girdi/kod reddi, etiket/eğitim kapıları,
boş desteğin açık sayılmaması ve komşu tarama sınıflarının korunması sınandı.
İlk çalışmanın çıktıları korundu; biçim düzeltmesi sonrası toplu geri okuma
aynı yedi sonucu yeniden hesaplamak yerine doğrulanmış dosyalardan kullandı.

Bu paket kaynak–uydu aktarımındaki bulut, silinmiş piksel, saat ve geçiş
seçimi etkilerini somutlaştırdı. Küçük Mersin örneklemi dört ile genellenmedi;
PU'nun pozitif zenginliği, ortak sınıf dağılımları, sınıf/hata oranları ve
bağımsız değerlendirme koşullarının bilimsel kabulü halen açık.
