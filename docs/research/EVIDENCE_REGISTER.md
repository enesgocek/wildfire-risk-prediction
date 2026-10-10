# Araştırma kanıt dizini

Son editoryal güncelleme: 10 Ekim 2026. Bu dizin birincil çıktılara yönlendirir;
buraya satır eklenmesi yeni bir bilimsel doğrulama yapıldığı anlamına gelmez.

## Kanıt düzeyleri

- **Yerel denetim kaydı:** belirtilen rapor kapsamında dosyalar geri okunmuştur.
- **Uzak çalışma çıktısı:** çalışma sırasında alınan log/progress sonucu; yeni yerel kabul değildir.
- **Manuel bildirim:** ekran veya işlem durumu aktarımı; canlı API sorgusu değildir.
- **Açık konu / plan:** tamamlanmış sonuç olarak kullanılamaz.

| Kimlik | İddia / konu | Kanıt ve kapsam | Sınır |
|---|---|---|---|
| E01 | Dört il ve 2.899 coğrafi hücre | [Coğrafi hazırlık](../PROJECT.md#çalışma-alanı-kararı), `data/aoi/manifest.json` | Bütün hücreler henüz uygun bitki örtüsü örneği değildir |
| E02 | 2018–2024 meteorolojisi hazır | [Meteoroloji kuralı](../WEATHER_POLICY.md), [kalite kaydı](../QUALITY_REVIEW_2026-10-02.md) | 7.412.743 hücre-gün; gerçek zaman tahmin erişimi doğrulanmadı |
| E03 | İki sensörden 33.255 aday tespit | [FIRMS incelemesi](../PROJECT.md#firms-arşivi-ve-gözlem-kapsamı--1-ekim-2026) | Olay sayısı ve doğrulanmış nihai etiket değildir |
| E04 | Temmuz 2023 gözlem tanıları denetlendi | [Aylık sonuç](../COLAB_MONTH_RESULTS_2023_07.md) | Günlük gözlem unknown; negatif etiket izni yok |
| E05 | İlk GCP oturum sonuçları geri okundu | [İlk oturum denetimi](../GCP_FIRST_SESSION_RESULTS.md) | Rapordaki günlük/aylık ve geometrik tekrar hesaplama sınırları geçerli |
| E06 | 24/4 hattı aynı VM baz ortalamasından 1,4655 kat hızlı | [Hızlandırma deneyi](../GCP_ACCELERATION_RESULTS_2026-10-08.md) | Üç günlük iş yükü; tüm dönem veya donanım etkisi garantisi değil |
| E07 | İki Aralık kaynağında gerçek geolocation girdisi uyuşmuyor | [Başlık denetimi](../GCP_GEOLOCATION_HEADER_CAPTURE_2026-10-09.md), [devam planı](../GCP_SOURCE_AWARE_CONTINUATION_2026-10-09.md) | 31 Aralık ertelendi; Aralık tam ay sayılamaz |
| E08 | Son uzak ilerleme: Aralık 2022–Kasım 2023 on iki tam ay; Kasım 2022 1–8 ve Aralık 2023 1–30 | [Oturum kapanışı](../GCP_CONTINUATION_FAILURE_2026-10-09.md), [9 Ekim günlüğü](../../Diary/09-10-2026.md) | Hatalı kapanış/korunan kayıt bildirimi; yeni sonuç arşivi yerelde denetlenmedi |
| E09 | FIRMS ekibi yazışmayı incelemeye aldı | [Kaynak bildirimi](../PROJECT.md#9-ekim-2026--nasa-firms-inceleme-bildirimi) | Manuel bildirim; Type teknik teyidi değil |
| E10 | Nihai model ve olay/etiket veri seti | [Güncel durum](../STATUS.md) | Henüz hazır değil; tahmin performansı ölçülmedi |
| E11 | 2.899 hücre için arazi/örtü adayı ve 32 hücre için geçmiş NDVI/NDMI örneği | [Arazi ve bitki örtüsü hazırlığı](../LANDSCAPE_PREPARATION_2026-10-09.md), `outputs/reports/landscape/local_readback.json` | Ham EE integrallerinden yerel geri okuma; bağımsız saha/DEM doğrulaması değil; günlük seri henüz yok |
| E12 | Aynı 32 hücrede dört mevsim/üç pencere için 384 özet ve 8.448 günlük eşleştirme örneği denetlendi | [Mevsim karşılaştırması](../VEGETATION_WINDOW_REVIEW_2026-10-09.md), `outputs/reports/landscape/seasonal_v1/local_readback.json` | Eğitim örneği; bütün dönem veya operasyonel erişim doğrulaması değil; model katkısı ölçülmedi |
| E13 | Kasım 2022 planı ve kalan 19 tam çift ZIP ağ kapalıyken bilimsel geri okumadan geçti | [Kapanma arşivi denetimi](../GCP_CONTINUATION_FAILURE_2026-10-09.md), `outputs/gcp_acceleration/continuation_failure_2026-10-09/readback_network_blocked/failure_readback.json` | 10 görev kısmi; bütün 12 ayın bağımsız kabulü veya kesin hata nedeni değil |
| E14 | Salt okunur Drive teşhisi ve 19 yerel payload ile kimlik/hash/boyut çapraz kontrolü geçti; V2 native checkpoint tekrar kullanım denemesi başarılı | [V2 devam ve tanı](../GCP_SOURCE_AWARE_V2_2026-10-09.md), `outputs/gcp_acceleration/continuation_failure_2026-10-09/publication_probe_verified.json` | Güncel erişim kanıtı, eski hatanın kök nedeni değil; 10 Ekim'de V2 uzak oturumu sürüyor, oturum sonu kabulü bekleniyor |
| E15 | 2.899 hücrede tek eğitim tarihinin iki pencereden 5.798 özeti denetlendi; eski örneğin 64 satırı eşleşti ve ağ kapalı 92 checkpoint yeniden kullanıldı | [Tam grid denemesi](../VEGETATION_FULL_GRID_2026-10-10.md), `outputs/reports/landscape/full_grid_v1/2018-08-01_b64/` | Tek tarih; günlük/aylık seri, saha doğrulaması veya operasyonel erişim onayı değil |

| E16 | Ağustos 2018 için 28.990 haftalık özetten 179.738 günlük bitki örtüsü adayının iki yerel geri okuması geçti | [Aylık eğitim denemesi](../VEGETATION_MONTH_2018_08_2026-10-10.md), `outputs/reports/landscape/month_v1/2018-08/` | Tek eğitim ayı; geçmiş erişim bilinmiyor; haftalık özet taşınıyor, taze günlük görüntü/etiket/model değil |

| E17 | Şubat 2018 için 162.344 yeni günlük aday kabul edildi; Şubat/Ağustos toplam 342.082 satırın bağımsız destek/yaş incelemesi geçti | [Kış–yaz tam grid incelemesi](../VEGETATION_TRAINING_SUPPORT_2026-10-10.md), `outputs/reports/landscape/month_comparison_v1/winter_summer_training_2018_v1.json` | 72 eğitim ayının ikisi; kış kısa penceresinde %13,845 eksik; etiket/model/operasyonel erişim yok |

E18 — 10 Ekim: [Habitat ön incelemesi](../HABITAT_REVIEW_2026-10-10.md)
bütün 2.899 statik hücreyi ve 15 örtü/eşik senaryosunu geri okudu.
Kanıt: `outputs/reports/habitat/review_v1/20261009T235212Z_3c2c021b/`.
Sınır: matematiksel sınıf/alan çapraz kontrolü; uygunluk, yangın etiketi,
güncel habitat doğruluğu veya uzman onayı değildir.

E19 — 10 Ekim: [Olay gruplaması geri okuması](../EVENT_GROUPING_REVIEW_2026-10-10.md)
30.295 eğitim adayının dokuz bağlantı grafiğini eski atamalarla iki yönlü
eşleştirdi; ilk zaman/hücre/hedef penceresi ayrı geri okundu.
Kanıt: `outputs/reports/events/review_v1/20261010T001137Z_320433ed/`.
Sınır: matematiksel küme tutarlılığı; gerçek yangın kimliği, nihai etiket,
çevrimiçi olay kimliği veya 2023–2024 olay sınırı doğrulaması değil.

E20 — 10 Ekim: [V2 snapshot geri okuması](../GCP_V2_FAILURE_2026-10-10.md)
8.794 bayt dosyanın kimliğini, ilk hata kaydını, kalan dosya boyutlarını ve
3.511 ölçümde kaynak rezervlerini kontrol etti. Kanıt:
`outputs/gcp_acceleration/continuation_failure_v2_2026-10-10/snapshot_readback.json`;
kaynak SHA-256 `43c6a64e6547c2856f7ce39fcf478e12be3df40c8032d80cdfa3daf8e4062e0b`.
Sınır: uzak durumun yerel geri okuması; ayların yeni bilimsel kabulü, tüm
anlarda kaynak yeterliliği veya ValueError kök nedeni kanıtı değildir.

E21 — 10 Ekim: [Gerçek scan zamanı replay'i](../GCP_SCAN_TIME_FIX_2026-10-10.md)
`SNPP:2022252.2230` kaynağında özgün fonksiyonun 184. satır ValueError'ını
yeniden üretti. Üç UTC sütununun açık ISO çözümlemesi, ham TAI93 dönüşümüyle
nanosaniyesine kadar eşleşti; girdiler değişmedi. Kanıt:
`outputs/gcp_acceleration/continuation_failure_v2_2026-10-10/scan_replay_readback.json`;
kaynak SHA-256 `528f74b8091232a8e54ed598b20d5acedec89e1ee07401eacbacb3b3c65476a5`.
Sınır: tek kaynaktaki hata noktası; adapter ile gerçek tam hücre sayımının
başarısı, bütün ay kabulü veya diğer hataların çözümü değildir.

E22 — 10 Ekim: [Gerçek adapter kabulü](../GCP_SOURCE_AWARE_V3_2026-10-10.md)
aynı `SNPP:2022252.2230` girdilerinde 203 scan/1.889 scan–grid satırını,
native hücre sayımlarını ve üç UTC sütununda nanosaniye eşitliğini doğruladı.
Kanıt: `outputs/gcp_acceleration/continuation_failure_v2_2026-10-10/scan_iso_adapter_readback.json`;
kaynak SHA-256 `edfba0a8a87cdbf642e9cfd31a9d7d3115ac3281003b844135e1b127369621ea`.
Sınır: tek kaynak düzeltme kabulü; yeni uzun oturum veya bütün dönem kabulü
değil. V3'nin gerçek eski checkpoint CLI denemesi yerel/ağ kapalı kontrolüdür.

E23 — 10 Ekim: [V3 oturum günlük/katalog geri okuması](../GCP_SOURCE_AWARE_V3_2026-10-10.md)
üç eşit final, 21 tam ay log birlikteliği, 2.032 tekil yeni çift ve 235 günlük
commit'in nominal kayıt/sayaç eşitliğini kontrol etti. Kanıt:
`outputs/gcp_acceleration/source_aware_v3_2026-10-10/session_log_readback_accepted.json`;
arşiv SHA-256 `19b177afebe1724770307f9e911e103b538ee7a347a283cd294f000cdb5482c7`.
Sınır: günlük/katalog tutarlılığı; yeni ürün ZIP/Drive geri okuması veya
tam dönem/model kabulü değil. Kaynak ölçümleri bütün anları kapsamaz.

E24 — 10 Ekim: [Bitki örtüsü gerçek ISO kabulü ve V2 devam](../VEGETATION_ISO_RESUME_2026-10-10.md)
92 ham grubun 868 zamanını scalar ile eşleştirdi; 20 varsayılan parser
hatası ve adapter altında 5.798 satır özgün geri okuması kanıtlandı.
Kanıt: `outputs/reports/landscape/iso_adapter_v1/proof_2019_03_22.json`;
SHA-256 `0e62593189533ad6223035e1260cd40306c23d860d667fd228adc8e57970b397`.
Eski Ağustos'un 179.738 satırı ağ kapalı yeni entrypoint'te geçti;
136 dosya baseline'ı ve yeni işin canlı üst/çocuk süreçleri kontrol edildi.
Sınır: matematiksel/zaman geri okuması ve başlangıç; 72 ay bitişi,
bağımsız saha doğrulaması, operasyonel erişim veya model kabulü değildir.

E25 — 10 Ekim: [Özellik birleştirme denemesi](../FEATURE_JOIN_PILOT_2026-10-10.md),
1 Ağustos 2018'in 2.899 hücresinde 27 adayı, ayrı kalite tablosunu ve
kaynak NaN konumlarını CSV'den geri okudu. 24 girdi dosyasının hash'i
değişmedi; kabul sırasında ağ bağlantıları engellendi. Kanıt:
`outputs/reports/dataset/feature_join_v1/20261010T120407Z_d4282cbe/readback.json`;
SHA-256 `b1b3f95757e3ce657042a80e086e309e8efa58acced87ef993571dfbd90b71f0`.
Sınır: tek eğitim günü özellik birleştirmesi; kaynakların mevcut kabul
kayıtları kullanıldı, ham çıkarım yeniden yapılmadı. Etiket, habitat,
tam veri seti, operasyonel erişim veya model başarısı kabulü değildir.

E26 — 10 Ekim: [Gün geçişleri ve hedef kabul hazırlığı](../TARGET_ADMISSION_REVIEW_2026-10-10.md)
dört eğitim gününde özellik geri okumasını ve dokuz keşif kataloğunda
sağdan kapalı 24 saat penceresi/boş hedef kontrolünü tamamladı. Kanıt:
`outputs/reports/dataset/target_admission_v1/20261010T121239Z_ce73888e/readback.json`;
SHA-256 `3e597acd1c8349c2fc486eefe785d469b6e93b75e98e0a72fb085a670a989e01`.
15 katalog/kod girdisi değişmedi. 0/1 ataması yok; senaryo seçilmedi.
Sınır: mevcut kataloglardan zaman/kabul hazırlığı; kaynak çıkarımı veya
nihai olay/negatif etiket doğrulaması değil. Gerçek split olay kimliği
denetimi nihai olay tablosunu bekler; mevcut davranış sentetikte sınandı.

E27 — 10 Ekim: [Destek ve zor vaka paketi](../DECISION_REVIEW_2026-10-10.md)
2.899 hücrenin habitat–meteoroloji destek kesişimini, 15 eşik sayımını
ve 33 habitat/53 olay-senaryo örneğinin kaynak bağlantısını geri okudu.
Kanıt: `outputs/reports/dataset/decision_review_v1/20261010T124447Z_f3e2eef2/readback.json`;
SHA-256 `ad0567e829719d4b2b45cb7b696ce4442c8fc083268a670c4696b1bd642aa5a9`.
Hücre × gün toplamları eski meteoroloji raporuyla eşleşti; seçili olay
üyelik/ilk-son zaman/hücreleri özgün atamalarla eşleşti. Sınır: amaçlı
vaka ve matematiksel geri okuma; bağımsız yangın veya habitat doğrusu
değil. Uzman formu boş, eşik/senaryo/etiket seçimi yok.

E28 — 10 Ekim: [Parçalı özellik kaydı](../FEATURE_PARTITION_PILOT_2026-10-10.md)
dört eğitim gününün 11.596 hücre-gününü günlük feature/kalite dosyalarından
tam eşitlikle geri okudu. Kanıt:
`outputs/reports/dataset/feature_partition_v1/20261010T135514Z_3672d40a/readback.json`;
SHA-256 `16b508109c3531a3c3e92d463f9d4067a4108279d40122d11716cb8e5f96fe07`.
44 girdi aynı; ağ engellenmiş süreç ve 47 ilgili test geçti. Sınır:
depolama/anahtar/değer pilotu; tam ay/dönem üretimi, etiket, model,
bilimsel kaynak kabulü veya bellek/verim kıyası değildir.

E29 — 10 Ekim: [Bitki örtüsü kota kontrolü](../VEGETATION_QUOTA_CHECK_2026-10-10.md),
gerçek süreç yokluğu, 22 ayın korunması, 91/92 son kesim grubu ve
265 değişmeyen dosyanın preflight kaydını içerir. Kanıt:
`outputs/reports/landscape/network_resume_v1/20261010_4675893f/quota_observation.json`;
SHA-256 `87470d6bb3f95ac7f201e0739622721bb9e175f2d3dd6ba3806309f7e8d7c0a9`.
Mevcut kimlikle küçük hizmet isteği geçti; SDK güncel kota aşımı/kısıtlı
mod bildiriyor. Sınır: eski EEException'ın nedeni, kullanılan tier/tüketim
ve eksik grubun tamamlanması kanıtlanmadı. Kuyruk/billing değiştirilmedi.

E30 — 10 Ekim: [Contributor sonrası devam](../VEGETATION_QUOTA_CHECK_2026-10-10.md#contributor-güncellemesi-sonrası-devam)
265 korunmuş dosya ve aynı proof/runtime kimlikleriyle yeni V2 çağrısının
başlangıcını kabul etti. Kimlikle küçük EE isteğinde kota uyarısı gelmedi;
gerçek süreçlerde üst/çocuklar canlı, kayıt `running`. Kanıt:
`outputs/reports/landscape/training_supervisor_v1/training_iso_v2_contributor_resume_20261010_5c811bc3/startup_check.json`;
SHA-256 `e6d8519b51cfde73742bde782d798eb9caccf288cdb987558eb51c3f974b50a5`.
Önceki 24 saat sınırı uzatılmadı. Sınır: başlangıç/kimlik/süre kabulü;
Kasım'ın veya 72 ayın bitişi, kalan kota yeterliliği ve model kabulü değildir.

E31 — 10 Ekim: [İkinci V3 kapanışı](../GCP_SOURCE_AWARE_V3_2026-10-10.md#ikinci-oturumun-kapanışı-ve-gerçek-arşiv-kontrolü)
482.319 bayt yeni günlük arşivini, üç eşit finali, paket kimliklerini
ve son çağrı sayaçlarını ağ kapalı geri okudu. Kanıt:
`outputs/gcp_acceleration/source_aware_v3_2026-10-10/session_20261010T194058Z_log_readback.json`;
SHA-256 `90989039f9a47425709013a14386bfe86588e52aa9216a2b0560abef74db8c6f`.
28 tam ay listesi, 1.863 yeni/18 yeniden kullanım, 206 commit ve 262
gün katalogla tutarlı; normal rezerv/poweroff kaydı geçti. Sınır:
günlük/katalog kabulü; yeni bilimsel ürün/Drive baytları, gözlem/etiket
ve bütün 72 ayın kabulü değil. Temmuz'un commit olmayan beş günü korunur.

## Yeni kanıt ekleme


Tarih, kapsam, kaynak dosya/rapor, doğrulama yöntemi, sonuç ve sınırlama birlikte
yazılır. Büyük dosyanın kendisi Git'e eklenmez. Yerel makine çıktısı için SHA-256
veya ilgili manifest bağlantısı korunur. Ölçümün tekrar üretimi başarısızsa önceki
başarı silinmez; yeni tarihli uyuşmazlık ve çözüm kaydı açılır.

Literatürden alınan sonuçlar bu projenin başarısı olarak yazılmaz. Kurum yazışması,
destek kaydı açılması veya başvuru hazırlığı resmî proje desteği anlamına gelmez.
