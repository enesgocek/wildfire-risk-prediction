# Bitki örtüsü duruşu ve Earth Engine kota kontrolü — 10 Ekim 2026

## Yerel durum

Bağlantı kesintisi bildirimi üzerine gerçek Windows süreçleri ve disk
kayıtları salt okunur denetlendi. Önceki üst/çocuk Python süreçleri yok;
üst rapor `failed_checkpoints_retained`. Son kayıt 15:06:30 UTC
(18:06:30 Türkiye); aylık çocuk `EEException`, alt kuyruk `RuntimeError`
bildiriyor. Serbest hata ayrıntısı tutulmadığından önceki hatanın kesin
nedeni veya internet kesintisiyle nedensel bağı kanıtlanmış değildir.

Ocak 2018–Ekim 2019 **22 tam ay** kabul listesinde korunmuş. Kasım 2019'un
son kesimi 29 Kasım; ham dosya envanterinde 30 günlük pencerenin 45/46,
60 günlük pencerenin 46/46 grubu var. Son logdaki 27/92 sayacı, toplam
kaydedilmiş parça sayısı değildir: executor hata sonrasında bekleyen
işlerin bitmesini beklemiş olabilir. Dosyadan ölçülen sayı **91/92**'dir.
Eksik dosya `30days_batch_023.json`; Kasım tam ay kabulü henüz yok.

## Koruma ve bağlantı kontrolü

Dondurulmuş proof, adapter ve özgün kaynak kimlikleri denetlendi.
Önceki baseline, kabul edilmiş aylık tablo/manifest/raporlar ve mevcut
91 ham grubun sözleşmeleri kontrol edildi; 265 izlenen dosya değişmedi.
Ham grup denetimi tam aylık integral geri okuması yerine geçmez.
İş kilitleri bulunmuyor; kilit veya veri silinmedi. Disk rezervi ihlali
görülmedi; kontrol anında yaklaşık 122,67 GiB boş alan vardı.

17:00:59 UTC kontrolünde mevcut kimlikle Earth Engine başlangıcı ve küçük
bir scalar hizmet isteği geçti. Görüntü çıkarımı veya yeni toplu iş
başlatılmadı. İstek sırasında SDK, noncommercial compute kotasının
aşıldığını ve `parallelism_restricted=true` durumunu bildirdi. Bu,
güncel kısıtlı modun kanıtıdır; önceki `EEException` için kesin neden
kanıtı değildir. Kullanılan tier ve tüketim sayısı henüz bilinmiyor.

## Kota ve devam sınırı

Google'ın [noncommercial tier belgesine](https://developers.google.com/earth-engine/guides/noncommercial_tiers)
göre aylık kota project düzeyindedir. Kısıtlı mod işi tamamen kapatmaz;
eşzamanlılığı ve hesaplama kaynaklarını azaltır. Community 150,
Contributor 1.000 EECU-saat sağlar; Contributor aktif billing hesabı
gerektirir. Noncommercial Earth Engine kullanımı için ücret alınmaz;
diğer Cloud hizmetlerinin maliyeti ayrıdır. Tier değişiminin yeni limiti
hemen uygulanır, mevcut tüketim korunur.

Bu belge tier/billing değişikliği yapmaz. Contributor uygunluğu ve mevcut
katman [Manage Tier ekranından](https://console.cloud.google.com/earth-engine/configuration/manage-tier)
incelenecek. Ücretli Cloud yükseltmesi veya commercial Earth Engine
geçişi yapılmadı. Yeni kuyruk şu kontrol sonunda **başlatılmadı**.
Sonraki devam, önceki 24 saatlik çağrının 11 Ekim 11:45:01 UTC
sınırı ve yeni onaylanmış çalışma kapsamı dikkate alınarak hazırlanır;
eski kayıtlar yeniden hesaplanmadan geri okunur.

## Kanıt

Klasör: `outputs/reports/landscape/network_resume_v1/20261010_4675893f/`.

- `preflight.json`: SHA-256
  `6f8915ebaf4046ad7404685b785a58e83a88e28715597dc1c5f8c7878fd7a2fd`.
- `quota_observation.json`: SHA-256
  `87470d6bb3f95ac7f201e0739622721bb9e175f2d3dd6ba3806309f7e8d7c0a9`.

Bu salt okunur teşhis için üretim kodu değişmedi; yeni davranış testi
gerektiren bir kod değişikliği yok. JSON/hash, checkpoint sözleşmesi,
kimlikle hizmet ve gerçek süreç kontrolleri yapıldı. Kimlik bilgileri
rapora alınmadı. GCP VM'deki iş bu yerel kontrolde sorgulanmadı veya
değiştirilmedi. Etiket ve kapalı 2025 final testi açılmadı.
