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

E61 — 13 Ekim: [V6 uzak ilerleme: 61 ay](../GCP_DRIVE_RESUME_V6_2026-10-12.md#61-aylık-uzak-ilerleme-bildirimi--13-ekim).
Kullanıcı SSH running/remaining_months, 61/72 ay, 715 çift; Ekim 2018
son kapanış 1 Ekim ve None hata alanları. Önceki snapshot'a göre iki
ay/413 çift artışı; gözlem saatleri yok, hız/ETA çıkarılmadı. Ay isim
listesi, süreç/hash ve yeni yerel ürün bayt kabulü yok.
Kanıt `outputs/gcp_acceleration/source_aware_v6_18h_2026-10-12/next_session_progress_61_user_readback_20261012T231032Z.json`;
SHA-256 `aca4da4d729f5d33fef14805724f78cb880623b9f5ede475a80bc09682292a24`.

E62 — 13 Ekim: [V6 yeni oturum VM duruşu](../GCP_DRIVE_RESUME_V6_2026-10-12.md#yeni-oturumun-vm-duruş-bildirimi--13-ekim).
Kullanıcı gcloud TERMINATED/18 saat/STOP/automaticRestart=false.
Türkiye damgaları 12 Ekim 21:36:10,056–13 Ekim 06:00:30,264;
8:24:20,208 çalışma, Google sınırından 9:35:34,434919 erken duruş.
Kapanış nedeni/tam-ay sonucu henüz yok; bağımsız canlı sorgu yapılmadı.
Kanıt `outputs/gcp_acceleration/source_aware_v6_session_2026-10-13/vm_stop_user_readback_20261013T094943Z.json`;
SHA-256 `abf76179d989ebeb6390444defeae627d8f3af1c8607c865c6355ca391fa3a37`.

E63 — 13 Ekim: [V6 Haziran 2018 hata denetimi](../GCP_V6_FAILURE_2026-10-13.md).
541.148 baytlık arşiv/beş normal üye/üç eşit failed final. 65 ay, yedi yeni
ay; 1.841 yeni/33 reused çift ve günlük/katalog sayımları eşleşti. Altı
13 Haziran NOAA-20 kaynağı actual geolocation guard hatası; hata sonrası
poweroff. 13.253 örnekte rezerv ihlali yok. Exact final bağlı public ad/stat
tanısı hazır; sekiz davranış testi/lint geçti, gerçek VM'de çalışmadı.
Arşiv SHA-256 `1bae31a2aada315c1e6e0297d935d8594790f88fa4283dca22d60abf5d975444`;
`outputs/gcp_acceleration/source_aware_v6_session_2026-10-13/failure_session_readback_20261013.json`
SHA-256 `ba030461e6bcdfbb6efb915f24c42da35b2fee88695499f5f7896c9b58e9af54`.
Sınır: günlük/katalog kabulü; gerçek deklarasyon adları henüz yok, yeni
bilimsel ürün veya canlı Drive kabulü değil. VM Stop kullanıcı teyidi var.

E64 — 13 Ekim: [V6 geolocation snapshot ve CMR kontrolü](../GCP_V6_FAILURE_2026-10-13.md#kaynak-tanısının-yerel-geri-okuması).
7.891 baytlık exact public snapshot, 14 korunan hash ve altı kaynak kimliği
geçti. Bildirilen 2021/selected 2024 üretim damgası farklı; boyutlar planla
aynı. CMR exact eski adlar 0/yeni adlar 1 hit; eski metadata revizyonları
404, yeni revision 4 URL'lerinde selected adlar doğrulandı. Anonim HEAD
303 sonucu varlık ayırmaz. Yeni iptal/payload hash tanısı hazır, birleşik
14 test/lint geçti; gerçek VM'de çalışmadı. Giriş/GCP/source indirmesi yok.
`outputs/gcp_acceleration/source_aware_v6_session_2026-10-13/geolocation_snapshot_readback_20261013.json`
SHA-256 `60fb6c66f587611054d8b20184f5c444936fda00520701f642cef5756cbe6c35`;
source snapshot SHA-256 `506ec0451d26436c562ab31a5ab74c9fea4a100c860fc4a45fcd59d103b821bc`.
Sınır: bütün NASA arşivlerinden yokluk veya raw eşdeğerlik kanıtı değildir.
Yeni kaynak ertelemesi/üretim veya bilimsel ürün kabulü uygulanmadı.

E65 — 13 Ekim: [İkinci V6 tanısı ve V7 hazırlığı](../GCP_SOURCE_RESUME_V7_2026-10-13.md).
15.843 baytlık public tanı exact final/ilk tanı/plan ve katalogla eşleşti;
18 çocuk, tek parent, 22 hazır ZIP / 65.888.711 bayt. Tanı SHA-256
`a98692817bb6a9f6288a645c6123d5d2d5fe4432f38e366b061515094be26de3`.
Ayrı V7 iki eksik günü dışlar, 27 kanıt dosyasını korur, 22 ZIP hash'ini
kontrol eder; native bilimsel kontroller ve 18 saat/Stop düzeni aynı.
156 birleşik test ve lint/format geçti; 22 donmuş paket/kod hash'i aynı.
Hazırlık kaydı `outputs/gcp_acceleration/source_aware_v7_18h_2026-10-13/prepared_readback_20261013.json`.
SHA-256 `00df6f85ed95430f52357c522f2d2598986a18b328ff9fb07e17339beecb3e92`.
Sınır: 65 ay günlük/katalog kapsamı; ZIP baytları yerelde/native kabul
edilmedi. Yeni V7 remote yürütmesi, kaynak eşdeğerliği veya tam eğitim
kabulü yok; kullanıcı indirme sonrası VM Stop teyitli.

E66 — 13 Ekim: [V7 başlangıcında OAuth 400 ve kurtarma hazırlığı](../GCP_DRIVE_AUTH_RECOVERY_2026-10-13.md).
Kullanıcı 18 çocuk/22 ZIP arşiv geçişi sonrası OAUTH 400 / parent 400 /
poweroff, eski V6 progress ve boş ps bildiriyor; VM Stop teyitli. Kanıt
`outputs/gcp_acceleration/source_aware_v7_18h_2026-10-13/oauth_failure_user_readback_20261013.json`,
SHA-256 `d401eef335403715ec4c8a5067348c0bc42298e6d817a0f30abdd86466dec4ee`.
Native kod sırası eski progress'i açıklıyor; OAuth alt nedeni bilinmiyor.
Testing 7 gün koşulu resmî kaynaktan; mevcut consent/issue kanıtı değil.
Aynı client/scope/folder erişimiyle renewal ve kilitli private installer
hazır, 61 test/lint/format geçti. 22 donmuş dosya ve V7 değişmedi.
Sınır: ilk yerel izin akışı başarısız; yeni yetki/VM kurulum/üretim kabulü
henüz yok. Google insan izni beklenir; 65 aylık önceki kapsam korunur.
Kurtarma hazırlığı `connection_recovery_prepared_20261013.json`, SHA-256
`b74c69193b2d28b0284436a456d3c6a5b18fc0b66203cce9099784c9d1d90d94`.

E67 — 13 Ekim: [Yerel yenilenmiş Drive bağlantısının canlı kontrolü](../GCP_DRIVE_AUTH_RECOVERY_2026-10-13.md#terminal-kapanması-sonrası-yerel-canlı-doğrulama).
Kullanıcı callback mesajı sonrası terminali kapattı; özel dosya mtime'ı
14:17:33 UTC'ye değişmişti. Yerel canlı OAuth refresh ve mevcut folder
metadata kontrolü geçti; drive.file, şema, canAddChildren ve dosyanın
kontrol sırasında değişmediği doğrulandı. Credential değerleri kaydedilmedi.
Kanıt `outputs/gcp_acceleration/source_aware_v7_18h_2026-10-13/local_connection_verified_20261013.json`,
SHA-256 `5beba1638f7b558744a9200d1b3ed380c8ad832f69c4e4c33763a360242f52dd`.
Sınır: eski VM client/folder eşitliği ve kurulum henüz kontrol edilmedi;
Drive nesnesi yazılmadı, VM/üretim başlatılmadı, yeni bilimsel kabul yok.

E68 — 13 Ekim: [VM özel bağlantı kurulumu SSH geri okuması](../GCP_DRIVE_AUTH_RECOVERY_2026-10-13.md#vm-kurulum-çıktısının-geri-okuması).
Kullanıcı installer SHA-256 OK ve üç PASS bildirdi: aynı client/scope/folder,
yenilenmiş token/folder erişimi, özel config kurulumu. İlk bulunamayan
dosya denemesi hash kapısında durmuştu. Yerel V7/registry/installer aynı
hash'te. Kanıt `outputs/gcp_acceleration/source_aware_v7_18h_2026-10-13/vm_connection_install_user_readback_20261013.json`,
SHA-256 `0b538635157a12cd1cc2f124a7daa4ede39f0af65a5f29e6d28a1eeae21c29b8`.
Sınır: kullanıcı uzak çıktısı; bağımsız VM sorgusu, yeni üretim veya yeni
bilimsel kabul yok. Güncel Start'ın 18 saat/STOP ve timestamp kontrolü bekleniyor.

E69 — 14 Ekim: [V7 uzak ilerleme kontrolü](../GCP_V7_PROGRESS_2026-10-14.md).
Kaynak kullanıcı VM SSH launcher/progress bildirimi: running/remaining_months,
364 çift, 66 tam ay, doğru V7 hash'i, güncel STOP sınırı ve None hata alanları.
Nisan 5–6 kapanışları görünüyor. Önceki 65 aylık uzak kapsamdan bir ay
artışı; eklenen ay kimliği seçilmiş çıktıda yok. Sınır: bağımsız canlı VM
sorgusu veya yeni yerel bilimsel ürün kabulü yok; gözlem zamanı verilmediği
için hız/bitiş hesabı yapılmadı. İki kaynak ertelemesi ve etiket kapısı korunur.

E70 — 14 Ekim: [V7 işlenebilir kapsam uzak finali](../GCP_V7_PROGRESS_2026-10-14.md#uzak-final-bildirimi-işlenebilir-kapsam-tamamlandı).
Kullanıcı final çıktısı beklenen status, 70 tam ay, 29/29 Haziran ve 30/30
Aralık günü, 862 çift, None hata alanları, eşit üç final kaydı ve poweroff
gösteriyor. Cloud Shell duruşu 14 Ekim 01:18 UTC; yaklaşık 5:43 çalışma,
18 saat sınırı öncesi. Kaynak `outputs/gcp_acceleration/source_aware_v7_session_2026-10-14/remote_final_user_readback_20261014.json`,
SHA-256 `a18bdb8a55870ea53e7d745da44e0ff15f3cf5f54dd0c573df9207db8405eea6`.
Sınır: kullanıcı uzak çıktısı, arşiv/tam ay kimlikleri ve bilimsel payload
baytları henüz yerelde kabul edilmedi. Asıl hedef 72 ay; iki kaynak günü
ertelenmiş, full_training_complete false. Public final alım adımı hazır.

E71 — 14 Ekim: [V7 final arşivinin yerel log/katalog kabulü](../GCP_V7_PROGRESS_2026-10-14.md#yerel-final-arşivi-ve-katalog-geri-okuması).
Arşiv 318.086 bayt, SHA-256 `61fc0aa9c59c3bb2ca37a01f0f2849907c364775d057aa04cd9dd694716bcb5c`.
Eşit üç final, 70 ay/210 çağrı günü (59 uygun kısmi gün dahil), 862 çift,
6 çıkarımsal yeniden kullanım, beş yeni ay ve 22 değişmeyen girdi geçti.
Kaynak örneklerinde rezerv ihlali yok; 36 test ve lint/format geçti.
Ağ engelli gerçek audit kaydı `outputs/gcp_acceleration/source_aware_v7_session_2026-10-14/accepted_final_readback_20261014.json`,
SHA-256 `5e7adb9eab5ba2483717751573271916ef0dff83ec5e2eac213eede2f58a6df0`.
VM Stop kullanıcı teyitli. Sınır: log/katalog kapanışı; bilimsel ürün/
checkpoint baytları ve canlı Drive geri okuması yok. İki kaynak günü açık.

E72 — 14 Ekim: [Drive kompakt teslimi, native pilot ve devam eden denetim](../GCP_PRODUCT_DELIVERY_2026-10-14.md).
199/199 görev, 1.278.737.639 bayt, completion/SHA kontrolü geçti;
teslim raporu SHA-256 `74827f6b182bc4acac4ab42651e7417daa9f1cbf974fd0c87aa52ab3e2eb9057`.
Ocak 2018 31 gün/139 çift native pilot raporu SHA-256
`56a95a8dcbbfba70aeb82600bcdae5155998b7ab2d33b9101cd12acc5d13ddb3`.
53 test/lint/format geçti. 2.158 günlük tam yerel kontrol dört süreçle
başladı; henüz bitmedi. Sınır: ayrı Temmuz referansı yeniden kabul
edilmedi; tüm geometri günlükleri teslim edilmedi/birleşim yeniden
hesaplanmadı, nihai negatif etiket kapısı kapalı.
Sekiz eski geolocation exact sorgusu sıfır hit; sekiz fire alternatif
sorgusu mevcut sürümü döndürdü. Metadata araştırması eşdeğerlik kanıtı
değildir; ilgili SHA'lar teslim raporunda, iki eksik gün korunuyor.

E73 — 14 Ekim: [Tam native kabul ve eğitim adayı birleştirme başlangıcı](../DATASET_TRAINING_JOIN_2026-10-14.md).
Native final `outputs/gcp_delivery/2026-10-14/compact/audit/20261014T120616395916Z/accepted_readback.json`:
71 ay/2.158 gün/18.423 kaynak çifti, dört süreçte 3.581,05 saniye;
stderr boş ve audit kilidi yok. Temmuz 2023 ayrı önceki referans olarak
kalır. Native final SHA-256
`52be7c3e8fb02798a1e21538607a4612a0c479c105b90157b195385eea4d6781`.
199 payload/22 donmuş girdi kapanış kontrolünün kaydı
`outputs/gcp_delivery/2026-10-14/native_final_handoff_20261014.json`,
SHA-256 `ff03cedb8b8483998b1453ae2c9597f1bf2268a24ad93516f24d93e8e6bad9df`.
Yeni plan SHA-256 `2167f5c015197e17df70a7e166a97572f0fd3d946a50cd01bf6c0908589573b6`:
72 kaynak/iki eski aday, 27 özellik ve 6.351.709 aday hücre-gün hedefi.
41 hazırlık/CLI testi geçti. 16:32'de iki saat sınırıyla yerel yürütme
başladı; 16:34'te üç ay geçti. Bu başlangıç snapshot'ıdır; tam aday veri
seti veya hedef/model kabulü değildir. İki kaynak günü, raw/geometri
sınırı, 2024 hazırlığı ve kapalı 2025 korunur.

E74 — 14 Ekim: [Tam eğitim aday takvimi ve kalite profili](../DATASET_QUALITY_REVIEW_2026-10-14.md).
72 ay/2.191 gün/6.351.709 hücre-gün/27 aday özellik; 70 yeni/iki
yeniden kullanılan ay. Batch indeksi SHA-256
`1964c76f773f2a0c48ae1128d47f43d8772a5c2829e9fcedd55b3ef095876647`;
ayrı tam takvim audit'i SHA-256
`c39536f74cf1b44dec1eec08b94941b495132e759d6ed0005a88110c1f46dbe8`.
17:24/17:32 Türkiye kapanışları, hata/stderr yok ve yazıcı kilidi yok.
İlk kalite profili SHA-256
`1530a4b0e7d74e4a0fa42d16cfee85e728dcada90fc8e37a3c2443df436255c9`;
hash bağlı aylık rapor sayımlarına dayanır, yeni CSV kabulü değildir.
Son sürüm profili SHA-256
`ecd617369a1a24237059361b53c95edb8fe58a49d8bb95ea61e8f20a8c649911`;
aynı sayımlar, 83 pin ve değişmeyen 22 bulut girdisi kapanış kaydı
SHA-256 `fbaa3e19d92e4143387be93597a3ac7f08e75178390f62a08874309a9cdb49e7`.
58 güncel test/lint/format geçti.
Meteoroloji/30g/60g sütunu başına %6,52/%6,92/%1,87 eksik. İki kaynak
günü için dört hedef tarihi yalnız inceleme kapsamıdır; ikili etiket,
imputasyon veya otomatik dışlama üretilmedi. Bilimsel altı kapı ve
2024 hazırlığı açık, 2025 kapalı; model_ready false.

E75 — 14 Ekim: [72 aylık ayrı gözlem denetim tabloları](../OBSERVATION_TABLES_2026-10-14.md).
6.351.709 satır, 6.345.911 ürünlü/5.798 eksik kaynak hücre-günü.
Her aylık CSV.gz dosyadan geri okundu; 477.448.199 bayt/72 tablo.
Tam final `outputs/reports/dataset/observation_materialization_v1/20261014T145638Z_c0881064/accepted_readback.json`,
SHA-256 `fb5fa5ce8c83be2c4e21b130bb06935a5e2d8014e45460c1f61660b73262cb14`.
Aynı dizinde `completion_readback.json` kapanış kaydı SHA-256
`4f3575224119340ca75b851a01d6527ec4359d229a3ec43f75478dd81fd5d506`:
72 tablo hash'i, 11 kaynak/yöntem kimliği ve 22 değişmeyen donmuş girdi;
iki eksik günün 5.798 satırı ayrı okunup boş ölçülerle doğrulandı.
52 ilgili test/lint/format geçti. 158,67 saniye yalnız yerel aktarım;
ham/geometri hesabı, bağımsız saha kabulü veya model başarısı değil.
unknown/negative=false; tanılar model girdisi veya etiket yapılmadı.

E76 — 14 Ekim: [Etiket kanıtı inceleme paketi](../LABEL_EVIDENCE_REVIEW_2026-10-14.md).
6.351.709 eğitim hücre-günü/200 boş olmayan tabakadan 400 sabit tohumlu
pilot; 53 amaçlı olay-senaryo vakası/28 üyelik örüntüsü; 208 ilk hücre/tarih
rolü bağlantısı. Formda 453 inceleme birimi, bütün insan karar/kanıt alanları
boş. Son çalışma 137,19 saniye; altı çıktı CSV'si ilk pilotla bayt olarak
aynı. 51 ilgili test ve lint/format geçti.
Final `outputs/reports/dataset/label_review_v1/20261014T153649Z_ca3fb92e/readback.json`,
SHA-256 `36ce8565a452efbf2a4f1e69fe3254ae33ccdd818eb08584f57b41a9eaf28037`;
aynı dizinde kapanış `completion_readback.json`, SHA-256
`40bc3ac82c37f54f36d4bfcda4353aec550ed5c3e0b827ebcf4731505ab9b781`.
186 kaynak/yöntem kimliği ve 22 donmuş girdi aynı. Kaynak ürünü bulunmayan
18 bağlantı tek bir 2023-12-31 hücre-gününün senaryo/rol tekrarlarıdır;
negatif veya 18 bağımsız vaka yapılmadı. Sektörler il değildir; pilot
tasarım hata oranı hesabı değildir. 0/1 hedef, uzman/bağımsız kabul veya
model üretilmedi; gözlem unknown/negative=false, 2024 açılmadı/2025 kapalı.

E77 — 14 Ekim: [Kurumsal kayıtlarla ilk vaka bağlamı](../REFERENCE_CONTEXT_REVIEW_2026-10-14.md).
Valilik/OGM iki canlı HTML kaynağı, 497.044 bayt; 10 seçilmiş küme adayı,
sekiz üyelik örüntüsü için candidate_regional_context_only bağlantısı.
Kesin olay/hücre kimliği, tutuşma ve 0/1 etiket kabul edilmedi. 55 ilgili
test/lint/format geçti; altı önceki çıktı ve 22 donmuş girdi aynı kaldı.
`outputs/reports/dataset/reference_context_v1/20261014T154819Z_113615fa/readback.json`
SHA-256 `fcca0e13511584f8d45f73887302ba840ee82f4d0d403a6a63b772c78a0de351`;
aynı dizinde `completion_readback.json` SHA-256
`a7732b2b6ed3be67b1eae4c91ea81c6b1ac08232125f43cc6ef3ff60102d194e`.
Kurumsal çoklu başlangıç anlatımı, kümenin tek tutuşma sayılmasına karşı
inceleme gerekçesidir; belirli yanlış birleşme veya dört yönlü bölme
kanıtı değildir. PDF duyurusu içerik kabulü yapılmadan dışarıda, EMSR527
yanlış ülke olarak reddedildi. Önceki 453 form hâlâ not_reviewed;
nihai etiket/model hazır değil, 2024/2025 erişimi ve bulut işi yok.

E78 — 14 Ekim: [Tarihli sınırlarla coğrafi karşılaştırma](../PERIMETER_REFERENCE_REVIEW_2026-10-14.md).
84 filtreli 2021 EFFIS kaydı/433.192 bayt; 42 pilot AOI kesişimi,
21 küme-senaryo varyantı/24 coğrafi bağlantı. MedEU ZIP'i boyut/MD5/SHA
ile doğrulandı; 320 yanmış adım/103 yangın öncesi/226 eksik kayıt ayrıldı,
pilot kesişimi sıfır olduğundan referansa alınmadı. 53 güncel test ve
lint/format geçti. Beş çıktı/35 giriş, önceki altı çıktı ve 22 donmuş girdi
kapanışta kontrol edildi. Final
`outputs/reports/dataset/perimeter_review_v1/20261014T162023Z_61ec4cba/readback.json`,
SHA-256 `32f85afaf1b2a223bae1c7e4003a2f953fa8563d03c97925ca5b0d12b9126810`;
aynı dizinde `completion_readback.json` SHA-256
`4fe1db02eb4df632cc734a578bf6016a1c423f5268b7bdddd746c590ee7a2d19`.
İlk noktanın yaklaşık 174 m sınır dışılığı hata etiketi yapılmadı;
üç varyanttaki ek sınırlar takvim olarak uyuşmadı. Sensör ortaklığı
nedeniyle bağımsız doğruluk/olay kimliği kabulü yok. 453 form hâlâ
not_reviewed; model/0-1 hedef ve holdout/bulut işlemi yok.

E79 — 14 Ekim: [Olay/ilk hücre karar duyarlılığı ve kabul taslağı](../EVENT_DECISION_PROTOCOL_2026-10-14.md).
53 amaçlı senaryo vakası/28 üyelik örüntüsü, ortak tespitlerle 11 inceleme
grubuna ayrıldı; fiziksel olay sayısı değildir. Dört grupta ilk zaman,
üç grupta ilk hücre kümesi, üç grupta aday hedef günü değişti. Hedef günü
değişen dokuz varyant sıralamada öne alındı; diğer 44 vaka korundu.
Altı kabul koşulu makine okunur taslakta unaccepted kaldı. 51 ilgili test
ve lint/format geçti; üç çıktı/40 giriş geri okuması, önceki 11 çıktı
ve 22 donmuş girdi kontrolü geçti. Final
`outputs/reports/dataset/event_decisions_v1/20261014T171606Z_3062f053/readback.json`
SHA-256 `d0210a017a57a3a5d327237e280ecfb4aae9dbc00e892b888759613c9a791a55`;
aynı dizinde `completion_readback.json` SHA-256
`2ea6726f73a9ebe2d156816cbddb1781687155e99fef9d9f562f50c5467f71a7`.
Amaçlı seçkiden hata oranı çıkarılmadı; 453 insan formu not_reviewed.
Senaryo seçimi, 0/1 hedef, model kabulü, 2024/2025 erişimi ve bulut işi yok.

E80 — 14 Ekim: [Öncelikli dokuz vakanın bağlantı/kaynak incelemesi](../PRIORITY_EVENT_TRACE_2026-10-14.md).
Üç gruptaki dokuz varyantın 246 üye satırı/100 farklı tespiti ve dokuz bağlı
iç grafı doğrulandı; 20 yol-düğüm satırı/dokuz ikili karşılaştırma üretildi.
Üç uzun varyant 38,03–51,51 gün; bu yangın süresi kabulü değildir.
98 farklı tespitte önceki yakın Type=2 bağlamı eleme yapılmadan tutuldu.
Altı varyantın takvim çevresindeki kaynak/dönem sonu eksikliği açık kaldı.
57 ilgili test/lint/format geçti; beş çıktı/34 giriş, önceki üç karar
çıktısı ve 22 donmuş girdi kapanışta kontrol edildi. Final
`outputs/reports/dataset/priority_trace_v1/20261014T173742Z_1aef9e5e/readback.json`
SHA-256 `4a09cc30034d94cf6e94b5436543e31e4c48416f262268d8906beace0940be74`;
aynı dizinde `completion_readback.json` SHA-256
`6c2531204a0bcfbc3cb93359e05f681f427ca3cb4ed15dfd25294ce71507c4ba`.
Yönsüz yol yayılma kanıtı, takvim çevresi tam pencere kapsamı değildir.
Olay/etiket/Type kabulü, 2024/2025 erişimi, model eğitimi ve bulut işi yok.

E81 — 14 Ekim: [400 hücre-günde gözlem kanıtı](../OBSERVATION_PILOT_REVIEW_2026-10-14.md).
200 tabakada sabit 400 örnek: 384 ürünlü/16 eksik; 192 termal/192 seçilmiş
termalsiz tanı. 202 alan birleşimi çakışması, 11 nominal kara merkezi
olmayan ürünlü satır ve bir gece yarısı örneği incelendi. Kaynak scan_grid
tarama 202'nin pencereyi aşması doğrulandı; kesin piksel günü atanmadı.
Altı farklı açıklayıcı örnek ve insan görev rehberi hazırlandı; insan
incelemesi yok. 68 ilgili test/lint/format geçti. Yedi çıktı/34 giriş,
önceki altı çıktı ve 22 donmuş girdi kapanışta kontrol edildi. Final
`outputs/reports/dataset/observation_review_v1/20261014T174956Z_cca3d882/readback.json`
SHA-256 `32f75f98feeef857e979fa50340c3b1a01053617f97aa72db6be53bf4a297c44`;
aynı dizinde `completion_readback.json` SHA-256
`5a3ae72ac2f5f7a298ebc6a072d3f641328779b2e73abcbd225deb84530ee865`.
Örneklerin ağırlıksız sayıları popülasyon oranı değildir. Kesim seçimi,
0/1 hedef, model, 2024/2025 erişimi ve bulut işi yok; 453 form boş kaldı.

E82 — 14 Ekim: [Araştırmacının A seçeneği ve su kapsamı](../WATER_SCOPE_2026-10-14.md).
2.899 gridde su dışı ayrık sınıf payları tam sıfır olan 10 hücre ayrı kapsam
tablosunda dışlandı; 727 karışık hücre korunur. Etki: 2.191 eğitim gününde
21.910 kapsam dışı / 6.329.799 korunan hücre-gün, etiketli satır sayısı değil.
30.295 tekil eğitim aday tespitinde dışlanan gridde tespit yok; gerçek yangın
yokluğu kanıtı değildir. 400 pilot satırdan 399'u kapsamı geçer; özgün örnek
ve ağırlıklar korunur. 58 ilgili test/lint/format, beş çıktı ve 22 donmuş
girdi kontrolü geçti. Final
`outputs/reports/dataset/water_scope_v1/20261014T185242Z_f2e469bd/readback.json`
SHA-256 `7b5d296bae6c3744790817409db4bce3a947e92919a06abde9271eac07814cae`;
kapanış SHA-256 `092c966d2a1e85613dddfc139ba47ebaecdf6aa6cd7eb53a528fb738b0d17a97`.
Kapsam tercihi bağımsız doğrulama veya tam habitat kabulü değildir; kaynak
tablolar, boş hedefler, 453 form ve 2024/2025 erişim sınırı aynı kaldı.

E83 — 14 Ekim: [Komşu nominal günlerde hedef pencere incelemesi](../OBSERVATION_WINDOWS_2026-10-14.md).
11 amaçlı pencerede 23 farklı eğitim günü okundu; altı pencerede üç paket
mevcut, beşinde kaynak/dönem sınırı açık. İki pencerenin belirsiz termal
merkezi aynı SNPP granül/tarama kaydıdır; iki yangın veya iki pozitif
sayılmadı. 65 ilgili test/lint/format geçti. Üç çıktı/58 giriş kapanışı,
22 donmuş girdi ve önceki yedi gözlem inceleme çıktısı doğrulandı.
Final `outputs/reports/dataset/observation_windows_v1/20261014T190400Z_25bfc71a/readback.json`
SHA-256 `3be2b93d9fe3e048d6429d94380e49280f4b9e7b04546265ee501e59b7a1b689`;
kapanış SHA-256 `89210f08e243c79eec892baa6b042052ddca1315408ad8488ab877920f40aa2a`.
Tam 400 pilot veya eğitim kabulü değil; piksel zamanı ve alan kırpması açık.
Etiketler/453 insan formu değişmedi, 2024/2025 veri erişimi veya bulut işi yok.

E84 — 14 Ekim: [Sabit pilotta tam pencere denetimi](../WINDOW_PILOT_2026-10-14.md).
400 örnek/200 tabaka ve N/n korunarak 72 aydaki 883 farklı günlük kaynak
okundu. 16 eksik paket kümesi, iki sınır taraması olan örnek, bir sınırdaki
termal merkez ve 191 kesin içeride termal merkezli örnek; bunlar olay/etiket
sayısı değildir. 2020-01-22 örneğinin önceki paketteki kara sınır taraması
ortaya çıkarıldı. Altı önceki amaçlı sonuç birebir tekrar üretildi.
79 ilgili test/lint/format ve beş çıktı/210 giriş kapanışı geçti; 22 donmuş
girdi, kaynak örnek ve 453 form aynı kaldı. Final
`outputs/reports/dataset/window_pilot_v1/20261014T191547Z_b008fcf9/readback.json`
SHA-256 `f79fcb11ede0b7d0c24cf3a976146eae6df871791e9abddf179b4fa96a9e195f`;
kapanış SHA-256 `d5fd9e414ddf8f881df79c5be1e9fdd757af1bdd03f53d3be429d4b9dcfef98f`.
Tam eğitim kabulü veya gözlem yeterliliği kararı değil; 2024/2025 erişimi,
etiket üretimi, model eğitimi ve yeni bulut işi yok.

E85 — 14 Ekim: [Etiket protokolü inceleme seçenekleri](../LABEL_PROTOCOL_REVIEW_2026-10-14.md).
400 örnek/dokuz senaryoda 3.600 aday eşleşme kaydı; 77 aynı üyelik,
11 tümünde eşleşip farklı üyelik ve sekiz kısmi eşleşme. 304 eşleşmesiz
örneğin 96'sı termal merkezli; negatif kabulü yapılmadı. 181 arka plan
örneği inceleme sırasına alındı. Nihai parça son kontrolü ve açık kullanıcı
onayı gereksinimi kaydedildi; gerçek onay veya nihai birleştirme yok.
97 ilgili test/lint/format ve dört çıktı/46 giriş kapanışı geçti;
22 donmuş girdi aynı. Final
`outputs/reports/dataset/label_protocol_v1/20261014T193224Z_54fdbb95/readback.json`
SHA-256 `534d67c44cad55a267aaf57330b4396a9cbb6aa65baa8bfdd71b9037b7bb0cab`;
kapanış SHA-256 `97bb378040b2a7dd74893ddb163803794316fc29f6a28932ad992cee917d7e40`.
Politika seçimi, etiket, model, 2024/2025 veri erişimi ve bulut işi yok.

E86 — 14 Ekim: [19 duyarlı örneğin kaynak ve zincir incelemesi](../SENSITIVE_PILOT_TRACE_2026-10-14.md).
35 pencere/hücre kaynak noktası dokuz senaryoda 181 küme bağlamına izlendi;
138 ilk eşleşme önceki raporla aynı. 43 eşleşmesiz bağlam önceki hedef
gününde başlıyor; 12'sinde ilk hücre de farklı. 5.436 farklı kaynak üyesi,
1.863 yol; en büyük küme 5.304 tespit, en uzun küme 815,37 saat. Bunlar
fiziksel yangın kimliği/süresi veya yayılma kanıtı değildir. 94 ilgili
test, üç dosyada lint/format ve beş çıktı/57 giriş kapanışı geçti;
22 donmuş girdi aynı. Final
`outputs/reports/dataset/sensitive_trace_v1/20261014T194620Z_284f08c1/readback.json`
SHA-256 `f613115b0d67caea55353b102e2c420d1879666dfc8f94ea52416b0e9954fa11`;
kapanış SHA-256 `000ed76785212fc4a2b32cc4bdb806aabddba7c22b7ddee0caab85a3ad40dac1`.
Kaynak Type semantiği, olay ve etiket kabulü açık. Nihai birleştirme,
insan kabulü, 2024/2025 erişimi, model veya bulut işi yok.

E87 — 14 Ekim: [Denetlenmiş eğitim adayı inceleme teslimi](../DATASET_INSPECTION_RELEASE_2026-10-14.md).
72 ay/6.351.709 özellik satırı yeni tam takvim denetiminden geçti;
72 gözlem CSV'si de yeniden okundu, 5.798 eksik ürün satırı korundu.
2.191 günlük feature/provenance dizini, 400 satır/27 özellik önizlemesi,
sözlük ve 181 arka plan adayında kabul edilmemiş kesimler hazırlandı.
119 ilgili test, üç dosyada lint/format, dokuz çıktı/9.772 giriş kapanışı
geçti; 22 donmuş girdi aynı. Güncel özellik denetimi SHA-256
`7e20556fcdf4aa90e32ce98605ebe57f9d81f4c839a0a6cb2a946a1a9df0fa12`.
Final inceleme sonucu
`outputs/reports/dataset/release_readiness_v1/20261014T202658Z_0c89a9de/readback.json`
SHA-256 `f494acb939d84024d5399139ea4e0fc6e45327c45114dfca2e441a6218d612ef`;
kapanış SHA-256 `25f83533cfd8c8c55584484dd8d35840c409c94c71b03ffa18668054d7d5d37b`.
Ana hedef korundu; ayrı katalog hedefi, 0/1 etiketi, insan kabulü veya
nihai birleştirme yapılmadı. Eğitim dışı CSV, model ve bulut işi yok.

## Yeni kanıt ekleme koşulları

Tarih, kapsam, kaynak dosya/rapor, doğrulama yöntemi, sonuç ve sınırlama birlikte
yazılır. Büyük dosyanın kendisi Git'e eklenmez. Yerel makine çıktısı için SHA-256
veya ilgili manifest bağlantısı korunur. Ölçümün tekrar üretimi başarısızsa önceki
başarı silinmez; yeni tarihli uyuşmazlık ve çözüm kaydı açılır.

Literatürden alınan sonuçlar bu projenin başarısı olarak yazılmaz. Kurum yazışması,
destek kaydı açılması veya başvuru hazırlığı resmî proje desteği anlamına gelmez.
