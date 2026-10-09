# Mevcut VM'de iki saatlik paralellik ölçümü

> Dönemsel uygulama kaydı. Kurulum, maliyet ve bekleyen iş ifadeleri belgenin
> ilgili çalışma aşamasına aittir. Güncel durum [STATUS.md](STATUS.md), mevcut
> üretim yolu [devam rehberinde](GCP_SOURCE_AWARE_CONTINUATION_2026-10-09.md) izlenir.

Paket hazır; VM üzerinde bu test henüz çalıştırılmadı. Mevcut VM'nin boş kapasitesini ölçmek için iki saatlik oturum planlandı.
Yeni VM veya ücretli hesaba geçiş gerekmiyor. Mevcut makine
`wildfire-cpu-pilot`, `europe-west3-c`, e2-standard-8, 8 vCPU / 32 GB.

## Ne ölçeceğiz?

4 → 8 → 12 → tekrar 4 işçi ile **aynı 28 çift ve aynı üç tam gün**.
13–15 Ekim 2023'ün bütün nominal çiftleri kullanılıyor; rastgele örnekleme
yok. Mevcut doğrulanmış sonuçlara karşı ham kaynak SHA ve dört native CSV
hash'i karşılaştırılacak. Günlük geometrik union aynı donmuş kodla üretilecek;
Drive'a yazma ve ayrı geri okuma da ölçülen toplam süreye dahil.

Son 4 işçi ölçümü ağ/NASA/Drive hızının zaman içinde değişip değişmediğini
gösterecek. CPU doluluğu veya RAM kullanımı tek başına başarı ölçüsü değil.
İşlenen çift/saat ve günlük kapanış dahil toplam süre asıl ölçü.

- Her profilde yaklaşık 5,14 GB, toplam **20.559.071.684 bayt** ham indirme.
  Ağ yeniden denemeleri bunun üzerine trafik ekleyebilir.
- Bu bir tekrar ölçümü; yeni üretim günü/ayı tamamlandı sayılmayacak.
- İşçi havuzu tamamlanan işi bekleyen Drive yayını sırasında yeniden doldurur.
  Bu nedenle deney, artan işçi sayısıyla birlikte bu zamanlama yöntemini de
  ölçer; eski dalga yöntemine göre kazanım yalnızca işçi sayısına bağlanamaz.
- Tüm dönem için aynı hız, kusursuzluk veya 12 işçinin üstünlüğü garanti değil.
- En az 4 GiB kullanılabilir RAM ve 4 GiB boş disk korunur. Örnekleme
  iki saniyede bir; kısa tepe değerleri kaçabilir. Bilimsel pair alt süreçlerinde
  orijinal 6 GiB adres alanı limiti de korunur.
- Deney başlangıcından itibaren en fazla 90 dakika ayrılır; Google'ın
  iki saatlik Stop sınırı ayrıca geçerli. Yeni işe başlamadan süre rezervi
  kontrol edilir. Ana süreçteki ağ/Drive çağrılarına da süre alarmı uygulanır.
  Dört profil bitmezse kısmi sonuçtan hız kazananı seçilmez.
- Özel test çalışma dizini `~/wildfire-gcp-tuning-v1`; Drive'da ayrı manifest
  namespace'i ve en fazla 2 GiB test kaydı. Üretimin lock'u deney boyunca
  tutulur; ilerleme dosyasının aynı kaldığı sonunda denetlenir.
- Orijinal üretim paketi, bilimsel kodlar ve production scope değişmez.
  Sekmeyi kapatınca detached çalışma devam eder. `--poweroff` ile sonunda
  konuk sistem kapanması istenir; Google Stop ikinci sınırdır.

## Başlatma adımları

**1. VM hâlâ kapalıyken:** Google Cloud → Compute Engine → VM instances →
wildfire-cpu-pilot → Edit. Zaman sınırını **2 saat**, termination action
**Stop**, automatic restart **Off** yapıp Save. Makine ve diski değiştirme.
Ücretli **Upgrade / Activate** düğmesine basma.

**2. Start → SSH.** SSH penceresinin Upload File düğmesiyle yalnızca şunu
yükle:

`C:\PROJELERIM\wildfire-risk-prediction\outputs\gcp_tuning\wildfire_gcp_tuning.zip`

Özel bağlantı/OAuth JSON'unu yeniden yüklemek gerekmiyor; mevcut özel dosya
VM'de kullanılacak. Paket beş üye, 620.491 bayt; SHA256:
`0caabe13761f5253dc2ba939e6d01dc268e6b13c550c87729e453557c2133050`.

**3. VM'nin SSH terminalinde bu bloğu bir kez yapıştır:**

```bash
~/wildfire-gcp-work/.venv/bin/python - <<'PY'
from pathlib import Path
import hashlib, json, zipfile
p = Path.home() / 'wildfire_gcp_tuning.zip'
expected = '0caabe13761f5253dc2ba939e6d01dc268e6b13c550c87729e453557c2133050'
assert hashlib.sha256(p.read_bytes()).hexdigest() == expected, 'Paket SHA farkli'
dest = Path.home() / 'wildfire-gcp-tuning-package'
assert not dest.exists(), 'Paket dizini zaten var; tekrar baslatma'
names = {'run_gcp_tuning.py', 'gcp_tuning_resources.py', 'tuning_plan.json',
         'month_manifest.zip', 'tuning_manifest.json'}
with zipfile.ZipFile(p) as z:
    assert set(z.namelist()) == names and len(z.infolist()) == 5
    assert z.testzip() is None
    assert all(0 < i.file_size < 2_000_000 for i in z.infolist())
    spec = json.loads(z.read('tuning_manifest.json'))
    assert set(spec['files']) == names - {'tuning_manifest.json'}
    for n, checksum in spec['files'].items():
        assert hashlib.sha256(z.read(n)).hexdigest() == checksum
    dest.mkdir(mode=0o700)
    for n in names:
        (dest / n).write_bytes(z.read(n))
print('Tuning paketi dogrulandi ve kuruldu')
PY
```

**4. Cloud Shell'de yeni durma saatini al:** Cloud Shell ayrı paneldir;
komut gcloud içindir. Eski sekiz saatlik tarihin kopyasını kullanma.

```bash
gcloud compute instances describe wildfire-cpu-pilot \
  --project=dogalafetonlemesistemi \
  --zone=europe-west3-c \
  --format='yaml(status,scheduling.maxRunDuration,scheduling.instanceTerminationAction,resourceStatus.scheduling.terminationTimestamp)'
```

`RUNNING`, `seconds: '7200'`, `STOP` görünmeli. `terminationTimestamp`
satırındaki güncel ISO tarih/saat değerini tırnaklar olmadan kopyala.

**5. Tekrar VM'nin SSH terminalinde:**

```bash
read -r -p "Google durma zamani: " termination
~/wildfire-gcp-work/.venv/bin/python \
  ~/wildfire-gcp-tuning-package/run_gcp_tuning.py \
  --connection ~/.config/wildfire/drive_connection.json \
  --termination "$termination" \
  --poweroff
```

Google durma zamanını isteyen ilk satıra kopyaladığın yeni saati yapıştırıp
Enter. Ardından Earthdata kullanıcı adı ve parola istenecek; **yazdığın
karakterler görünmez**, bu normaldir. Bilgilerini terminalde gir; sohbette
paylaşma. `Detached tuning launch requested` çıktısı başlatma isteği;
gerçek profil çalışmasını aşağıdaki günlükten kontrol et.

**6. İlk kontrol:**

```bash
tail -n 15 ~/gcp_tuning_launcher.log
```

`PROFILE START four_before workers 4`, sonrasında `pair saved/verified`
satırları gelmeli. Profil sonunda `PROFILE COMPLETE`, ardından eight/twelve/
four_after gelir. Başlangıç kontrolü başarılıysa sekmeyi/bilgisayarı kapatabilirsin.
Sürekli izlemek gerekmiyor. İsteğe bağlı olarak 10–15 dakika sonra aynı salt okunur
komutla bak. Hata/partial satırı olursa aynı paketi yeniden başlatma; çıktıyı paylaş.

**7. Sonuçları alma:** Dört profil bitince veya güvenli test duruşunda
`Download: /home/enesnuhgocek1/gcp_tuning_results.zip` yazılır ve VM'ye
kapanma isteği gider. VM zaten Stopped ise **yalnızca dosyayı indirmek için**
kısa süre Start → SSH aç. Çalışma otomatik yeniden başlamaz.

SSH → Download File:

`/home/enesnuhgocek1/gcp_tuning_results.zip`

Yerelde `C:\PROJELERIM\wildfire-risk-prediction\outputs\gcp_tuning\received\`
klasörüne koy. Ardından VM'yi tekrar Stop yap. Yerel doğrulama sırasında
açık kalmasına gerek yok. ZIP yoksa günlük hatasını paylaş; test dizinini
silme veya bütün deneyi tekrar etme.

## Sonuçtan sonraki karar

Hazır yerel okuyucu `scripts/cloud/verify_gcp_tuning_results.py` önce paket/
metadata SHA, 112 cold çift kaydı, 12 günlük payload, CMR kaynak journal'ları,
aynı native CSV hash'leri ve profiller arası günlük tabloları kontrol eder.
Kaynak örneklerinden CPU, RAM ve disk istatistiklerini yeniden hesaplar.
Kısmi veya dengesiz testten kazanan seçmez. Baz tekrar oranı 0,8–1,25 dışında
olursa ağ/zaman etkisi ayrışmadığı için hız kararı bekler.

8/12 adayının her iki 4 işçi ölçümünden de en az %15 hızlı olması gerekir.
Birbirlerine %5 yakınsa daha az işçili seçenek tercih edilir. Bunlar
önceden konmuş pratik karar eşikleri; istatistiksel güven aralığı değildir.
Yeni üretim sürücüsü ve eski checkpoint'lerle devam uyumu ayrıca doğrulanır;
sonra 8 saatlik üretim oturumuna geçeriz. Bu paket orijinal üretim işçi
sayısını değiştirmez ve sekiz saatlik işi kendiliğinden başlatmaz.

## Kredi ve kapanış

8 Ekim hesap ekranı: ay içinde 80,11 TL kullanım ve aynı tutarda
indirim, net 0 TL; kalan deneme kredisi 13.519 TL ve 18 gün. Ay içi kullanım
ile tüm deneme kredisi farkı aynı dönem değildir. Kullanım ekranına veriler
gecikmeli gelebilir; oturum maliyeti sonuç faturalandırmasıyla tekrar kontrol
edilecek. [Google Billing raporları](https://docs.cloud.google.com/billing/docs/how-to/reports).

Hesap Free Trial olarak kalacak; ücretli yükseltme yapılmayacak.
[Google Free Trial koşulları](https://docs.cloud.google.com/free/docs/free-cloud-features).
Stop sonrasında disk saklanır ve kredi tüketimi sürebilir. Üretim tamamen
bitip tüm sonuçlar bağımsız doğrulanınca VM, bağlı disk, ayrılmış IP/snapshot
gibi kaynaklar envanter üzerinden temizlenecek; kapanış doğrulanmadan
"maliyet sıfırlandı" denmeyecek. Şu anki üretim kayıtları korunacağı için
bu ölçümün başında veya sonunda diski silmiyoruz.

## Yerel hazırlık kanıtı

Süre alarmı ve rehberdeki kurulum bloğu dahil 24 koruyucu test ile iki
gerçek ürün provası geçti. Sahte çocukların eşzamanlı başlangıcı için
testte barrier kullanılarak işletim sistemi zamanlamasından doğan oynaklık
giderildi; 24 koruyucu test son durumda tekrar geçti. Windows üzerindeki
Linux grup temizliği mock'una SIGKILL sabiti eklendi. Ruff kod/biçim kontrolü başarılı.
Bir gerçek native pair ZIP'i ayrı
test scope'una yazma/geri okuma provası geçti; ham kaynak indirmesi yok.
15 Ekim'in mevcut on native çıktısı ile günlük geometrik union da geçici
yerel provada üretildi; üretim kaydı olarak Drive'a yazılmadı. Bu gerçek
günlük sonuç ve 13/14 Ekim sonuçlarıyla okuyucunun 12 günlük payload kontrolü
geçti. Prova süreleri yapaydı; Linux VM performansı veya canlı Drive erişimi
kanıtı değildir.
Orijinal üretim ZIP SHA'sı a930d3438a6745d76bfb642d008d298d907ce0cf2fb89811cf9e2ff7d4252571.
