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

## Yeni kanıt ekleme

Tarih, kapsam, kaynak dosya/rapor, doğrulama yöntemi, sonuç ve sınırlama birlikte
yazılır. Büyük dosyanın kendisi Git'e eklenmez. Yerel makine çıktısı için SHA-256
veya ilgili manifest bağlantısı korunur. Ölçümün tekrar üretimi başarısızsa önceki
başarı silinmez; yeni tarihli uyuşmazlık ve çözüm kaydı açılır.

Literatürden alınan sonuçlar bu projenin başarısı olarak yazılmaz. Kurum yazışması,
destek kaydı açılması veya başvuru hazırlığı resmî proje desteği anlamına gelmez.
