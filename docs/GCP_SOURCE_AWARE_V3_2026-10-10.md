# Doğrulanmış zaman çözümlemesiyle V3 devam — 10 Ekim 2026

## Paylaşılan ilk V3 çalışma durumu

Kullanıcının VM sorgusunda üst Python süreci PID 1677 ile canlı, çalışma
süresi 2 dakika 14 saniye. Progress `running`; wrapper ve adapter hash'leri
hazırlanmış sürümle eşleşiyor. Launcher 15 incelenmiş V2 tanısının saklandığını
ve `december_safe_days` aşamasına girişini bildiriyor. Yeni uygulama deadline'ı
10 Ekim 09:58:35,730711 UTC, Türkiye saatiyle 12:58:35. İlk progress okuması
Drive başlangıç kontrolleri bitmeden eski V2 son durumunu göstermişti.
Sonraki çıktı V3 durumunun yazıldığını doğruluyor. Bu uzak çıktı kullanıcı
tarafından paylaşıldı; canlı API denetimi, yeni kaynak işlem başarısı veya
uzun oturum bitiş kabulü değildir. Hazırlık kaydı aşağıda korunmuştur.

## Gerçek kaynak kabulü

Son `gcp_scan_iso_adapter_proof_20261010T014316599475Z.json` dosyası 3.233
bayt; SHA-256 `edfba0a8a87cdbf642e9cfd31a9d7d3115ac3281003b844135e1b127369621ea`.
Üretim girdileri önceki hatalı replay ile birebir aynı hash'lere sahip.
Üç sütunun 203'er UTC zamanı ham TAI93 dönüşümüyle nanosaniyesine kadar
eşleşti. Adapter altında özgün scan fonksiyonu 203 tarama, 1.889 scan–grid
satırı üretti ve native hücre sayımları eşleşti. Pandas isim alanı geri
yüklendi; kaynak dosyaları değişmedi, yeni indirme/üretim yazımı yok.
Yerel geri okuma `scan_iso_adapter_readback.json` içinde tutuldu.

Bu, önceki [tarih biçimi düzeltmesinin](GCP_SCAN_TIME_FIX_2026-10-10.md)
tek gerçek kaynakta kabulüdür. Başka kaynak hatalarının olmayacağı, tüm
ayların tamamlandığı veya uzak listede bulunan 14 aya yeni yerel kabul
verildiği anlamına gelmez. Kullanıcı indirmeden sonra VM'nin Stopped
olduğunu teyit etti; canlı API sorgusu veya yeni üretim oturumu yapılmadı.

## V3 davranışı ve yöntem kaydı

Yeni `run_gcp_source_aware_continuation_v3.py`, V2'nin dönem sıralamasını,
31 Aralık 2023 ertelemesini, 24 çift/4 günlük işçi gate'ini, gizli auth pipe'ını,
tek iş kilidini, rezervleri ve otomatik poweroff davranışını korur. Orijinal
bilimsel/controller paketleri, registry, gate, katalog, checkpoint anahtarları
ve kabul edilmiş ürünler değiştirilmez. Log yeni `gcp_source_aware_launcher_v3.log`
dosyasına yazılır. Yeni ebeveyn hataları ayrı `parent_failure_v3_<UTC>.json`
dosyalarına kaydedilir.

V3 her girişte gerçek başarılı proof dosyasını ve daha önce VM'ye yüklenen
`verify_gcp_scan_iso_adapter.py` dosyasını hash ile doğrular. Çift çocuğunda,
bilimsel klon üyeleri doğrulandıktan sonra yalnız scan modülünün üç UTC
çağrısına sınırlandırılmış adapter uygulanır. Özgün zaman eşitliği, scan
kalitesi/sırası, kaynak kimliği ve hücre sayım kontrolleri aynen çalışır.
Yanlış tarih sessizce eksik değere dönüştürülmez veya yuvarlanmaz.

Yeni hesaplanan çiftlerin `scan_provenance.json` dosyasında
`scan_time_parser_adapter` kaydı adapter/proof/V3 hash'lerini ve uygulanan
çağrıları belirtir. Progress/final durum aynı adapter kimliğini içerir.
Bu kayıt bilimsel kaynak dosyasının hash'i ile çalışma zamanı davranışını
ayırır: eski worker SHA, dondurulmuş kod dosyasının kimliğidir; bütün yürütmenin
adapter kullanılmadan gerçekleştiği iddiası değildir. Eski çift checkpoint'i
geçerli ise native ürünler ve hash'ler değiştirilmeden yeniden kullanılır.

İlk V3 başlangıcında eski son durum ve gerçek proof girdileri tekrar eşleşir.
Yalnız incelenmiş 15 V2 çocuk tanısı, bütün baytları korunarak
`wildfire-gcp-production-v1/diagnostics/reviewed_v2/` dizinine taşınır.
Taşımanın manifesti ve dosya hash'leri `receipt.json` içinde saklanır.
İşlem tek iş kilidi altında gerçekleşir; önce tüm girdiler denetlenir.
Kısmi taşıma sonradan kayıp/üzerine yazma olmadan tamamlanabilir. Ham kaynak,
bilimsel ürün, checkpoint veya tam ay silinmez. Başarılı task'ın normal
cleanup'ı merkezi tanı arşivini silmez. Yeni veya değişmiş başarısızlık
otomatik olarak yeniden denenmez; inceleme gerektirir.

Sonraki normal rezerv duruşlarında V3 kimliğiyle yeniden giriş desteklenir.
Yeni V3 hata durumunda veya bilinmeyen başka çocuk hata dosyasında başlatma
reddedilir. Supervisor kilidi aldıktan sonraki hata, rezerv veya bitiş
kapatma isteğine gider. Başlangıç kontrolünün reddi manuel Stop gerektirir.

## Yerel kontroller

20 yeni V3 kontrolü dahil **94 ilgili test geçti**. Önceki erteleme, sayım,
rezerv, güvenli hata ve kod kimliği kuralları korundu. Yeni testler gerçek
proof/değişmiş proof reddini, adapter factory/isim alanı geri yüklemesini,
provenance kimliğini, yazmayan preflight'ı, tanı baytlarının saklanmasını,
yarım taşımanın devamını ve yeni hata/ham veri/durum değişiminin reddini
kontrol etti. Gerçek eski Kasım checkpoint'iyle V3 çocuk CLI denemesi ağ
engellenerek geçti: native ürünlerin baytları aynı, indirme sıfır.

Ardından aynı integration testine ayrı, yalnız fixture amaçlı provenance
alanı ekleme kontrolü dahil edildi ve test tekrar geçti. Ayrı geçici
üründeki metadata uzantısı dondurulmuş checkpoint/bilimsel geri okumadan
geçti; kabul edilmiş asıl arşiv değiştirilmedi. Günlük birleştirmenin
zaman kontrolü scalar Timestamp kullanır; ilgili kodda ikinci toplu parser
uygulaması gerekmedi. Ruff geçti. Canlı bitki örtüsü hazırlığının kaynak
hash'leri korunmuştur. Bunlar gerçek yeni uzun VM oturumunun kabulü değildir.

## Uzun oturuma geçiş

1. Yeni tek dosyayı hazırla:
   `C:\PROJELERIM\wildfire-risk-prediction\outputs\gcp_acceleration\source_aware_v3_2026-10-10\run_gcp_source_aware_continuation_v3.py`.
2. VM Start → SSH → Upload File ile ev dizinine yükle. Önceki helper'lar,
   proof/snapshot JSON'ları, registry ve özel bağlantı dosyası VM'de kalmalıdır.
   Yerel kimlik bilgisi JSON'u yeniden yüklenmez veya paylaşılmaz.
3. SSH'de yeni dosyanın hash'ini kontrol et:

```bash
printf '%s  %s\n' \
  '792d774f53c2a7249a10f4111f2f785e08d5bd2a8153e1151c73efe493b5942e' \
  "$HOME/run_gcp_source_aware_continuation_v3.py" | sha256sum --check
```

OK çıkmazsa uzun komutu çalıştırma; VM Stop ve kısa hata satırı paylaş.

4. **Cloud Shell**'de mevcut oturumun ayarlarını ve gerçek Google durma
   zamanını al. Cloud Shell, VM'nin SSH terminalinden ayrı ortamdır:

```bash
gcloud compute instances describe wildfire-cpu-pilot \
  --project=dogalafetonlemesistemi --zone=europe-west3-c \
  --format='yaml(status,machineType,scheduling.maxRunDuration,scheduling.instanceTerminationAction,scheduling.automaticRestart,resourceStatus.scheduling.terminationTimestamp)'
```

RUNNING, n2-standard-32, 28800 saniye, STOP ve automaticRestart false
beklenir. Yeni `terminationTimestamp` değeri kullanılmalı; eski oturumun
zamanı kullanılmaz. Faturalandırmada Free Trial dışına çıkılmaz; Upgrade yapılmaz.

5. **VM SSH**'de şu satırı ayrı çalıştır; yeni timestamp'i gir ve Enter'a bas:

```bash
read -r -p "Yeni Google durma zamani: " termination
```

Ardından üretimi bir kez başlat:

```bash
~/wildfire-gcp-work/.venv/bin/python ~/run_gcp_source_aware_continuation_v3.py \
  --registry ~/source_blocks.json \
  --registry-sha 6f4eb9fd307ef892a3d3446ef14f32fb758bfd4c59c98b77dce82410e859dd5d \
  --termination "$termination" \
  --poweroff
```

Earthdata kullanıcı adı/parola girişinde karakterler görünmez; bunlar sohbet
ve loga gönderilmez. Detached mesajı başlangıç isteğidir. Gerçek ilerleme:

```bash
tail -n 30 ~/gcp_source_aware_launcher_v3.log
cat ~/wildfire-gcp-production-v1/progress.json
```

İlk aşamada tamamlanmış aylar ve Aralık 2023'ün güvenli günleri doğrulanarak
kullanılır; sonra Eylül 2022'nin kalan kısmına ve diğer eğitim aylarına geçilir.
Ay listesi yeniden doğrulama sırasında kısa başlayabilir; kayıt kaybı değildir.
Kısmi çiftlerde gereken hesap yeniden yapılabilir, tam dönem sıfırlanmaz.

VM işi için ilerleme doğrulanınca SSH sekmesi kapatılabilir; 20–30 dakikada
bir kontrol yeterlidir. Bilgisayarda yürüyen bağımsız bitki örtüsü işi
tamamlanana kadar bilgisayar açık ve uyku dışında kalmalıdır. Bitiş, hata veya rezerv sonrası supervisor kapatma
ister; Google'ın sekiz saat STOP sınırı ek koruma olarak kalır. Sekiz saat
bütün ayların bitiş garantisi değildir. Stop kaynak silme değildir; doğrulanmış
sonuçlar alındıktan sonraki son kaldırma planı [ayrı belgededir](GCP_FINAL_CLEANUP.md).
