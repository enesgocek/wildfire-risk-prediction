# Araştırma kanıt dizini

Son editoryal güncelleme: 12 Ekim 2026. Bu dizin birincil çıktılara yönlendirir;
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

E32 — 10 Ekim: [13 saatlik V4 hazırlığı](../GCP_THIRTEEN_HOUR_CONTINUATION_2026-10-10.md)
yerelde 20 V4 ve 46 eski regresyon kontrolü, lint/format ile geçti. İlk V3 geçişi
üç kabul edilmiş finalin tam bayt hash'ine bağlı; bilimsel/rezerv/worker
kuralları korunur. V3, 19 donmuş paket üyesi ve iki canlı bitki örtüsü kodu
aynı hash'lerle okundu. Kanıt:
`outputs/gcp_acceleration/source_aware_v4_13h_2026-10-10/prepared_readback.json`;
SHA-256 `16a91a44b7bb027de62498945fcb68c9c5303b2c25bb14d9cd99f3cb07fa8e19`.
Sınır: yerel hazırlık ve geçiş kabulü; canlı VM ayarı/başlangıcı, 13 saatlik
performans veya yeni ay/ürün/etiket kabulü değildir.

E33 — 10 Ekim: [V4 uzak başlangıcı](../GCP_THIRTEEN_HOUR_CONTINUATION_2026-10-10.md#ilk-uzak-çalışma-geri-bildirimi)
kullanıcı SSH çıktısında doğru wrapper, `running`, `remaining_months`, canlı
PID ve yeni son zamanla bildirildi. Eski ay yeniden kullanımı görülür;
yeni çift sıfırdır. Yerel özet:
`outputs/gcp_acceleration/source_aware_v4_13h_2026-10-10/startup_20261010T203926Z_user_readback.json`;
SHA-256 `6dbf75a2d52c2c8f7f3cc50019c4712747adb2935e6b4ddc75f10b9376f7960d`.
Sınır: kullanıcı çıktısının kimlik/durum/timezone kontrolü; canlı bağımsız
VM/API sorgusu, yeni ay/ürün/etiket kabulü veya gerçek kapanış değildir.

E34 — 11 Ekim: [VPN molası duruşu](../VEGETATION_VPN_PAUSE_2026-10-11.md)
gerçek Windows süreç/konsol sınırı, kontrollü Ctrl+C, final interrupted durumu
ve süreç/kilit yokluğu ile doğrulandı. 36 doğrulanmış ayın 108 dosyası ve
13 runtime pin'i aynı; Ocak 2021 ham grup sayımı kısmi kapsamdır. Kanıt:
`outputs/reports/landscape/vpn_pause_v1/20261011_ac047933/pause_readback.json`;
SHA-256 `0f8e8826af580687cdd940d9053d164d3dede853684e3eff0a832291593ea864`.
Sınır: kontrollü yerel duruş/hash koruma; kalan bütün ayların kabulü veya
VPN sonrası yeniden başlatma değildir. Otomatik yeniden başlatma yok.

E35 — 11 Ekim: [Kesinti sonrası yerel devam](../VEGETATION_POWER_RESUME_2026-10-11.md)
eski süreç/kilit yokluğu, 121 dosya kimliği, ISO proof, 368 geçerli Ocak ham
grubu, disk rezervi ve küçük EE hizmet isteğiyle başlatıldı. Yeni V2 üst/çocuk
süreçleri gerçek Windows sorgusunda canlı; başlangıç `running`, hata dosyası boş.
Kanıt:
`outputs/reports/landscape/training_supervisor_v1/training_iso_v2_power_resume_20261011_bb85a275/startup_check.json`;
SHA-256 `add9376a683e6cb4d08b56f326bc6fea25252902615bdf3e8a8fb83d92272ebc`.
Sınır: yeniden başlatma/koruma/ham sözleşme kabulü; kalan kota, bütün aylar,
bilimsel etiket veya 48 saatte kesin bitiş kanıtı değildir.

E36 — 11 Ekim: [V4 tanı arşivi ve 18 saatlik V5](../GCP_EIGHTEEN_HOUR_CONTINUATION_2026-10-11.md).
30 üye/üç eşit final, 40 tam ay, 3.020 yeni/45 yeniden kullanılan çift
katalogla tutarlı; 5 ReadTimeout/19 sonraki iptal, örneklenmiş rezerv ihlali yok.
Geri okuma `outputs/gcp_acceleration/source_aware_v4_13h_2026-10-10/failure_readback.json`;
SHA-256 `9d477cd9c388ed2b004ee76b33292ce1de310c9b87e9a37a1bc4d6269f971594`.
V5 hazırlığı `outputs/gcp_acceleration/source_aware_v5_18h_2026-10-11/prepared_readback.json`;
SHA-256 `ec5ef9bdd2c946eb10b7dd0469354305ce0f9a247f9a19f65d39c4546b450c49`.
32 V5/20 V4 ve 73 eski test geçti. Sınır: yerel günlük/katalog ve yazılım
denetimi; ürün ZIP/Drive veya uzak 18 saatlik çalışma kabulü değildir.

E37 — 11 Ekim: [Bakım için bitki örtüsü duruşu](../VEGETATION_MAINTENANCE_PAUSE_2026-10-11.md).
İzole konsola Ctrl+C, final interrupted kayıt, gerçek süreç/kilit yokluğu;
45 ay ve 13 runtime pin'i toplam 148 dosyada aynı hash. Kanıt:
`outputs/reports/landscape/maintenance_pause_v1/20261011T182521Z/pause_readback.json`;
SHA-256 `2c216e13e8c80d717a3c8cb63921803cb7325160c1e1c5a7f7e9a9b4db4e9623`.
Sınır: duruş ve koruma kabulü; Ekim 2021 tam ay kabulü veya yeniden
başlatma değildir. Devam için açık kullanıcı isteği gerekir.

E38 — 11 Ekim: [Bakım sonrası yerel devam](../VEGETATION_MAINTENANCE_RESUME_2026-10-11.md).
148 kabul edilmiş dosya/276 kısmi ham kayıt aynı; ISO proof, disk ve scalar
bağlantı geçti. Yeni üst/çocuklar gerçek Windows sorgusunda canlı, running,
stderr sıfır. Kanıt:
`outputs/reports/landscape/training_supervisor_v1/training_iso_v2_maintenance_resume_20261011_bd22517d/startup_check.json`;
SHA-256 `5ad90201c16a8cdb45b4410e319488f5db5870cad894eada445f376197374594`.
Sınır: koruma ve başlangıç kabulü; ilk geri okunan iki ay yeni ay değildir,
45 eski ay korunur. Kalan kota, tüm dönem veya kesin bitiş kanıtı yok.

E39 — 11 Ekim: [V5 uzak başlangıç bildirimi](../GCP_EIGHTEEN_HOUR_CONTINUATION_2026-10-11.md#ilk-v5-uzak-başlangıç-geri-bildirimi).
Kullanıcı SSH çıktısında doğru V5/running/remaining_months, canlı supervisor,
hata None ve 24 korunmuş tanı. Ay listesi bu çağrıda yeniden kuruluyor;
başlangıç beşi eski 40 ayın kaybı değildir. Kanıt:
`outputs/gcp_acceleration/source_aware_v5_18h_2026-10-11/startup_user_readback_20261011.json`;
SHA-256 `295596772dfcead6b0d71999d71bfc0914c933cdacead345c437934af1a35761`.
Sınır: kullanıcı bildirimi/kod kimliği/zaman dönüşümü; bağımsız canlı API,
Drive veya yeni ürün/ay kabulü değil. Yeni çift sıfırdır.

E40 — 12 Ekim: [V5 erken kapanış ön incelemesi](../GCP_V5_EARLY_STOP_2026-10-12.md).
Kullanıcı Cloud Shell çıktısında TERMINATED, 64800 saniye/18 saat doğru;
1:56:55,696 çalışma, cap'ten 16:02:59,121457 önce kapanış. Kanıt:
`outputs/gcp_acceleration/source_aware_v5_18h_2026-10-11/early_stop_user_readback_20261012.json`;
SHA-256 `3c99fc34c964027d4223fc780483f0f5523d77296636b8fbe8d39c17a80616da`.
Sınır: kullanıcı API çıktısı/zaman dönüşümü; kapanış nedeni veya yeni
ürün kabulü değildir. Günlük alınmadan hata/erken tamamlanma ayrıştırılamaz.

E41 — 12 Ekim: [V5 Drive metadata hatası bildirimi](../GCP_V5_EARLY_STOP_2026-10-12.md#sonraki-ssh-bildirimi--drive-metadata-hatası).
Kullanıcı SSH çıktısında Temmuz 2020/pair_publication, 156 yeni çift,
40 tam ay, FILE_METADATA 404/notFound ve parent hata/poweroff kaydı.
Kanıt `outputs/gcp_acceleration/source_aware_v5_18h_2026-10-11/failure_user_readback_20261012.json`;
SHA-256 `e8985c002ca25abc6bed2df27e97f91534479fed2adbcefccc5f65c153deac19`.
Sınır: uzak kullanıcı bildirimi ve kod/HTTP sınıf yorumu; dosya kimliği,
silinme/erişim/geçici görünürlük nedeni ve yeni ürün baytları doğrulanmadı.

E42 — 12 Ekim: [V5 gerçek arşiv kabulü ve Drive tanısı](../GCP_V5_EARLY_STOP_2026-10-12.md#gerçek-arşiv-kontrolü-ve-salt-okunur-tanı-hazırlığı).
5 normal üye, 3 aynı final; donmuş kod, 40 ay, 17 yeni gün/156 çift ve
2.696 kaynak örneği kontrol edildi. Kanıt:
`outputs/gcp_acceleration/source_aware_v5_18h_2026-10-11/failure_readback.json`;
SHA-256 `b98cad5bff82fed84e1ff17f1ff234da1de074606986211e453f903129158daa`.
25 yeni/36 Drive/51 ilgili manifest-controller testiyle salt okunur tanı hazır.
Sınır: günlük/katalog
kabulü, örneklenmiş kaynak kullanımı; uzak ürün bayt kabulü, canlı Drive
kontrolü veya tarihsel dosya/404 nedeninin tespiti değildir.

E43 — 12 Ekim: [Drive tanısı ve V6 devam hazırlığı](../GCP_DRIVE_RESUME_V6_2026-10-12.md).
Rapor hash'i/katalogla eşleşen 31 hazır ZIP; 30 not_published / bir
payload_without_completion; protected hash'ler aynı, mevcut erişim başarılı.
Kanıt `outputs/gcp_acceleration/source_aware_v5_18h_2026-10-11/drive_probe_readback_20261012.json`;
SHA-256 `e5dcfdf63931c786f1e50ba1720865104caf8a31f9eee6d4194a75b3c4668112`.
V6 hazırlığı `outputs/gcp_acceleration/source_aware_v6_18h_2026-10-12/prepared_readback_v2.json`;
SHA-256 `5ba23563b9cb3eb34a857405224bcb47a7016cbbe9225ad2cab1edd47b1f3daa`.
97 test/25 hash aynı. Sınır: üretici tanısının yerel rapor kabulü; bağımsız
canlı Drive/31 ZIP'in yerel bilimsel kabulü veya tarihsel 404 nedeni değil.

E44 — 12 Ekim: [İlk V6 uzak başlangıç bildirimi](../GCP_DRIVE_RESUME_V6_2026-10-12.md#ilk-uzak-başlangıç-bildirimi--12-ekim).
Kullanıcı günlük bölümünde V5 kanıtları/31 retained pair korunması ve altı
eski ayın geri okunması var. Kanıt
`outputs/gcp_acceleration/source_aware_v6_18h_2026-10-12/startup_user_readback_20261012.json`;
SHA-256 `c4518db6d02740d9e56108b474b32d0b31904eb487f59cb66edbc637713a74c0`.
Sınır: kullanıcı launcher bildirimi; canlı süreç, progress hash/deadline ve
yeni ürün/ay kabulü değil. Görünen hata satırı yok; genel hata yokluğu kanıtı değil.

E45 — 12 Ekim: [V6 süreç/progress bildirimi](../GCP_DRIVE_RESUME_V6_2026-10-12.md#sonraki-süreç-ve-progress-bildirimi--12-ekim).
Kullanıcı SSH çıktısında doğru V6 hash'i, running, PID 1683/53:52,
26 eski ay, sıfır yeni çift ve hata alanları None. Progress son sınırı
12 Ekim 21:13:37 Türkiye. Kanıt
`outputs/gcp_acceleration/source_aware_v6_18h_2026-10-12/progress_user_readback_20261012.json`;
SHA-256 `68c3e0a7c0544210d2f10b9546dc67fa330bc474b702f3faf2e1d1a8ea8267cb`.
Sınır: kullanıcı bildirimi; bağımsız Google API/Drive veya yeni bilimsel
ürün kabulü değildir. Aylık geri okuma yeni ham işleme sayılmaz.

E46 — 12 Ekim: [Tam aylık aday özellik birleştirmesi](../FEATURE_MONTH_READBACK_2026-10-12.md).
Ocak/Ağustos 2018: 62 gün, 179.738 hücre-gün ve 27 aday; ayrı kaynak
değer/eksiklik geri okuması, 165 değişmeyen kaynak/yöntem hash'i ve 66 test.
Kanıt `outputs/reports/dataset/feature_month_v1/two_month_readback_20261012.json`;
SHA-256 `ba00e9b1b612094964a4b767b889b4699a477c72888fbcd4a71abe05fe2c98da`.
Sınır: iki ay aday özellik kabulü; bütün dönem, saha doğrulaması, etiket,
nihai habitat, operasyonel erişilebilirlik veya model başarısı değildir.
Canlı kuyruklar ve bilimsel kapılar değiştirilmedi.

E47 — 12 Ekim: [Veri setine geçiş hazırlığı](../DATASET_PREPARATION_RUNBOOK_2026-10-12.md).
27 aday sözlüğü, 72 aylık kaynak/teslim planı, hash bağlı toplu yeniden
kullanım, boş hedef anahtar eşleştirmesi ve son aday denetimi hazır.
Ocak/Ağustos'ta 179.738 hücre-gün yeniden üretilmeden denetlendi;
107 test ve 165 değişmeyen kaynak/yöntem dosyası. Kanıt
`outputs/reports/dataset/preparation_v1/20261012T020712Z_ae295f2a/workflow_readback.json`;
SHA-256 `8791ce3d379776ff49fa4822f827001d741a6001c2b20e3a00cf269628572f84`.
Sınır: kaynak referansı/aday yapısal kabul; yeni tüm dönem, bilimsel
etiket/habitat/gözlem, operasyonel veya model kabulü değildir. Snapshot'ın
61 bitki örtüsü referansı ve tarihsel 40 uydu günlük/katalog ayı ayrıdır;
2024 kaynak hazırlığı ve bilimsel kapılar açık, 2025 kapalı.

E48 — 12 Ekim: [Bitki örtüsü VPN duruşu](../VEGETATION_VPN_PAUSE_2026-10-12.md).
62 ay (Ocak 2018–Şubat 2023), 199 kabul/runtime dosyası duruş öncesi ve
sonrası aynı hash'lerde. Gerçek Windows süreç ağacı ve iki kilit kapalı;
final interrupted_checkpoints_retained. Ctrl+C sonrasında kapanmayan tek
istek alt süreci kimliği doğrulanarak sonlandırıldı. Mart'ın 169 ham JSON'u
kısmi envanter; tam ay kabulü değil. Kanıt
`outputs/reports/landscape/vpn_pause_v1/20261012T022851Z/pause_readback.json`;
SHA-256 `7e141075c2f619455ab64f3605926b5ba0478e67394142b2b5f017dab7c0c304`.
Yeni bilimsel üretim/etiket kabulü, otomatik devam veya VM işlemi yok.

E49 — 12 Ekim: [VPN sonrası yerel devam](../VEGETATION_VPN_RESUME_2026-10-12.md).
62 ay/199 kaynak ve 169 kısmi Mart JSON'u aynı hash'lerde; ISO proof,
paket/disk/scalar bağlantı kontrolü geçti. Yeni job running, gerçek süreç
ağacı canlı ve stderr boş; ilk üç ay geri okunmuş, Nisan 2018 denetleniyor.
Başlangıç kanıtı
`outputs/reports/landscape/training_supervisor_v1/training_iso_v2_vpn_resume_20261012_6b68627a/startup_check.json`;
SHA-256 `b76b4102f786c7e1596e23afad3ac4938cb96cd1365ad16e2577a7aeccb7ede3`.
13 Ekim son sınırı/rezerv korunur; yeni ay, etiket veya model kabulü değildir.
Bağlantı testi VPN durumunu veya kalan kota bütçesini kanıtlamaz; VM değişmedi.

E50 — 12 Ekim: [Eğitim bitki örtüsü tamamlanması](../VEGETATION_TRAINING_COMPLETE_2026-10-12.md).
72 ay (2018–2023), selected_training_range_verified; son çağrıda 62 eski
ay/10 yeni ay. Gerçek Windows süreçleri ve iki kilit yok; stderr boş.
229 manifest/tablo/readback/runtime dosyası final hash'lerle eşleşti;
2.191 gün/2.899 hücre/iki pencere 12.703.418 hücre-gün-pencere satırı.
Kanıt `outputs/reports/landscape/training_completion_v1/20261012T082646Z/completion_readback.json`;
SHA-256 `1d6352218200992dbc05323fcf29ae802da070af4e04fe1a0dda90d9ba9374c5`.
Sınır: aday özellik dosya bütünlüğü ve üretim aylık kabulü; yeni bağımsız
bilimsel hesaplama/saha doğrulaması, etiket, model veya 2024 kabulü değil.

E51 — 12 Ekim: [V6 48 aylık ilerleme bildirimi](../GCP_DRIVE_RESUME_V6_2026-10-12.md#48-aylık-uzak-ilerleme-bildirimi--12-ekim).
Kaynak kullanıcı SSH progress/launcher/ps çıktısı: running/doğru hash,
48 tam-ay sayacı, Kasım 2019/11 Kasım görünen kapanış, 2.115 yeni/beş
yeniden kullanılan çift. Supervisor 8:20:27 ve 18 görünen çocuk süreç;
hata alanları None. Kanıt
`outputs/gcp_acceleration/source_aware_v6_18h_2026-10-12/progress_user_readback_20261012T083704Z.json`;
SHA-256 `c9e0c28b60a022506e92f212e2313a325996830ba18121b34a423f87e8c65c73`.
Uzak gözlem saati/tam ay listesi yok; bağımsız VM/Drive ve yerel ürün bayt
kabulü değil. Aralık 31 ertelemesi, bilinmeyen gözlem/negatif etiket engeli korunur.

E52 — 12 Ekim: [V6 50 aylık ilerleme bildirimi](../GCP_DRIVE_RESUME_V6_2026-10-12.md#50-aylık-uzak-ilerleme-bildirimi--12-ekim).
Kullanıcı SSH çıktısında running/doğru hash/None hata; tam-ay sayacı 50,
Eylül 2019/18 Eylül son görünen kapanış. Önceki bildirime göre iki ay ve
612 çift artışı, 2:00:32 supervisor elapsed farkı. İşlenmiş çift toplamı
2.727, yeniden kullanım beş. Kanıt
`outputs/gcp_acceleration/source_aware_v6_18h_2026-10-12/progress_user_readback_20261012T103705Z.json`;
SHA-256 `16119b6e7067fec0b3190ced7a97894c62eb239ae84639383f8ae41cb81376b6`.
Üretici gözlem saati/tam ay listesi yok; bağımsız VM/Drive veya yerel ürün
bayt kabulü değil. Havuz sınırı ve bütün dönem ETA'sı bu snapshot'tan çıkarılmaz.

E53 — 12 Ekim: [Literatür incelemesi](LITERATURE_REVIEW_2026-10-12.md),
[kaynak sicili](literature_sources_2026-10-12.json) ve
[önerilen deney protokolü](ARTICLE_RESEARCH_PROTOCOL_2026-10-12.md).
34 seçilmiş birincil kayıt; yayın statüsü, erişim düzeyi ve çalışma aileleri
ayrı. FireAId/ertesi gün Yunanistan/Mesogeos/ECMWF ve Türkiye yerel kaynakları
genel yaklaşımın mevcut olduğunu destekliyor. Olası katkı olay/gözlem
politikalarının kapsam ve uyarı yüküne etkisi; uygulanmış sonuç değil.
Sınır: web indeksli yapılandırılmış kapsam incelemesi; Scopus/WoS/TR Dizin
sonuç evreni ve bütün tam metin/ekler yok. Kaynaklar proje başarısı sayılmadı;
özgünlük yokluğu/varlığına dair eksiksiz ispat, danışman onayı veya yayın
kabulü verilmedi. Yerel belge/sicil bağlantıları ve kaynak URL'leri kanıttır;
236 izlenen kod/config/test dosyasının değişmediği ayrı bütünlük kontrolündedir.
Kontrol kaydı `outputs/reports/literature/2026-10-12/review_validation.json`;
SHA-256 `c8ef97af931774f4dec6b5b2b00193a8fb1509a601277945fef1c60772b10edd`.

E54 — 12 Ekim: [Kaynak kimliği denetimi](LITERATURE_IDENTITY_AUDIT_2026-10-12.md)
ve [makine okunur kayıt](literature_identity_audit_2026-10-12.json).
34 gerçek kayıt/yazar atfı, 23 Crossref dergi/konferans kaydı ve yedi ek
DataCite kaydı; toplam 30 sicil eşleşmesi. Dört kayıtta resmî kurum/ürün/
konferans kanalı. Hayalî başlık/yazar/başka makaleye ait DOI saptanmadı.
R18/R32 yayın durumu düzeltildi, üç DOI tamamlandı; R30 çalıştay kabulünün
yazar bildirimi olduğu kaydedildi. Ham açık metadata kayıtları
`outputs/reports/literature/2026-10-12/` altındadır.
Sınır: DOI/yayın ve yazar atfının varlığı; deneylerin bağımsız tekrarı,
bütün başarı iddiaları veya nihai özgünlük değerlendirmesi değildir.
Denetim JSON SHA-256:
`69765117f897795763d609e5319a50b5fe509f0981f6cc4cef2d79126bfb843b`.
Yerel yapı/bağlantı ve 236 değişmeyen kod/config/test kontrolü:
`outputs/reports/literature/2026-10-12/identity_audit_validation.json`.

E55 — 12 Ekim: [V6 VM duruş bildirimi](../GCP_DRIVE_RESUME_V6_2026-10-12.md#vm-duruş-bildirimi--12-ekim-kapanış-günlükleri-bekleniyor).
Kullanıcı gcloud describe çıktısı TERMINATED/64.800 saniye/STOP/
automaticRestart=false. Verilen damgalardan 17:40:11,654 oturum süresi
ve Google üst sınırından 19:42,677464 önce duruş hesaplandı. Süre rezervi
ile uyum; kesin neden, kuyruk tamamlanması veya yeni ay kabulü değil.
Kanıt `outputs/gcp_acceleration/source_aware_v6_18h_2026-10-12/vm_stop_user_readback_20261012T181417Z.json`;
SHA-256 `5ab9627ef285da6a890cef5639bb3b38d17930e2285ea07113669c9f9187f910`.
Kapanış günlükleri bekleniyor; bağımsız agent VM/Drive sorgusu yok.

E56 — 12 Ekim: [V6 kontrollü kapanış: 58 ay](../GCP_DRIVE_RESUME_V6_2026-10-12.md#kontrollü-oturum-kapanışı-58-ay--12-ekim).
Kullanıcı SSH seçilmiş progress/launcher çıktısı: doğru V6 hash'i,
paused_at_runtime_reserve, Guest poweroff requested=True; hata/failed alanları
None. 2019-02–2023-11 tam-ay listesi 58/72 (%80,6), 4.829 işlenmiş/beş
yeniden kullanılan çift; Ocak 2019 kısmi, 31 Aralık 2023 ertelenmiş.
Ay listesi/sayısı ve yerel V6 hash'i kontrol edildi. Kanıt
`outputs/gcp_acceleration/source_aware_v6_18h_2026-10-12/final_user_readback_20261012T182251Z.json`;
SHA-256 `0666075db8ba27974fe5c66632146980d0cac7392997cc2fbea57839d4d53149`.
Sınır: kullanıcı uzak bildirimi; özgün kapanış arşivi ve yeni ürün baytlarının
yerel kabulü bekleniyor. Bağımsız canlı VM/Drive sorgusu veya üretim yok.

E57 — 12 Ekim: [V6 kapanış arşivi yerel denetimi](../GCP_DRIVE_RESUME_V6_2026-10-12.md#kapanış-arşivinin-yerel-denetimi--12-ekim).
1.190.920 baytlık arşiv, beş güvenli üye ve üç eşit final. Donmuş paket/
katalog, 4.829 yeni ve beş reused pair sayacı geçti; 18 yeni + 40 önceki
referansla 58 tam ay. Ocak 1–11 kapalı; 12–15 günlerinde 33 pair pending.
29.146 örnekte RAM/disk rezerv ihlali yok; tek negatif iowait ölçümü açık
kaydedilip CPU özetinden dışlandı, ham CSV korunuyor. Aynı V6 devam kimliği
ve ikinci hash/yanlış durum kontrolleri geçti. Kanıt dizini
`outputs/gcp_acceleration/source_aware_v6_18h_2026-10-12/`;
`session_log_readback_20261012.json` SHA-256
`a47aec42c6df357c6284625ddeb09de2909ae82b6d5489ef049182d586b5ba2a`.
Arşiv SHA-256 `bdca0bccabdc580cf7f0010983985d85066ed97a042370d5d3956b9c5d6ab509`.
Sınır: günlük/katalog kabulü; bilimsel ürün baytları ve canlı Drive yok.
Kullanıcı indirme sonrası VM Stop teyidi verdi; üretim/VM ayarı değişmedi.

E58 — 12 Ekim: [V6 yeni oturum scheduling bildirimi](../GCP_DRIVE_RESUME_V6_2026-10-12.md#sonraki-18-saatlik-oturum-için-scheduling-bildirimi--12-ekim).
Kullanıcı gcloud çıktısı RUNNING/64.800 saniye/STOP/automaticRestart=false;
yeni üst sınır 13 Ekim 12:36:04,698919 UTC. Aynı V6 komutu hazırlanmıştır,
üretim başlangıcı doğrulanmış değildir. Bağımsız VM sorgusu yok.
Kanıt `outputs/gcp_acceleration/source_aware_v6_18h_2026-10-12/next_session_scheduling_user_readback_20261012T183734Z.json`;
SHA-256 `fccb8adaea815a93fe16569a1bdd328ec81f6448d121c563eab172cf7ecfcc9a`.

E59 — 12 Ekim: [V6 yeni oturum başlangıcı](../GCP_DRIVE_RESUME_V6_2026-10-12.md#yeni-oturum-başlangıç-bildirimi--12-ekim).
Kullanıcı SSH running/december_safe_days, 13 Ekim 12:36:04,698919 UTC
deadline, dört geri okunan ay/sıfır yeni çift ve None hata alanları.
Eski poweroff satırının ardından yeni phase var; önceki 58 ay kabulü
korunur. Süreç/hash bildirimi, bağımsız canlı sorgu ve yeni ürün kabulü yok.
Kanıt `outputs/gcp_acceleration/source_aware_v6_18h_2026-10-12/next_session_startup_user_readback_20261012T184921Z.json`;
SHA-256 `53ec23a2ed04ada3e5b6ede9f01bef59d81b0bb563dee1198549b00b292d967c`.

E60 — 13 Ekim: [V6 uzak ilerleme: 59 ay](../GCP_DRIVE_RESUME_V6_2026-10-12.md#59-aylık-uzak-ilerleme-bildirimi--13-ekim).
Kullanıcı SSH running/remaining_months, 59/72 ay, 302 yeni çift,
Aralık 2018 son kapanış 17 Aralık; None hata alanları. Ay isim listesi,
süreç/hash ve yeni ürün bayt kabulü yok. Ocak kapanışı iş sırası çıkarımı.
Kanıt `outputs/gcp_acceleration/source_aware_v6_18h_2026-10-12/next_session_progress_59_user_readback_20261012T214509Z.json`;
SHA-256 `371077849e58bb1704b2346d29cdbfcfd22cb24676f8ec9197521c0dda4da4b2`.

## Yeni kanıt ekleme koşulları

Tarih, kapsam, kaynak dosya/rapor, doğrulama yöntemi, sonuç ve sınırlama birlikte
yazılır. Büyük dosyanın kendisi Git'e eklenmez. Yerel makine çıktısı için SHA-256
veya ilgili manifest bağlantısı korunur. Ölçümün tekrar üretimi başarısızsa önceki
başarı silinmez; yeni tarihli uyuşmazlık ve çözüm kaydı açılır.

Literatürden alınan sonuçlar bu projenin başarısı olarak yazılmaz. Kurum yazışması,
destek kaydı açılması veya başvuru hazırlığı resmî proje desteği anlamına gelmez.
