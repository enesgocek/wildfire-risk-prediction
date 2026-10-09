# Doğrulanmış yeni hatla sekiz saatlik üretim

**9 Ekim durum değişikliği:** Aralık 2023 içindeki geolocation kaynak
eşleşme sorunu teşhis edildi. 31 Aralık'ı eksik bırakıp diğer
aylara devam etmeyi onayladım. **Yeni çalıştırmada aşağıdaki eski komut
yerine [güncel devam rehberini](GCP_SOURCE_AWARE_CONTINUATION_2026-10-09.md)
kullan.** Doğrulanmış eski paket ve hazır-kayıt değiştirilmiyor.

Gerçek deney ve bağımsız geri okuma geçti. Aynı VM ve mevcut doğrulanmış
controller paketi kullanılacak; seçilen ayar 24 çift ve en fazla 4 günlük
birleştirme işçisi. VM'nin Stopped olduğunu teyit ettim.
Yeni bir benchmark veya Python kurulumu gerekmiyor.
[Ölçülen hız ve sınırları](GCP_ACCELERATION_RESULTS_2026-10-08.md).

## 1 — Kapalı VM'nin sınırını değiştir

Google Cloud → Compute Engine → VM instances → **wildfire-cpu-pilot → Edit**:

- Machine type **n2-standard-32** aynı kalsın.
- Provisioning model **Standard**.
- Time limit → By hours → **8**.
- On VM termination **Stop**, Automatic restart **Off**.
- Mevcut Ubuntu 24.04 ve 30 GB disk aynı; ek kaynak ekleme.
- **Save**, sonra **Start → SSH**. Free Trial korunur; ücretli Upgrade yok.

Bu ayar bütün yılların sekiz saatte biteceği anlamına gelmez. Uygulama süre
rezervinde yeni iş almayı keser; doğrulanmış checkpoint'ler kalır. Sonraki
oturumda kaldığı yerden devam edilir. Uygulama 24 Ekim UTC kesmesini de uygular.

## 2 — Yalnız secretsiz hazır-kaydını yükle

SSH → Upload File ile şu dosyayı yükle:

`C:\PROJELERIM\wildfire-risk-prediction\outputs\gcp_acceleration\readback\production_readiness.json`

Bu dosya deney sonucunun hazır-kaydıdır; içerik hash'i ve seçilen işçi sayıları
vardır, hesap parolası veya OAuth token içermez. Özel bağlantı dosyası VM'de
kalır. Controller ZIP'i yeniden yüklemek gerekmiyor.

**VM SSH'de** yüklemeyi kontrol et:

```bash
printf '%s  %s\n' \
  'ac1f974daaf97a0a8392e9d6b225b4a7753147a9e527ec05caca4e6ea1cac3ef' \
  "$HOME/production_readiness.json" | sha256sum --check
```

`/home/enesnuhgocek1/production_readiness.json: OK` beklenir. Farklı dosya
veya hash hatası varsa ilerleme; yüklenen dosyanın adını/konumunu kontrol et.
Program hem gate SHA/CPU/politika hem kendi ve orijinal paket üye hash'lerini
başlangıçta tekrar kontrol eder. Eski proof dosyalarına dokunmaz.

## 3 — Yeni Google durma saatini al

**Cloud Shell'de** aşağıdaki tek komut:

```bash
gcloud compute instances describe wildfire-cpu-pilot \
  --project=dogalafetonlemesistemi \
  --zone=europe-west3-c \
  --format='yaml(status,machineType,scheduling.maxRunDuration,scheduling.instanceTerminationAction,resourceStatus.scheduling.terminationTimestamp)'
```

RUNNING, n2-standard-32, seconds **28800**, action **STOP** beklenir.
`terminationTimestamp` satırındaki yeni ISO zamanını tırnaklar olmadan kopyala.
İki saatlik deneyin eski durma saatini kullanma.

## 4 — Üretimi bir kez başlat

**VM SSH'de** önce şu tek satırı çalıştır, yeni Google durma saatini yapıştır
ve Enter'a bas:

```bash
read -r -p "Google durma zamani: " termination
```

Sonra aşağıdaki bloğu ayrı yapıştır:

```bash
~/wildfire-gcp-work/.venv/bin/python \
  ~/wildfire-gcp-acceleration-package/run_gcp_acceleration.py \
  --mode production --cpus 32 \
  --connection ~/.config/wildfire/drive_connection.json \
  --termination "$termination" \
  --gate ~/production_readiness.json \
  --gate-sha ac1f974daaf97a0a8392e9d6b225b4a7753147a9e527ec05caca4e6ea1cac3ef \
  --poweroff
```

Earthdata kullanıcı adı/parola terminalde gizli girişle istenir; yazılan
karakterler görünmez. Kimlik bilgileri raporlara veya paylaşılan çıktılara eklenmemelidir. Detached acceleration launch
requested başlatma isteğidir; günlükten gerçek ilerlemeyi kontrol et.

## 5 — İlk ilerlemeyi kontrol et

```bash
tail -n 25 ~/gcp_acceleration_launcher.log
cat ~/wildfire-gcp-production-v1/progress.json
```

Launcher geçmiş deney satırlarını da içerir; yeni son satırlara bak.
Başlangıçta Ağustos/Eylül aylık kayıtları bilimsel olarak yeniden okunabilir;
`Month verified/reused` bunların ham indirmeyle baştan işlenmesi değildir.
Ekim 1–14 günlük kayıtları ve 15 Ekim'in 10 çift kaydı denetlenip kullanılır;
bekleyen günlük kapanış tamamlanır ve sonraki gün/aylara geçilir.

Progress'te `cpu_count:32`, `pair_workers:24`, `daily_workers:4`,
`controller_manifest_sha256:102c9e4ab16e4450d0d94eb3511dfdbf360fd6b6292809c5457efc93d2be5837`
beklenir. Orijinal queue scope aynı kalır:
`0c5302cadf0c05dce36843254300cd8719346ddac4648c78c5c20a7dfd8f7394`.
Saved/verified ve DAY COMMITTED yalnız ilgili geri okuma başarılıysa görünür.
Ay listeye ancak tam aylık kayıt denetiminden sonra eklenir.

Başlangıç ilerlemesi doğrulandıktan sonra sekmeyi veya bilgisayarı
kapatabilirsin. Oturum sırasında isteğe bağlı 30–60 dakika aralıklarla aynı
salt okunur komutlar yeterli. Üretim çalışırken komutu yeniden başlatma.
Hata sınıfı/phase görüldüğünde günlük/progress paylaş; özel JSON'u okuma.

## Oturum sonu

Uygulama güvenli süre rezervinde checkpoint'leri tutup kapanma isteği gönderir;
Google'ın sekiz saatlik Stop sınırı ayrıca geçerlidir. Normal rezerv duruşu
`paused_at_runtime_reserve`, hata `failed_checkpoints_retained`, bütün eğitim
ayları doğrulanırsa `all_training_months_verified` olur. Stopped tek başına
bilimsel tamamlanma göstergesi değildir.

Stopped olduğunda Cloud Shell'den süre/durum okunup kısa Start/SSH ile
`progress.json`, `acceleration_run_summary.json` ve loglar alınabilir.
Başlatma kendi başına üretimi otomatik devam ettirmez; yeni gerçek Google
son zamanıyla aynı production komutu gerekir. Kesilmiş, henüz doğrulanmamış
işler yeniden yapılabilir; doğrulanmış çift/gün/aylar hamdan başlatılmaz.

Bu paket üretim modunda `gcp_acceleration_results.zip` adlı yeni benchmark
ZIP'i üretmez; o dosya önceki deneydir. Kalıcı ürünler aynı Drive checkpoint
protokolünde ve mevcut üretim dizininde saklanır. Tam dönem sonunda sonuçlar
bağımsız indirilip doğrulanacak; sonra VM ve disk/snapshot/IP gibi kaynaklar
envanterle temizlenecek. Stop sonrası saklanan disk hâlâ kredi tüketebilir.
Şimdiki hedef, kuyruğu ilerletirken veri ve devam kayıtlarını korumaktır.

## Bütçe

Aylık 1.462,65 USD fiyat gördüm. Bir VM/730 saat/taahhütsüz fiyat
varsayımıyla kaba sekiz saatlik VM tutarı 16,03 USD kredi. Gerçek kullanım
süresi, disk/ağ ve üretimdeki hız ayrıca değerlendirilir. Ücretsiz deneme
bakiyesi ve hesabın Free Trial olduğu koşulu korunur. Tüm işin maliyetini
ilk gerçek uzun üretim ilerlemesiyle yeniden hesaplayacağız.
