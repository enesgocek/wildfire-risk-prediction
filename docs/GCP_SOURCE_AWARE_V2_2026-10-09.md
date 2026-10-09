# Doğrulanmış kayıtlarla devam ve güvenli hata tanıları

Kayıt tarihi: 9 Ekim 2026. Önceki hatanın kesin nedeni belirlenmiş değildir.
Yeni V2, bilimsel hesap veya hız değişikliği değil, hata gözlenebilirliği sürümüdür.
Gerçek yeni VM oturumu henüz başlatılmadı.

## Yeniden deneme kararı ve kanıt

İndirilen salt okunur Drive teşhisi `readonly_checks_passed` durumunda.
Teşhis nesne yazmamış, ham işleme yapmamış. JSON 4.444 bayt; SHA-256
`0e7eb0a5e3633757e7566ac61d4a91ee8a2e95c4834b22881b896dc1e9dd21e1`.
Kasım manifesti uzak completion/payload ile yerel bytes düzeyinde eşleşmiş.
Üretim kapsamı listesinde 7.412 nesne, 10.266.240.315 bayt saklanmış veri var.
Kimlik/kota/listing kontrolleri başarılı; kalan 19 tam çiftin tamamında uzak
payload ve completion henüz yok (`not_published`).

API kota sınırı 429.496.729.600, kullanım 44.925.083.963 bayt; boş alan
384.571.645.637 bayt, yaklaşık 384,6 GB. Bu kapasite ölçümü faturalandırma
kredisi veya maliyet hesabı değildir. Güncel erişimin başarısı geçmişteki
hata nedenini kanıtlamaz. Yerel 19 ZIP'in kimlik/hash/boyutları bu teşhisle
çapraz kontrol edildi; rapor
`outputs/gcp_acceleration/continuation_failure_2026-10-09/publication_probe_verified.json`.

Önceki öneri hata nedeni belirlenene kadar beklemekti. Ek denetimler, güncel
bir erişim/kota veya yerel tam ürün bozukluğu göstermedi. Bu nedenle bütün
kayıtları koruyup mevcut bilimsel kontroller altında yeniden deneme,
tekrar hata olduğunda ayrıntıyı güvenli kaydetme koşuluyla planlandı.
Bu karar kök nedenin çözüldüğü veya yeniden hata olmayacağı iddiası değildir.

## V2 kapsamı

`run_gcp_source_aware_continuation_v2.py` ayrı dosyadır. V1, controller,
bilimsel paket, katalog, registry, gate ve checkpoint namespace'i değişmedi.
Kaynak erteleme/sayım kurallarını uygulayan beş yardımcı AST düzeyinde V1
ile aynı. Negatif etiket izni false, gözlem unknown; 31 Aralık ertelemesi
sürüyor. 24 çift/4 günlük işçi, tek iş kilidi, çocuk süre/kaynak sınırları,
sekiz saat bütçe ve supervisor poweroff kuralları korunuyor.

Ek tanılar:

- Drive hatası sırasında yalnız HTTP rolü, durum kodu ve izinli neden sınıfı
  kaydedilir. URL, HTTP response metni, OAuth/Earthdata bilgisi veya traceback yazılmaz.
- Ebeveyn hatası güvenli sınıf/literal kontrol adıyla, ayrı UTC adlı yeni
  `wildfire-gcp-production-v1/diagnostics/parent_failure_v2_*.json` dosyasına yazılır.
- Python hata JSON'u bırakmayan çocuk süreçte çıkış kodu kaydedilir; kod
  tek başına ölüm nedeninin kesin kanıtı sayılmaz.
- V2 launcher günlüğü `~/gcp_source_aware_launcher_v2.log`; önceki log korunur.

20 ilgili test geçti: alınan gerçek Drive raporunun hash/kimlik/boyut eşleşmesi
ve değiştirilmiş rapor reddi; V1 erteleme/sayım/rezerv kuralları; güvenli
HTTP/ebeveyn tanıları, ayrı hata dosyaları, çocuk exit kodu ve factory geri
yükleme. Gerçek bir Kasım VM checkpoint'iyle yeni çocuk CLI ağ engellenerek
çalıştırıldı: bütün native ürün bytes aynı, ham indirme sıfır. Bu tek checkpoint
yeniden kullanım denemesidir; bütün kayıtların gerçek yeni VM oturumunda
kapanışı veya bağımsız bütün ay kabulü değildir. Ruff başarılı.

## Kullanıcı adımları

1. Yeni dosyayı hazırla:
   `C:\PROJELERIM\wildfire-risk-prediction\outputs\gcp_acceleration\source_aware_v2_2026-10-09\run_gcp_source_aware_continuation_v2.py`.
2. VM Start → SSH. Upload File ile bu tek dosyayı ev dizinine yükle.
   Mevcut registry/özel bağlantı/orijinal paketler kalır; yeni kaynak oluşturulmaz.
3. VM SSH'de dosya bütünlüğünü kontrol et:

```bash
printf '%s  %s\n' \
  '943878d4416ac5c6c42ab73070f420920208fadd62e08e4119eea76341b7a2ea' "$HOME/run_gcp_source_aware_continuation_v2.py" \
  'e1402d4cb28263fe8d05c474656ed64094cd069ca77040ed09e6d0a7296a9c63' "$HOME/diagnose_gcp_production_manifest.py" \
  '6f4eb9fd307ef892a3d3446ef14f32fb758bfd4c59c98b77dce82410e859dd5d' "$HOME/source_blocks.json" \
  | sha256sum --check
```

Üç satır da OK olmalı. Hata varsa üretimi başlatma; VM tekrar Stop ve kısa
hata satırını paylaş. V2, diğer gate/paket hash'lerini başlangıçta doğrular.

4. Cloud Shell'de yeni gerçek Google durma zamanını al:

```bash
gcloud compute instances describe wildfire-cpu-pilot --project=dogalafetonlemesistemi --zone=europe-west3-c --format='yaml(status,machineType,scheduling.maxRunDuration,scheduling.instanceTerminationAction,scheduling.automaticRestart,resourceStatus.scheduling.terminationTimestamp)'
```

RUNNING, n2-standard-32, 28800 saniye, STOP, automaticRestart false beklenir.
Yeni `terminationTimestamp` değeri kullanılmalı; önceki oturumun saati değil.

5. VM SSH'de bu tek satırı ayrı çalıştır, yeni tarihi gir ve Enter'a bas:

```bash
read -r -p "Yeni Google durma zamani: " termination
```

Ardından ayrı olarak üretimi bir kez başlat:

```bash
~/wildfire-gcp-work/.venv/bin/python ~/run_gcp_source_aware_continuation_v2.py \
  --registry ~/source_blocks.json \
  --registry-sha 6f4eb9fd307ef892a3d3446ef14f32fb758bfd4c59c98b77dce82410e859dd5d \
  --termination "$termination" \
  --poweroff
```

Earthdata kullanıcı adı/parola gizli girişlidir; karakterler görünmez. Bunlar
sohbete gönderilmez. Detached mesajı yalnız başlatma isteği; gerçek ilerleme:

```bash
tail -n 30 ~/gcp_source_aware_launcher_v2.log
cat ~/wildfire-gcp-production-v1/progress.json
```

İlk aşama Aralık 1–30 ve mevcut tam ayları geri okur; sonra Kasım 2022'den
kalan günlere/aylara döner. Kayıtlar doğrulama üzerinden yeniden kullanılır;
tamamlanmamış işlerde gerekli hesap tekrarlanabilir. Bütün işlemi sıfırlama,
checkpoint veya ham dosya silme yapılmaz. Sıra kayıtları yeniden doğrularken
ilk anda ay listesi küçük görünebilir; bu eski kayıtların silindiği anlamına gelmez.

İlk ilerleme doğrulanınca sekme/bilgisayar kapatılabilir; yaklaşık 20–30
dakikada bir kontrol yeterli. Hata, normal rezerv veya bitiş sonrası supervisor
kapatma ister; Google'ın sekiz saat Stop sınırı da korunur. Başlangıç kontrolü
reddinde manuel Stop gerekir. Sekiz saat bütün yılların tamamlanma garantisi değildir.

V1'e ait eski forensic araçlar V2 hash'ini bilerek kabul etmez; yeni bir hata
olursa V2'ye bağlı kayıtlarla ayrı toplama/denetim uygulanacaktır. Eski paket
hash'leri bu nedenle gevşetilmez.
