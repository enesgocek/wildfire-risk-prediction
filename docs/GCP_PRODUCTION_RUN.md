# Tam eğitim dönemi: GCP çalıştırma rehberi — 6 Ekim 2026

> Dönemsel uygulama kaydı. Kurulum, maliyet ve bekleyen iş ifadeleri belgenin
> ilgili çalışma aşamasına aittir. Güncel durum [STATUS.md](STATUS.md), mevcut
> üretim yolu [devam rehberinde](GCP_SOURCE_AWARE_CONTINUATION_2026-10-09.md) izlenir.

Bütün eğitim aylarıyla devam etmeyi seçtim. Örnek gün seçimi ana plan
değil. Temmuz 2023 hazır; kalan **71 ay / 18.441 nominal çift** tek kuyruğa
kondu. İlk ay Ağustos 2023. Bir çalışma dilimi bitince aynı paket tamamlanmış
kayıtları Drive'dan doğrulayarak devam eder. Her gün veya ay için ayrı komut yok.

## 1. VM kapalıyken süreyi düzenle

Compute Engine → VM instances → `wildfire-cpu-pilot` → Edit.
VM çalışma süresi / time limit ayarını **8 saat**, süre sonundaki eylemi
**Stop**, automatic restart seçeneğini **Off** yap ve Save ile kaydet.
Mevcut e2-standard-8, europe-west3-c, Ubuntu 24.04, 30 GB disk ve no backups
ayarları korunur. Bu adım yeni VM oluşturmaz.

İlk uzun çalışma 8 saatliktir; bütün dönem 8 saatte bitecek demek değildir.
Paket sonraki çalışmalar için 24 saate kadar mutlak son zamanı kabul eder;
Google tarafındaki sınır ayrıca manuel olarak seçilir. Otomatik Start yok.

8 saat ilk üretim çalışmasının üst sınırıdır; toplam işin bitiş tahmini değildir.
Amaç ilk uzun çalışmada gerçek günlük hız, dört işçi ve Drive kayıt yükünü
ölçmek, beklenmeyen hatada VM'nin açık kalmasını sınırlamaktır. Tamamlanmış
kayıtlar her yeni çalışmada geri okunarak doğrulanır ve atlanır. Bu kontrolün
ve yeniden başlatmanın ek süre/aktarım maliyeti vardır; üretimde büyüklüğü
henüz ölçülmedi, sıfır tekrar maliyeti iddiası yoktur. Ani kesintide yalnızca henüz kalıcı tamamlanma kaydı
doğrulanmamış işler yeniden gerekebilir. İlk ölçüm uygunsa sonraki çalışmada
aynı paketle 24 saate kadar daha uzun süre seçilebilir; 8 saat/gün zorunluluğu yok.

6 Ekim hesap durumu bildirimi: **Free Trial, TRY13,623 kredi**. Canlı Billing
ekranına araçla erişilemedi. Upgrade/Activate paid account uygulanmaz.
Google, Free Trial sırasında ücret alınmadığını; yükseltme yapılmadan süre/kredi
bittiğinde kaynakların duracağını belirtir. Disk gibi saklanan kaynaklar,
VM durduktan sonra da deneme kredisinden tüketebilir; Stop bütün kaynakları silmez.
[Free Trial](https://docs.cloud.google.com/free/docs/free-cloud-features),
[VM Stop](https://docs.cloud.google.com/compute/docs/instances/stop-start-instance).

## 2. Start → SSH → yalnızca üretim ZIP'ini yükle

Hazır paket: `outputs/gcp_production/wildfire_gcp_production.zip`.
SSH penceresinde Upload File ile ana dizinine yükle. Önceki özel bağlantı
`~/.config/wildfire/drive_connection.json` zaten VM'dedir. Yeni OAuth client
JSON'u, parolayı veya token'ı sohbetle paylaşma. Python ortamını yeniden kurmak yok.

SSH terminalinde aşağıdaki bloğu tek sefer çalıştır. Paket hash'i ve bütün
dosyalar doğrulanmadan hiçbir paket kodu çalıştırılmaz. Var olan farklı paket
dosyalarının üstüne yazılmaz.

```bash
python3 - <<'PY'
from pathlib import Path
import hashlib, json, zipfile
source = Path.home() / 'wildfire_gcp_production.zip'
expected = 'a930d3438a6745d76bfb642d008d298d907ce0cf2fb89811cf9e2ff7d4252571'
assert hashlib.sha256(source.read_bytes()).hexdigest() == expected, 'ZIP SHA differs'
destination = Path.home() / 'wildfire-gcp-production-package'
assert not destination.is_symlink(), 'Package directory symlink'
with zipfile.ZipFile(source) as z:
    names = z.namelist()
    assert len(names) == 12 and len(set(names)) == 12
    assert all(Path(n).name == n and '/' not in n and '\\' not in n for n in names)
    assert z.testzip() is None, 'ZIP CRC'
    manifest = json.loads(z.read('production_manifest.json'))
    assert set(names) == set(manifest['files']) | {'production_manifest.json'}
    for name, checksum in manifest['files'].items():
        assert hashlib.sha256(z.read(name)).hexdigest() == checksum, 'Member SHA differs'
    destination.mkdir(mode=0o700, exist_ok=True)
    for name in names:
        target = destination / name
        assert not target.is_symlink(), 'Package file symlink'
        data = z.read(name)
        if target.exists():
            assert target.read_bytes() == data, 'Existing package differs; do not overwrite'
        else:
            target.write_bytes(data)
        target.chmod(0o600)
print('Production package verified')
PY
```

## 3. Yeni durma zamanını al

VM'yi **bu kez Start yaptıktan sonra**, Cloud Shell'de şu salt okuma komutunu çalıştır:

```bash
gcloud compute instances describe wildfire-cpu-pilot \
  --project=dogalafetonlemesistemi \
  --zone=europe-west3-c \
  --format='value(resourceStatus.scheduling.terminationTimestamp)'
```

Çıkan `...T...Z` zamanını kopyala. Eski `2026-10-06T13:42:05.734350Z`
zamanını kullanma. Alan boşsa üretimi başlatma: Google süre sınırı henüz
doğrulanmamıştır. Duration her Start için yeniden hesaplanır.
[Google süre sınırı](https://docs.cloud.google.com/compute/docs/instances/limit-vm-runtime).

## 4. SSH'de kuyruğu başlat

```bash
read -r -p "Yeni Google durma zamanı: " termination
~/wildfire-gcp-work/.venv/bin/python \
  ~/wildfire-gcp-production-package/run_gcp_production.py \
  --connection ~/.config/wildfire/drive_connection.json \
  --termination "$termination" \
  --poweroff
```

İstenen yeni Google zamanını yapıştırıp Enter'a bas. Earthdata kullanıcı adı
ve parolası **yazarken görünmez**; yazıp Enter'a bas. Bilgiler komut argümanına,
dosyaya veya günlüğe yazılmaz. Sadece süreç belleğinde kullanılır.

`Detached production launch requested` sürecin istendiğini gösterir;
bilimsel işin başarılı olduğunu tek başına kanıtlamaz. Ardından:

```bash
tail -n 20 ~/wildfire-gcp-production-v1/launcher.log
```

`Pair saved/verified` kaydedilen çifti; `DAY COMMITTED` bütün beklenen nominal
çiftleri doğrulanmış günü; `MONTH NOMINAL DIAGNOSTICS COMPLETE` ayı gösterir.
Başlangıçta önce kaynak metadata hazırlanır. Aynı başlatma komutunu iş sürerken
tekrar çalıştırma. İlk `DAY COMMITTED` çıktısını kontrol için paylaşabilirsin.

## Sekmeyi kapatma ve takip

İlk `Pair saved/verified` çıktısını ve yeni çalışmanın durumunu kontrol ettikten
sonra SSH sekmesi kapatılabilir; bilgisayarın kapanması da VM işini durdurmaz.
Başlatıcı ve supervisor `start_new_session=True`, `stdin=DEVNULL` ve dosya
günlükleriyle terminalden ayrılır. Colab'ın kullanıcı etkinliği davranışı
buraya uygulanmaz. Tarayıcıdan ayrılma ile gerçek Google Stop/Start deneyi
aynı şey değildir; üretim oturumu henüz canlı yürütülmedi.

Durumu tekrar SSH açarak salt okumayla görebilirsin:

```bash
cat ~/wildfire-gcp-production-v1/progress.json
tail -n 20 ~/wildfire-gcp-production-v1/launcher.log
tail -n 10 ~/wildfire-gcp-production-v1/supervisor.log
```

`progress.json` içindeki `actual_vm_termination_timestamp` bu Start'tan
alınan yeni zamanla aynı olmalıdır. Önceki log satırı yeni başlatmayı kanıtlamaz.
`paused_at_runtime_reserve` kalan kuyruk bulunduğu anlamına gelir.
`invocation_finished_no_automatic_restart` tek başına bütün ayların tamamlandığını
kanıtlamaz; uzak aylık kayıtlar ayrıca doğrulanır.

Sürekli ekran başında olmak gerekmez. Mevcut paket bildirim/e-posta göndermez;
ilk kayıt kontrolü ve çalışma dilimi sonrasında Console'da **Stopped** kontrolü
gerekir. Kuyruk bittiğinde veya normal hata çıkışında `--poweroff` guest shutdown
ister. Başlatma öncesi hata ya da supervisor arızasında Google süre sınırı
bağımsız Stop korumasıdır; hata görülürse beklemek yerine manuel Stop uygulanır.
Sonuçların daha sonra kontrol edilmesi tamamlanmış Drive kayıtlarına bir oturum zaman aşımı
uygulamaz. OAuth Testing token'ının yenilenmesi gerekmesi sonuçların silinmesi
değildir; deneme bitişinden önce VM'deki gerekli raporlar dışarı alınır.

## Çalışma ve devam etme davranışı

- İlk doğrulanmış tam güne kadar 2 işçi, ardından 4 ayrı Python süreci.
  Dört işçinin ham veri hızlanması henüz VM'de ölçülmedi.
- Her kaynakta ürün, sürüm, zaman, dosya boyutu ve mevcut CMR checksum denetlenir.
  Donmuş bilimsel kod, AOI, grid ve metadata hash'leri korunur.
- Çift → tam gün geometrik birleşimi → aylık küçük arşiv sırası uygulanır.
  Sonuç Drive'a yazılır, yeni dizinde geri okunur, bilimsel kontrolden geçer;
  tamamlanma işareti en son yazılır. Yarım sonuç yeniden kullanılamaz.
- Ham dosyalar aynı anda sadece küçük bir gruptur. Kalıcı kayıt doğrulanınca
  VM scratch dosyaları temizlenir. 3,39 TB toplam kaynak akışı arşiv olarak
  bilgisayara veya Drive'a indirilmez.
- Google son zamanından 15 dakika önce işçi için son sınır; yeni görev için
  ayrıca 15 dakika çalışma ve 15 dakika kaydetme rezervi aranır. Bu nedenle
  çalışma dilimi 8 saatin biraz öncesinde bitebilir. Guest shutdown istenir;
  Google'ın bağımsız Stop sınırı ikinci korumadır. Hata da işi sonlandırır.
- Kayıtlar 200 GB uygulama depo sınırıyla tutulur. Bu **para/fatura sınırı değil**.
  Tek VM / tek yazıcı desteklenir; çok VM'li cluster aynı kuyrukta desteklenmez.
- Kesinti veya Stop sonrasında aynı ZIP, aynı Drive klasörü ve yeni Google
  durma zamanı kullanılır. Tamamlanmış ay/gün/çift tekrar doğrulanır ve atlanır.
  Yanlış uzunluktaki yarım ham dosya tekrar indirilir; bozuk tamamlanmış kayıt
  sessizce değiştirilmez, iş durur.
- `--poweroff` iş sonunda guest shutdown ister. Console'da **Stopped** durumunu
  yine kontrol et. İş başlamadan doğrulama hatası olursa VM'yi manuel Stop yap.

Google OAuth uygulaması External / Testing durumundaysa Drive refresh token'ı
7 gün sonra sona erebilir. Bu durumda iş hata ile durur; tamamlanmış kayıtlar
silinmez. VM kapalıyken bağlantı, **aynı Drive klasörü korunarak** yenilenir;
özel bağlantı dosyası VM'ye güvenli şekilde aktarılır. Yeni klasöre geçmek
tamamlanmış kayıtları otomatik taşımış sayılmaz.
[Google token ömrü](https://developers.google.com/identity/protocols/oauth2).

283 eşleşmemiş katalog kaydı korunur. Günlük durum hâlâ `unknown`, negatif
etiket izni `false`: nominal ayın bitmesi nihai yangın etiketlerinin hazır
olması değildir. 2024 doğrulama ve kapalı 2025 final dönemine bu kuyruk erişmez.
Bitki örtüsü, arazi, olay/etiket kuralları ve eğitim tablosu sonraki aşamalardır.

## Kontrol kanıtı

İş sona erince VM yalnızca Stop durumunda bırakılmaz. Sonuçlar bağımsız
kopyayla doğrulandıktan sonra VM/disk ve diğer oluşturulmuş kaynaklar kaldırılır,
proje billing bağlantısı devre dışı bırakılır ve ilgili Cloud Billing hesabı
kapatılır. [Sıralı son temizlik ve kabul ölçütleri](GCP_FINAL_CLEANUP.md).
Bu işlem bugün yapılmış değildir; üretim ve sonuç doğrulaması sonrasında uygulanır.

Son paket raporu: `outputs/gcp_production/package_report.json`.
Gerçek eski altı ürünle kesinti/geri yükleme ve günlük geometri provasının
raporu: `outputs/gcp_production_rehearsal/report.json`. Eski arşivler değişmez.
Bu yerel prova yeni NASA indirmesi veya gerçek VM Stop/Start deneyi değildir.
Gerçek Drive V2 küçük ürün provasının daha önce alınmış sonucu ayrıca korunur.

Son paketle **512 test**, Ruff kod/156 Python dosyası biçim kontrolü geçti.
Altı gerçek ürün, 20 çift bilimsel geri okuması, 4 günlük geri okuma ve altı
ayrı süreçte restore geçti. Sayım/zaman/kimlik tabloları sıralı karşılaştırmada
birebir eş; alanlarda en büyük mutlak fark 0,0000102241 m², 0,0001 m² mutlak
ve 1e-10 göreli tolerans içinde. Oranlardaki en büyük fark 1,51e-11.
Karşılaştırma toleransı üretim bilimsel kodunu değiştirmedi. Kesilmiş
completion ve eksik çift seti kabul edilmedi. Son proof manifest SHA'sı
`0c5302cadf0c05dce36843254300cd8719346ddac4648c78c5c20a7dfd8f7394`.
Rehberdeki kurulum bloğu temiz kurulum/aynı paket/farklı dosyayı reddetme
kontrolünü geçti. Yeni VM üretimi henüz başlamadı.
