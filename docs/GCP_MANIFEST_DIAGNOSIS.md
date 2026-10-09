# İlk Drive manifest kaydının teşhisi — 7 Ekim 2026

İlk üretim 7 dakika 54 saniyede RuntimeError ile durdu ve supervisor VM
kapatma isteği gönderdi. 556 cache/metadata dosyası, month.json ve
manifest.zip bulunduğunu doğruladım. İşlenen/yeniden kullanılan çift 0;
doğrulanmış gün yok. Sekiz saat sınırı dolmadı. Drive kaydı/geri okuması
adımının HTTP hata nedeni eski güvenlik filtresinde genelleştirilmiş.

AI Pro planının bitip yeniden açıldığını bildirdim; güncel görsel
31,67 GB / 400 GB. Geçici 15 GB kotaya dönüş yazmayı engellemiş olabilir.
Bu bir hipotezdir; yenilenen planın OAuth hesabına yansıdığı doğrulanmadı.
[Kota etkileri](https://support.google.com/googleone/answer/6374270?hl=en)
ve [depolama güncellemesinin gecikmesi](https://support.google.com/drive/answer/2375123?hl=en).

`scripts/cloud/diagnose_gcp_production_manifest.py` orijinal paket manifest
SHA'sını ve 11 üyenin hash'ini import öncesi doğrular. Aynı job.lock'u alır;
mevcut aylık metadata ZIP'ini orijinal bilimsel doğrulayıcıyla kontrol eder.
Bağlı hesabın storageQuota alanını okur, yalnızca sayısal kullanım/sınır
değerlerini gösterir. HTTP hatalarında yalnızca kod ve izin verilen neden
isimlerini gösterir; ad/kimlik/token/yanıt mesajı göstermez.

Varsayılan salt okunur. `--publish` yalnızca aynı kapsamlı ilk başarısız
oturum (0 çift, 0 gün) için hazır metadata ZIP'ini orijinal store protokolüyle
kaydeder. ZIP 20 MB üst sınırıyla kısıtlıdır; payload bağımsız geri okunup
doğrulanmadan completion yazılmaz. Mevcut doğrulanmış kayıt tekrar yazılmaz.
NASA isteği, ham işleme, paket değişimi veya VM/billing ayarı yok.

VM home dizinine yalnızca outputs/gcp_production_diagnosis altındaki dışa
aktarılmış .py yüklenir. SHA diagnostic_report.json ile karşılaştırılır.
SSH'de çalıştırma:

```bash
timeout 180s ~/wildfire-gcp-work/.venv/bin/python \
  ~/diagnose_gcp_production_manifest.py --publish
```

`MANIFEST_READY` kayıt ve geri okumanın geçtiğini gösterir; uzun üretim
başlamaz. Hata halinde HTTP_DIAGNOSTIC/FAIL ve kota sayıları incelenir.
Çıktı alındıktan sonra Console Stop uygulanır; duruş kendiliğinden yapılmaz.
Yeni uzun başlangıçta güncel Google terminationTimestamp alınmalıdır.
Eski progress.json bu teşhisten sonra da başarısız oturumu anlatabilir.

İlgili 121 test ve Ruff kod/biçim kontrolü başarılı. Sonraki
VM çıktısında orijinal paket, kapsam ve yerel bilimsel kontroller geçti.
Manifest ZIP 736.111 bayt; bağlantı/refresh/klasör/kota kontrolleri başarılı.
API kotası ondalık GB olarak kullanım 34,00, sınır 429,50, boş 395,49.
Önceden kayıt yoktu; publish ve bağımsız geri okuma geçti:
`MANIFEST_READY published and verified; raw processing not started`.
Bu paylaşılan terminal çıktısına dayalı kanıttır; yerelde sonuç ZIP'i ayrıca alınmadı.
Geçmiş kota aşımı kesinleşmedi; mevcut Drive yazma engeli görülmedi.
Yeni uzun kuyruk henüz başlatılmış sayılmıyor; güncel Google son zamanı
ile aynı paket tekrar çalıştırılacak. Yeni push yapılmadı.
