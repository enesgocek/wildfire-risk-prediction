# N2 ve örtüşen işlem hattıyla hızlandırma deneyi

Deney tamamlandı: bağımsız kontrol 24/4 ayarı için yaklaşık 1,47 kat hız
kazancını doğruladı; 2–3 kat hedefi henüz kanıtlanmadı.
[Gerçek sonuç](GCP_ACCELERATION_RESULTS_2026-10-08.md) ve
[sekiz saatlik üretim devamı](GCP_ACCELERATED_PRODUCTION_2026-10-08.md).
Bu rehber ilk deneyi kurma kaydıdır; aynı cold deneyi tekrar başlatma.
Önceki gerçek deneyde E2/8 vCPU üzerinde 8 işçi 644,20 saniye,
12 işçi 671,15 saniye sürdü; yalnız işçi sayısını artırmak yeterli olmadı.

## Donanım ve maliyet sınırı

8 Ekim paylaşılan kota çıktısında Frankfurt N2_CPUS 200, global
CPUS_ALL_REGIONS 32, kullanım 0. N2 32 vCPU bu iki kotaya sığıyor;
başlatma anındaki bölgesel kapasite ayrıca Google'a bağlı.
Mevcut `wildfire-cpu-pilot`, `europe-west3-c` düzenlenecek.
N2 ailesine geçerken mevcut Ubuntu ve 30 GB persistent disk korunabilir.
[Google makine değiştirme rehberi](https://docs.cloud.google.com/compute/docs/instances/changing-machine-type-of-stopped-instance),
[bölgesel/global CPU kotaları](https://docs.cloud.google.com/compute/resource-usage).

Son hesap ekranı: Free Trial, ay içi 149 TL kullanım / 149 TL indirim /
net 0 TL, kalan kredi 13.484 TL, 18 gün. Saatlik N2 Frankfurt fiyatı bu
belgede tahmin edilmedi; **Edit ekranındaki yeni maliyet tahminini oku**.
Deneme hesabını ücretli hesaba dönüştürme; **Upgrade / Activate kullanılmaz**.
Google, ücretli hesaba yükseltilmeyen Free Trial'da kişisel ücret alınmadığını
belirtiyor. [Free Trial şartları](https://docs.cloud.google.com/free/docs/free-cloud-features).

## Yazılımda değişenler

- Çift havuzu dolu tutulurken başka günlerin günlük birleşimleri ayrı
  süreçlerde yapılır. 32 vCPU deneyi için 24 çift işçisi + en fazla 4 günlük
  birleştirme işçisi; ana yayın/doğrulama sürecine de CPU payı bırakılır.
- Bilimsel modüllerin ana süreç kontrolleri sırayla çalışır. Donmuş modüllerin
  ortak ROOT değişkenleri işçi thread'lerinden değiştirilmez.
- Aynı yerel payload ve Drive'dan yeni indirilen bağımsız kopya tam bilimsel
  kontrolden geçer. Tamamlanma kaydı en son yazılır; ardından marker ve
  payload tekrar Drive'dan okunup byte eşitliği denetlenir.
- Tek-yazarlı iş kilidiyle Drive nesne listesi indekslenir; her okumada güncel
  metadata ve gerçek media alınır, her yeni yazıda canlı çakışma kontrolü yapılır.
  Yerel byte kopyası uzaktan geri okuma yerine kullanılmaz.
- Önceki üretim kodu ve kapsamı değişmez. Üretim çift/gün/ay kayıtları eski
  bilimsel worker ve task kimliklerini korur; yeni dış controller kendi
  manifest kimliğini ayrıca kaydeder. Eski kayıtlar tam denetimle yeniden kullanılır.
- Kısmi/bozuk/kararsız deney uzun çalışmaya izin vermez. Yerel okuyucunun
  ürettiği hash bağlı `production_readiness.json` gerekir.

## Deney ne yapacak?

13–15 Ekim 2023'ün aynı üç tam günü, 28 çift:

| Sıra | Profil | Çift işçisi | Günlük işçisi |
| --- | --- | ---: | ---: |
| 1 | Eski yöntem, başlangıç baz ölçümü | 8 | 1, seri günlük evre |
| 2 | Yeni işlem hattı | 8 | 1 |
| 3 | Yeni işlem hattı, geniş havuz | 24 | 4 |
| 4 | Eski yöntem, tekrar baz ölçümü | 8 | 1, seri günlük evre |

Bu dört profil aynı yeni N2 üzerinde çalışır. Böylece yazılım farkı aynı
donanımda ölçülür; eski E2'nin 644,20 saniyesi ayrıca tarihsel kıyas olarak
gösterilir. Ağ/zaman etkisi nedeniyle bu tarihsel kıyas saf donanım kanıtı değildir.
Kaynak toplamı 20.559.071.684 bayt, ağ tekrarları hariç. Deney yeni ay eklemez.

Başlangıç dahil uygulama bütçesi en fazla 90 dakika; Google limiti 2 saat.
4 GiB kullanılabilir RAM/disk rezervi, 900 saniye çocuk süre sınırı, ana
süreç alarmı ve sonunda guest shutdown isteği var. Deney namespace'i 2 GiB
ile sınırlı. Google Stop ayrı son sınırdır; uygulama erken de bitebilir.
Kapatma/arşivleme hatasında da guest shutdown denenir. Sekmeden ayrılınca
detached süreç devam eder. Bu paket VM'yi kendiliğinden yeniden başlatmaz.

## 1 — VM kapalıyken düzenle

Compute Engine → VM instances → **wildfire-cpu-pilot → Edit**:

1. General purpose → **N2** → **n2-standard-32 (32 vCPU, 128 GB)**.
2. Provisioning model **Standard**.
3. Set a time limit → **By hours: 2**.
4. On VM termination **Stop**, Automatic restart **Off**.
5. Ubuntu 24.04 ve mevcut 30 GB disk aynı kalsın. Ek disk/snapshot ekleme.
6. Yeni maliyet tahminini oku ve **Save**.

N2/32 seçeneği görünmezse ekranı paylaş; ücretli Upgrade veya kota artırma
yoluna geçme. Ayarlar kaydedildikten sonra **Start → SSH**.

## 2 — Tek ZIP yükle ve doğrula

SSH → Upload File ile yalnızca şu dosya:

`C:\PROJELERIM\wildfire-risk-prediction\outputs\gcp_acceleration\wildfire_gcp_acceleration.zip`

Özel OAuth/bağlantı JSON'u mevcut VM'de kalır, yeniden yüklenmez veya paylaşılmaz.
ZIP 634.922 bayt, dokuz üye. SHA256:
`7a324d4046f03fe1a051f6dee38272ced7e6e29a02fe0b400fb445baaa8b0010`.

**VM SSH terminalinde** aşağıdaki bloğu bir kez çalıştır:

```bash
~/wildfire-gcp-work/.venv/bin/python - <<'PY'
from pathlib import Path
import hashlib, json, zipfile
p = Path.home() / 'wildfire_gcp_acceleration.zip'
expected = '7a324d4046f03fe1a051f6dee38272ced7e6e29a02fe0b400fb445baaa8b0010'
assert hashlib.sha256(p.read_bytes()).hexdigest() == expected, 'Paket SHA farkli'
dest = Path.home() / 'wildfire-gcp-acceleration-package'
assert not dest.exists(), 'Paket dizini mevcut; tekrar kurma'
names = {'run_gcp_acceleration.py', 'accelerated_production.py',
         'accelerated_pipeline.py', 'accelerated_checkpoint_store.py',
         'gcp_tuning_resources.py', 'reference_tuning.py', 'proof_plan.json',
         'month_manifest.zip', 'acceleration_manifest.json'}
with zipfile.ZipFile(p) as z:
    assert set(z.namelist()) == names and len(z.infolist()) == 9
    assert z.testzip() is None
    assert all(0 < i.file_size < 2_000_000 for i in z.infolist())
    spec = json.loads(z.read('acceleration_manifest.json'))
    assert set(spec['files']) == names - {'acceleration_manifest.json'}
    for n, checksum in spec['files'].items():
        assert hashlib.sha256(z.read(n)).hexdigest() == checksum
    dest.mkdir(mode=0o700)
    for n in names:
        (dest / n).write_bytes(z.read(n))
print('Hizlandirma paketi dogrulandi ve kuruldu')
PY
```

## 3 — Gerçek iki saatlik Google durma zamanını al

**Cloud Shell'de** (VM SSH'den ayrı panel) tek komut:

```bash
gcloud compute instances describe wildfire-cpu-pilot \
  --project=dogalafetonlemesistemi \
  --zone=europe-west3-c \
  --format='yaml(status,machineType,scheduling.maxRunDuration,scheduling.instanceTerminationAction,resourceStatus.scheduling.terminationTimestamp)'
```

`RUNNING`, makine tipi `n2-standard-32`, `seconds: '7200'`, `STOP` olmalı.
`terminationTimestamp` değerini tırnakları olmadan kopyala. Eski oturumun
saatini kullanma. Program actual CPU/RAM ve doğru VM kimliğini de kontrol eder.

## 4 — SSH'de karşılaştırmayı başlat

İlk satırı çalıştırıp yeni Google durma saatini gir. Ardından ikinci komutu
çalıştır. İki ayrı komut olarak yapıştırmak, `read` satırına komutun yanlışlıkla
giriş olmasını önler.

```bash
read -r -p "Google durma zamani: " termination
```

```bash
~/wildfire-gcp-work/.venv/bin/python \
  ~/wildfire-gcp-acceleration-package/run_gcp_acceleration.py \
  --mode proof --cpus 32 \
  --connection ~/.config/wildfire/drive_connection.json \
  --termination "$termination" --poweroff
```

Earthdata kullanıcı adı ve parola gizli girişle istenir; karakterlerin
görünmemesi normaldir. Bilgileri terminale gir, paylaşılan çıktılara ekleme.
`Detached acceleration launch requested` ardından ilk kontrol:

```bash
tail -n 20 ~/gcp_acceleration_launcher.log
```

`PROFILE START baseline_before workers 8`, ardından saved/verified ve
PROFILE COMPLETE beklenir. Sonra pipeline_eight, pipeline_scaled,
baseline_after. Başlangıç doğrulanınca sürekli izlemene veya sekmeyi açık
tutmana gerek yok. İsteğe bağlı 10–15 dakikada aynı komutla bakılabilir.
Hata/kısmi sonuç varsa yeniden başlatma; logdaki güvenli satırları paylaş.

## 5 — Sonucu indir, VM'yi kapalı tut

SSH → Download File:

`/home/enesnuhgocek1/gcp_acceleration_results.zip`

Yerel hedef:

`C:\PROJELERIM\wildfire-risk-prediction\outputs\gcp_acceleration\received\`

VM otomatik durmuşsa yalnızca dosyayı indirmek için kısa Start/SSH yap;
komutu yeniden çalıştırma. İndirdikten sonra Console **Stop** ve Stopped teyidi.
ZIP yoksa launcher logunu paylaş; test dizinini silme veya deneyi tekrarlama.

## Sonuç kabulü ve bütün ayların devamı

Yerel okuyucu 112 cold çift kaydı, 12 günlük ürün, SHA/CMR/native CSV ve
günlük bilimsel kontrolleri yapar. CPU/RAM/disk istatistiklerini CSV'den
yeniden hesaplar. İki baz sürenin oranı 0,8–1,25 içinde olmalı. Yeni profil
her iki bazdan en az %15 hızlıysa adaydır; adaylar %5 yakınsa daha az işçi
seçilir. Kısmi/kararsız/bozuk sonuçtan hazır-kaydı oluşturulmaz.
Bu eşikler pratik karar kuralıdır; istatistiksel güven aralığı değildir.

Kontrolleri Codex yerelde yapacak. Kabulden sonra `production_readiness.json`
ve hash'i elde edilecek; mevcut VM'ye bu **açık, secretsiz sonuç kaydı** yüklenecek.
O zaman sınır tekrar 8 saat/Stop yapılacak ve production modu başlatılacak.
Özel bağlantı JSON'u bu hazır-kaydından farklıdır; onu paylaşmayacağız.

Üretim kuyruğu bütün kalan eğitim aylarına tek başlangıçla sırayla gider;
her ay için manuel yeniden komut gerekmez. Her oturumun süre rezervinde
durur; sonraki oturumda eski doğrulanmış çift/gün/ay kayıtlarını kullanır.
Bitmemiş birkaç çocuk işi yeniden yapılabilir; doğrulanmış bütün dönem
baştan indirilmez. Büyük VM üzerinde restore/metadata/month kapanışları
da süre alır; ilk 8 saat bütün yılların tamamlanması garantisi değildir.

Şu anda üç tam ay (Temmuz/Ağustos/Eylül 2023), Ekim 1–14 ve 15 Ekim'in
10 çift kaydı mevcut. 69 tamamlanmamış ay / 17.768 ham çift işlemi kaldı.
Günlük gözlem `unknown`, negatif etiket izni `false` korunur.

Tam dönem çıktıları bağımsız doğrulanıp yerelde yedeklendiğinde VM, kalan
disk/snapshot/IP gibi ücret tüketebilen kaynaklar ve gerekli özel bağlantılar
envanterle temizlenecek. Stopped tek başına bütün kaynakların silinmesi değildir.
Bu hazırlıkta bulut başlatma/resize/Upgrade veya kaynak silme yapılmadı.
Uygulamanın trial güvenlik kesmesi 24 Ekim UTC'den önce; kalan iki gün temizlik payı.

## Yerel hazırlık kanıtı

Orijinal üretim ZIP SHA:
`a930d3438a6745d76bfb642d008d298d907ce0cf2fb89811cf9e2ff7d4252571`.
Yeni controller kapsamı:
`102c9e4ab16e4450d0d94eb3511dfdbf360fd6b6292809c5457efc93d2be5837`.
Yerel prova ham kaynak indirmeden gerçek native ürünleri yeniden kullandı;
gerçek ayrı günlük çocuk süreci, eski okuyucu ile yeni kayıtların geri
yükleneceği ve tamamlanmış günün çocuk işlem başlatmadan kullanılacağı denetlendi.
Toplam 26 ayrı kontrol geçti: son hedefli kümede 25 başarılı, daha önce
başarılı olan gerçek native/günlük pipeline testi tekrar çalıştırılmadı.
Eski Ağustos'un 31 günlük aylık arşivi ve bozuk nested marker reddi,
rehberdeki gerçek ZIP kurulum/overwrite reddi ve pinned üye kontrolü dahil.
Ruff kod/biçim ve paket CRC/üye SHA kontrolleri geçti.
Yerel prova zamanları VM hız ölçümü değildir. Sonradan alınan gerçek VM
sonuçları ayrı sonuç raporunda bağımsız doğrulandı.
