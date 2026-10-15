# Yerel gözlem pilotu kuyruğu ve zaman kanıtıyla aktarım azaltma

Tarih: 15 Ekim 2026. Kapsam: önceden sabitlenmiş 12 eğitim günü ve
156 amaçlı hücre-gün. 72 aylık ana üretim ve özellik takvimi değiştirilmedi.
Bu kuyruk yöntem pilotunu ilerletir; bütün döneme ait etiket kabulü değildir.

## Kullanıcı müdahalesi olmadan tamamlanan işler

1. İlk çiftin alanları tarama bazında yeniden kuruldu; zaman, kalite,
   sensör/yörünge ve hücre geometrileri aynı kayıtla bağlandı.
2. Sabit kohortun bütün satırlarını koruyan kısmi kaynak özeti üretildi.
   Eksik kaynaklar sıfır gözlem/negatif etiket olarak kabul edilmedi.
3. Gerçek tamamlanmış çiftin checkpoint'i yeniden kullanılarak ikinci
   denemede aynı sonuç ve CSV hash'i elde edildi; tekrar hesaplanmadı.
4. 292 çiftin saklanmış native tarama zamanı kayıtları doğrulandı.
   Kesin olarak hedef penceresi dışındaki kaynaklar için yeniden ham
   alan hesabının gereksiz olduğu ölçüldü; sınırdaki kaynaklar korundu.
5. Yeni sürümlü, disk/süre sınırı ve özel giriş kapısı olan devam planı
   üretildi; kimlik bilgisi olmadan önbellek modu gerçekten çalıştırıldı.

Yeni uzak veri aktarımı, bulut işi, dosya silme, etiket veya nihai
birleştirme yapılmadı. Kullanıcıya ait bağlantı/token dosyaları okunmadı.

## İlk tarama-geometri denemesi ve devam kanıtı

V1 referans planında bütün 292 çift envanterdeydi. Yereldeki
SNPP:2018045.0000, 15 Şubat 2018 kohortunun sekiz seçilmiş hücresi için
işlendi: **203 tarama × 8 hücre = 1.624 satır**, bu hücrelerde
**1.016 piksel merkezi**. Her sınıfın tarama geometrileri birleştirilerek
ayrı granül alan hesabıyla karşılaştırıldı; konum farkı tolerans içinde
eşleşti. Üç GPKG katmanının kaydedilen geometrileri tekrar okundu.

Kaynak 14 Şubat 00:00–00:06 UTC'dir. 15 Şubat hedef penceresinde bu
203 tarama **outside** durumundadır; önceki günün desteği ertesi günün
gözlemi gibi kullanılmadı. 156 satırlık kısmi özette hiçbir hedef atanmadı.

İlk çalışma:
`outputs/reports/dataset/observation_pilot_run_v1/20261015T112305Z_0b39c271/`.
Gerçek yeniden başlatma:
`outputs/reports/dataset/observation_pilot_run_v1/20261015T112416Z_2f5ecc88/`.
İkisinin `readback.json` SHA-256 değeri aynıdır:
`3f2994d2edd1d3c9d39868e966fa666919c09d55d2397ecc056e67849015dd88`.
Kısmi özet SHA-256:
`7c24cd8b4e457017f8723391cdb4717e5ee92f7a7ec7e3b123f566ed3ef4cffa`.
Tarama-geometri çift raporu SHA-256:
`273d21f5be4b89c848e35e5b8752259327c37e9263c49b12b5c36f78eadb9e6e`.

Zaman filtresi geliştirilmeden önce bu V1 çalışmasının 28 bağlı Python
girdisi, `outputs/reports/dataset/observation_pilot_queue_code_v1/20261015T113000Z_v1_preserved/`
altında ayrı kod snapshot'ıyla korundu. Snapshot makbuzu SHA-256:
`47131500c3d62d3fbd797cb23020b98b255b628b0234c20aba46719132e0719f`.
Eski plan ve sonuçlar elle değiştirilmedi; V2 yeni plan/hash ve iş alanı kullanır.

## Zaman kanıtıyla güvenli kaynak ayrımı

36 kaynak gününün kabul edilmiş aylık/günlük arşivlerinden `report.json`
ve `scans.csv` okundu. Ay arşivi hash'i, günlük rapor hash'i ve rapora
bağlı CSV hash'i doğrulandı. Her çiftte kaynak adı/sürümü/bayt/SHA,
native dizi yüksekliği/32 ile tarama sayısı, kesintisiz tarama indeksleri,
detektör satır bağı ve zaman sırası eşleşti. İlk çiftteki 203 taramanın
başlangıç/bitiş/orta zamanları yeniden açılan native dosya sonucuyla
nanosaniye düzeyinde aynı bulundu.

Her tarama gerçek zaman zarfıyla `(T,T+24h]` karşısında sınıflandı:
**bir çift yalnız bütün taramaları outside ise ham geometri kuyruğundan
çıkarılabilir.** Tek bir inside veya boundary_unknown tarama varsa çift
korunur. Eksik/tekrarlı/bozuk tarama tanığı dışlama izni vermez.
Nominal gün adına göre topluca önceki/sonraki gün silinmedi. İki saniyelik
native/nominal sanity kontrolü dışlama marjı değildir; dışlama gerçek
tarama başlangıç/bitişleriyle yapılır.

| Kapsam | Çift | Ham dosya | Kayıtlı bayt |
|---|---:|---:|---:|
| Bütün komşu gün envanteri | 292 | 584 | 53.517.820.515 |
| Tam zaman tanığıyla pencere dışında | 194 | 388 | 35.522.365.754 |
| Ham geometri için korunan | 98 | 196 | 17.995.454.761 |

Yeni ham aktarım gereksinimi **%66,37** azalır; kalan yük ondalık
**18,00 GB**'tır. Bu ölçü kaynak baytı karşılaştırmasıdır; indirme/işleme
hızının aynı oranda arttığı veya aynı miktarda nakit tasarrufu sağlandığı
iddia edilmez. Aynı 12 gün, 156 birim ve bütün 292 çiftin zaman muhasebesi
korunur; olay/gözlem kabul eşiği değiştirilmedi.

Bu kanıt, önceki kabul edilmiş native türevlerden gelir. 584 ham dosyanın
bu aşamada yeniden açıldığı veya 98 çiftin yeni geometrisinin doğrulandığı
söylenmez. Native doğruluğun eski kabul sınırları korunur.

Uyarılı ilk tanı çalışmasından sonra Timestamp karşılaştırması açık
nanosaniye tamsayılarıyla düzeltildi. Değişken ISO alt-saniye biçimleri
projenin mevcut açık UTC ayrıştırıcısına bağlandı. Uyarıları hata sayan
yeni tam çalışma ayrı dizinde tamamlandı:
`outputs/reports/dataset/observation_pilot_time_triage_v1/20261015T112942Z_8cd17175/`.
Readback SHA-256: `dc01d0c302416a3cdc448558ec7729ecf7aaf5abb2d77a12ab8ba6b6917173f8`.
Kapanış SHA-256: `d8f8b74f92e578a33ae06e4900794349d23c207be90cec8a75806d8fc50e7ef0`.

## V2 devam planı ve gerçek önbellek kontrolü

Yeni plan:
`outputs/reports/dataset/observation_pilot_queue_v2/20261015T114055Z_a141e892/`.
Plan SHA-256: `af4a8e1d7c6e8929cbb2a998864acb1ad7814f1bbd4a74a6cb4fd09acfc1112b`.
Readback SHA-256: `c517062db64d26a68f9d0e9dd35c2b0bf82ee5610bd6a7a48d6e407161f5c737`.
Kapanış SHA-256: `03f384068c588f69ba20a9789376c23dfd8c76ae662580f04981b1f7345697b1`.

**156 bağlı girdi** doğrulandı; bu sayı 156 hücre-gün sayısından ayrı bir
dosya kapanışı ölçüsüdür. 22 donmuş üretim girdisi aynı kaldı. Hazırlık
anında 102.398.103.552 bayt boş disk vardı. Kurallar:

- Tek işçi, toplam **4 saat üst sınır**, çift aktarımına en fazla
  900 saniyelik deadline. Üst sınır bitiş garantisi değildir.
- Ham önbellek 20 GB; 20 GB boş disk ve 10 GB türetilmiş çıktı rezervi.
  Her çiftte güncel disk koşulu yeniden denetlenir; ham dosya silinmez.
- Boyut/tarihsel SHA ve varsa sağlayıcı checksum'u, aynı CMR nesnesine
  tek kimliksiz CDN adımı, native eş kaynak ve zaman koşulları korunur.
- Tamamlanan çiftin çıktı makbuzu/hash'leri tekrar doğrulanarak kullanılır.
  Kısmi dosya otomatik silinmez veya bozuk tam dosyanın üzerine yazılmaz.
  Hata halinde iş durur; tamamlanan çiftler ve tanı kayıtları korunur.
- Sert süre aşımında yazıcı kilidi kalabilir; süreç/kilit/kısmi dosya
  denetimi yapılmadan kilit silinerek zorla yeniden başlatılmaz.
- Özel giriş yalnız etkileşimli yerel terminalde, persist=false.
  Kullanıcı adı/parola çocuğa taşınmaz; token yalnız çocuk ortamında olur.
  Çıktı sıfır koduyla bitse bile makbuz/artefakt kapanışı olmadan kabul edilmez.

Bir aktarım hatası varsa kesin toplam ağ baytı alanı `null` kalır;
yalnız tamamlanan dosyaların aktarım baytı ayrıca kaydedilir. Yarıda
kalan yanıtın tüm ağ trafiği ölçülmüş gibi sunulmaz.

Gerçek kimliksiz çalışma:
`outputs/reports/dataset/observation_pilot_run_v1/20261015T114102Z_e3e803a5/`.
Durum `cache_review_complete_missing_private_transfer`: gerekli 98 çiftin
hiçbiri yerelde yok; **0/98 ham geometri çifti**, 194 zaman dışlama tanığı,
156 korunan inceleme satırı ve sıfır yeni ağ baytı. Bu bir tamamlanmış
geniş pilot değildir. Önceki 1/292 denemesi silinmedi; o çift yeni kuyrukta
zamanla dışlananlar arasındadır. Sayaçlar aynı işi ölçmez.

Çalışma readback SHA-256:
`890c96f4190c99c4276db5f21d69fb0fe54ced37fcdce91189f8a0aa3cf65918`.
Kapanış SHA-256: `2fc655044804356e8746d49b4299d42f43562e449e12d4a0e1ea6c81f8675c39`.
156 satırlık özet SHA-256:
`f5c9b0e05f4475094a804fdbb662923c2afde75ba4216d5207b0d8ce2101f445`.

**36 yeni davranış vakası dahil 197 ilgili test** geçti. Eksik kaynak,
zaman sınırı, tarama/konum eşliği, boş destek, tam olmayan dışlama tanığı,
değişmiş kaynak/bayt, özel girişte ortamın geri yüklenmesi, giriş çıktısının
bastırılması, etkileşimsiz girişin reddi ve timeout korumaları sınandı.
Makbuzsuz sıfır çıkış senaryosu başlatıcıdaki bir hata kaydını yakaladı;
makbuz artık finally içinde başarısız durumda da yazılır ve sahte başarı
verilmez. Deprecation/Future uyarıları hata sayıldı. On yeni Python
dosyasında lint/format geçti. Geniş aktarım yolu sentetik kontrollerle
sınandı; gerçek kimlikli 98 çift aktarımı henüz yapılmadı.

Son ağ muhasebesi kaydı değişikliğinden sonra etkilenen beş başlatıcı/
özel giriş testi ayrıca geçti; yeni plan üretildi ve kimliksiz gerçek
çalışma tekrar tamamlandı. Yukarıdaki makbuz kimlikleri bu son sürüme aittir.

## Kullanıcı dönünce gereken tek adım

Kendi PowerShell terminalinde aşağıdaki komut çalıştırılır. Kullanıcı adı
ve parola ekranda gizli istenir; sohbet veya terminal dökümü paylaşılmaz.

```powershell
& "C:\PROJELERIM\wildfire-risk-prediction\.venv\Scripts\python.exe" "C:\PROJELERIM\wildfire-risk-prediction\scripts\firms\run_observation_pilot_queue.py" --latest-plan --prompt-login
```

Bu yerel bir iştir; VM gerekmez. Terminal ve bilgisayar açık kalmalı,
bilgisayar uykuya geçmemelidir. İnternet kesintisi veya kaynak hatası
tamamlanan çiftleri silmez; bir sonraki başlatma önce checkpoint kontrolü
yapar. Hata/kilit/kısmi dosya varsa inceleme gerekir. Normal tamamlanmada
kuyruk kendi biter; bilgisayarı veya VM'yi kapatmaz. 4 saat sınırı dolarsa
tamamlanan çiftler korunur ve sonraki oturuma devam gerekir.

İzleme için komutun yazdırdığı sonuç klasöründeki `progress.json` ve
`worker.log` salt okunur incelenebilir; ilk çift tamamlanmadan progress
dosyası oluşmayabilir. Parola/token/imzalı URL paylaşılmamalıdır.

Tüm satırlarda unknown/negative=false ve boş hedef korunur. Bağımsız olay
referansı, negatif etiket gerekçesi, model ve nihai birleştirme ayrı kabul
kapılarıdır; bu kuyruğun tamamlanması bunların otomatik kabulü değildir.

## Gerçek aktarım kesintisi ve korunan devam noktası

15 Ekim özel girişli gerçek çalışma
`outputs/reports/dataset/observation_pilot_run_v1/20261015T121531Z_911c43a7/`
durumu `failed_checkpoints_retained` olarak kapandı. Başlatıcının
`child_failed_outputs_retained` mesajı bu başarısız denemeyi doğru yansıtır;
tamamlanan çiftlerin kaybolduğunu veya etiket kabulünü ifade etmez.
Readback SHA-256:
`598b9fd63092d312e1c71c3d9aa22024a56288301204c90784f3e1422e270dc7`.

Gerekli **98 çiftin 86'sı** tamamlandı; **12 çift** eksik kaldı.
156 sabit birimin 130'unda planlanan kaynaklar tamdır; bu bir günlük
gözlem yeterliliği veya negatif etiket kabulü değildir. Tamamlanan dosya
aktarımları 15.785.318.661 bayttır; kesilmiş aktarım nedeniyle kesin toplam
ağ trafiği bilinmez (`network_bytes=null`).

Hata, `SNPP:2023227.1036` konum dosyasının gövdesi okunurken
`ConnectionError` sınıfında oluştu. Kaynak 303 yönlendirmesi ve son HTTP
200 kayıtlıdır; tam nesne/sorgu korumaları geçmiştir. Kayıt bir giriş
reddi göstermez; kesintinin yerel bağlantıdan mı uzak servisten mi
kaynaklandığını belirlemez. Yeni kimlik bilgisi veya ücretli yükseltme
gerektiği sonucu çıkarılmadı.

Çevrimdışı, bu rapor kimliğine bağlı dar kurtarma betiği
`scripts/quality/recover_observation_pilot_transfer.py` çalıştırıldı.
Aynı kuyruk yazıcı kilidi altında 86 çiftin **172 ham dosyası**, toplam
**15.782.215.707 bayt**, tam boyut/tarihsel SHA ve varsa sağlayıcı checksum'u
ile yeniden doğrulandı. Hatalı çiftin tamamlanmış yangın dosyası ayrıca
kontrol edildi. Planın 156 bağlı girdisi ve başarılı çift makbuzları
tekrar geçti; bilimsel kod, plan ve checkpoint alanı değiştirilmedi.

Tek yarım dosyanın **40.894.464 baytı** hash alınarak etkin ham önbellekten
ayrı `retained_partial/` teşhis dizinine taşındı; taşıma sonrası boyut/hash
aynıdır. Kaynak veya kabul edilmiş çıktı silinmedi/üzerine yazılmadı.
Yarım dosya native kaynak sayılmadı. İlgili konum dosyası sonraki özel
girişte tam **183.347.040 bayt** olarak yeniden istenir; HTTP Range ile
yarım gövdeden devam edilmez. Diğer tamamlanmış çiftler makbuz kontrolüyle
yeniden kullanılır.

Kurtarma dizini:
`outputs/reports/dataset/observation_pilot_recovery_v1/20261015T133507Z_9568106e/`.
Readback SHA-256:
`69f179452f6d219beda129cae7c391cff422fe5d02d85bd7297cf937564d8729`.
Kapanış SHA-256:
`63c114abeb75d3aeec62cdc2a53dd4906120411163bec79980bb65a8b18191b6`.
Korunan kısmi dosya SHA-256:
`998ae542096d34df01bc8743a3950f74287a7b48af93f26a89544b6c58898e46`.

Yedi yeni kurtarma vakası dahil **91 ilgili test**, Deprecation/Future
uyarıları hata sayılarak geçti. İki yeni Python dosyasında lint/format
kontrolü geçti. Kurtarma ağ kullanmadı, kimlik bilgisi okumadı ve bulut
işi başlatmadı. Kalan 12 çift için yukarıdaki aynı özel giriş komutu
kullanılır; bu aşamada tam pilot veya etiket/model kabulü yoktur.

Kurtarma sonrası **gerçek kimliksiz devam kontrolü** tamamlandı:
`outputs/reports/dataset/observation_pilot_run_v1/20261015T133620Z_a8d3212a/`.
86 çift mevcut makbuzlarından yeniden kullanıldı; 12 eksik çift, 130/156
planlanan kaynakları tam birim, sıfır ağ baytı ve `failure=null` kaydedildi.
Durum `cache_review_complete_missing_private_transfer`; günlük gözlem
kabulü değildir. Etkin önbellekte kısmi dosya ve yazıcı kilidi kalmadı.
Readback SHA-256:
`0dba21ab260cfd3a4571f18d6c4109b6d117a81c53c93dfc845f153e3d95dd45`.
Kapanış SHA-256:
`7f3ad9af89cae7e448bd9bba88046bff29aee4e1c177ede0ca3370dcb3d8fb91`.
