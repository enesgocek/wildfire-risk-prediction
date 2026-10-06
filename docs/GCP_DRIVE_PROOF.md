# Google Drive kalıcılık kontrolü — VM kapalıyken hazırlık

Bu paket mevcut doğrulanmış SNPP:2023197.0018 sonucunu kullanır. Yeni NASA
ham verisi indirmez, yeni üretim ayı veya yangın etiketi oluşturmaz. Paket
6,86 MB, Drive'a yazılacak ürün 3,98 MB; iş deposu sınırı 20 MB. Kayıttan
önce bilimsel denetim, Drive'dan geri indirilmiş byte'larla tekrar bilimsel
denetim, en son tamamlanma kaydı vardır. Tamamlanma öncesi yapay kesinti
ve farklı Python süreci/yeni dizinde geri yükleme birlikte sınanır.

VM'yi henüz başlatma. Önce aşağıdaki Windows/Console bağlantısını tamamla.
Mevcut Free Trial hesabı korunur; Upgrade yapılmaz, yeni VM/bucket/disk yok.
Google Drive API'nin standart kullanımı ek ücret gerektirmez; Google kota
üstü kullanım için değişiklik duyuruyor. Küçük kontrolün kapsamı bu sınırların
çok altında; API kota artışı veya ücretli yükseltme yapılmayacak.
[Google API kullanım koşulları](https://developers.google.com/workspace/drive/api/guides/limits).

## 1. Console ayarları — VM kapalı

Mevcut `dogalafetonlemesistemi` projesini seç:

1. **APIs & Services → Library → Google Drive API → Enable**.
2. **Google Auth platform → Branding → Get started**. Uygulama adı
   `Wildfire Drive Checkpoints`; destek ve iletişim e-postası kendi hesabın.
   Audience **External**. Yalnızca kişisel kullanımımız için kuruyoruz.
3. **Audience → Test users → Add users**: Drive'ı kullanacağın kendi Google
   e-postanı ekle. Testing durumunda kalsın.
4. **Data Access → Add or remove scopes**: yalnızca
   `https://www.googleapis.com/auth/drive.file` ekle ve kaydet.
5. **Clients → Create client → Desktop app** seç. Oluşturulan istemcinin
   JSON dosyasını bilgisayarına indir. Web application veya service-account
   anahtarı seçme. Dosyayı proje klasörüne koyma, içeriğini sohbetle paylaşma.

[Google izin ekranı rehberi](https://developers.google.com/workspace/guides/configure-oauth-consent),
[masaüstü OAuth akışı](https://developers.google.com/identity/protocols/oauth2/native-app).

## 2. Windows'ta bağlan — VM kapalı

Proje terminalinde:

```powershell
.\.venv\Scripts\python.exe scripts/cloud/connect_drive.py
```

İndirilen istemci JSON'unun tam dosya yolunu soracak. Yolu yaz; içerik
yapıştırma. Açılan Google tarayıcı sayfasında doğru Drive hesabını seç.
Sadece uygulamayla kullanılan dosyalar için izin ver. Tam Drive/Gmail veya
Cloud Platform erişimi istenirse bu akışla uyuşmaz; ilerleme.

Başarılı olursa yeni `wildfire-gcp-checkpoints-...` klasörü oluşur. Önceki
Colab klasörü değiştirilmez. Bağlantı bilgisi proje dışında,
`%LOCALAPPDATA%\wildfire-cloud-auth\drive_connection.json` konumuna kaydedilir.
Bu dosya yetkilendirme bilgisi içerir: sohbet/Git/Drive sonuç klasörüne
gönderilmez; yalnızca aşağıdaki özel VM aktarımında kullanılır.
`drive.file` kapsamı uygulamayla kullanılan dosyalara erişim içindir.
[Google kapsam açıklaması](https://developers.google.com/workspace/drive/api/guides/api-specific-auth).

Testing OAuth yenileme izni genellikle **7 gün** sonra sona erer; bütün
dönemi aylar boyunca tek izinle kesintisiz işler gibi varsaymıyoruz. Gerekirse
VM kapalıyken `connect_drive.py --renew` çalıştırılır; aynı kalıcı klasör
korunur ve yeni bağlantı VM'ye özel olarak yeniden aktarılır.
[Token ömrü](https://developers.google.com/identity/protocols/oauth2).

## 3. Bağlantı hazır olunca VM'de kısa kontrol

Önce Console'da **Free trial** durumunu ve mevcut **2 saat / Stop / Automatic
restart Off** ayarını doğrula. Değişiklik yok. Ardından Start ve SSH.
SSH **Upload file** ile ayrı ayrı yükle:

- `outputs/gcp_drive_proof/wildfire_gcp_drive_proof.zip`
- Windows'ta oluşan özel `drive_connection.json`

VM terminalinde özel bağlantının erişimini daralt:

```bash
mkdir -p -m 700 ~/.config/wildfire
chmod 600 ~/drive_connection.json
mv -n ~/drive_connection.json ~/.config/wildfire/drive_connection.json
```

Hedefte zaten bir bağlantı varsa üzerine yazma; yenileme aktarımında eski/yeni
dosya durumunu önce kontrol et. Paket açma komutu yalnızca sabit SHA ve düz
üye adları doğrulandıktan sonra dosyaları çıkarır:

```bash
python3 - <<'PY'
import hashlib, zipfile
from pathlib import Path
p = Path.home() / 'wildfire_gcp_drive_proof.zip'
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'bc7a24a33eb313ce96b7b40a53e504a6017f4c84bcc5930f149afea8d3744ba5'
dest = Path.home() / 'wildfire-gcp-drive-package'
assert not dest.exists(), 'Package directory already exists; verify existing package before reuse'
with zipfile.ZipFile(p) as z:
    names = z.namelist()
    assert len(names) == len(set(names)) == 7
    assert all(Path(n).name == n and '/' not in n and '\\' not in n for n in names)
    assert sum(i.file_size for i in z.infolist()) < 12_000_000
    assert z.testzip() is None
    z.extractall(dest)
print('Package verified')
PY
```

**Cloud Shell**'de şu salt okuma komutuyla Google'ın gerçek planlı durma
zamanını al. Burada Cloud Shell'i kullanmamızın nedeni VM service-account
scope'larını genişletmeden hesaplama kaydını okuyabilmek:

```bash
gcloud compute instances describe wildfire-cpu-pilot \
  --project=dogalafetonlemesistemi --zone=europe-west3-c \
  --format='value(resourceStatus.scheduling.terminationTimestamp)'
```

Boş çıktı gelirse zaman tahmin ederek başlatma. Bu alan VM Running iken
dolu olmalı. Çıkan RFC3339 zamanı aşağıdaki `GOOGLE_DURMA_ZAMANI` yerine
koy ve **VM SSH** terminalinde çalıştır:

```bash
~/wildfire-gcp-work/.venv/bin/python \
  ~/wildfire-gcp-drive-package/run_gcp_drive_proof.py \
  --connection ~/.config/wildfire/drive_connection.json \
  --termination 'GOOGLE_DURMA_ZAMANI'
```

Paket yeni pip kurulumu yapmaz. Ayrılmış supervisor ve çocuk süreç grubu
SSH oturumundan bağımsız çalışmak üzere kurulur. İş en fazla **20 dakika**
çalışır; Google durma zamanından ayrıca 5 dakika önce kesilir. 15 dakikadan
az VM zamanı kalmışsa başlamaz. Bu davranışın gerçek VM/SSH bağlantı kopması
deneyi henüz yapılmadı; ilk gerçek çalışmanın kontrol konularından biridir.

```bash
tail -n 20 ~/wildfire-gcp-drive-proof/launcher.log
```

`Passed` sonrası SSH **Download file** ile
`/home/enesnuhgocek1/wildfire-gcp-drive-proof/drive_proof_summary.json`
dosyasını indir, yerelde `outputs/gcp_drive_proof/received/` klasörüne koy ve
VM'ye **Stop** uygula. Başarısızsa çalışma dizinini/Drive dosyalarını silme.
İş VM ayarlarını değiştirmez veya kendiliğinden yeniden başlatmaz.

## Kanıtın sınırı ve sonraki iş

Son paket SHA/CRC ve gerçek ürünle ayrı süreç provasından geçti. Tam test
kümesi 442 başarılı; Ruff kod ve 141 Python dosyasının biçimi başarılı.

Yerelde gerçek ürünle yapay kesinti ve iki ayrı süreçte geri yükleme geçti;
bu henüz Drive'a yazma kanıtı değildir. Dönen JSON'un kimlik/scope/checksum
kontrolü `scripts/cloud/verify_gcp_drive_proof.py` ile yapılır. JSON denetimi
tek başına uzaktaki payload'ı bağımsız yeniden indirmiş sayılmaz.

Drive aynı isimli birden çok dosyaya izin verir. Adapter bu durumu, bozuk
metadata/eksik byte'ları ve listeleme hatalarını reddeder. Tek VM/tek yazıcı
kuralı vardır; dağıtılmış kilit iddiası yok. Mevcut tamamlanmış ürünlerin
üzerine yazma/silme/sync yok. API hataları sınırlı denemeden sonra işi durdurur.

Uzun ay kuyruğu ve günlük geometrik birleşimin GCP sarmalayıcısı henüz
tamamlanmış sayılmıyor. Bu kapı geçince 26 çiftlik 1–3 Ağustos denemesiyle
tam iş süresi/kayıt hacmi ölçülecek; sonra 6/8 saat ve daha büyük gruplar
konusunda somut sonuçlarla karar verilecek. Negatif etiket izni false kalır.
