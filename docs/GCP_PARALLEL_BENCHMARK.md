# GCP: bir ve iki işçi karşılaştırması

İlk GCP tek geçiş sonucu bağımsız yerel kontrolden geçti: iki kaynak SHA'sı,
tam QA raporu ve 2.899 hücrenin bütün sütunları referansla aynı. Kaynak
194.702.968 bayt; 134,84 saniye son çalıştırmanın ortam kontrolü/kurulumu
dahil süresi, 21,65 saniye doğal işleyici süresidir. Önceki Ctrl+C denemeleri,
VM boş bekleme süresi ve faturalama toplamı bu süreye dahil değil.
Rapor: `outputs/reports/observation_coverage/gcp_pilot_received_verification.json`.

## Yeni denemenin kapsamı

- Önceden tamamlanan 16 Temmuz 2023 günü, aynı altı kaynak çifti.
- Önce bir, ardından iki ayrı işlem. Yeni üretim ayı veya günlük etiket yok.
- Her kolda kaynaklar yeniden indirilir: toplam nominal 2.194.808.406 bayt,
  yaklaşık 2,19 GB yalnızca VM'ye. Yeniden deneme/protokol trafiğinin sert
  toplam sınırı değildir. Yerel ham indirme yok.
- Kaynak SHA'ları ve dört doğal CSV her geçişte eski Colab sonucuyla tam
  eşleşmelidir. Değişmeyen alan/tarama kodunun bütünlük kontrolleri de çalışır.
- Her işçinin ayrı paket/dizin/çıktısı vardır. Ortak değişkenler veya geçici
  kaynak yolu paylaşılmaz; kütüphane iş parçacıkları iki kolda da bir.
- İşçi evrelerinin ortak 35 dakika son tarihi ve her çocuğun en çok 15 dakika
  sınırı var. İstemlerde bekleme ve son birleştirme buna dahil değildir.
  VM'nin mevcut iki saat/Stop ayarı değişmez. Boot yaşı 70 dakikayı aşmışsa
  başlamaz; boot yaşı Google'ın kesin kapanma zamanı değildir.
- SHA bağlı checkpoint geri okunmadan geçici ham çift silinmez. Sonuçlar
  VM boot diskindedir; Drive/GCS veya VM dışı kalıcı kayıt sayılmaz.
  Hata/kesintide çalışma dizini korunur; hız ölçümü için dolu dizin tekrar
  kullanılmaz, otomatik VM yeniden başlatma yok.

Paket: `outputs/gcp_benchmark/wildfire_gcp_benchmark.zip`, 2.944.243 bayt.
SHA256: `61ef861ffe461e60de45856b43cb1111d5ed80f5f9b8ac2f6aeb4bf98af783bb`.
Eski `l2_summer_B_bundle.zip` ve bütün bilimsel kodu değiştirilmedi.

## Çalıştırma

Yalnızca mevcut Free trial / kredi sınırı içinde, aynı VM'de. Upgrade,
yeni VM/disk, GPU, kapsam genişletme veya süre uzatma komutu içermez.
Yeni ZIP tarayıcı SSH upload simgesiyle kullanıcı ana dizinine yüklenir.
[SSH dosya aktarımı](https://docs.cloud.google.com/compute/docs/instances/transfer-files).

```bash
python3 - <<'PY'
import hashlib, zipfile
from pathlib import Path
p = Path.home() / 'wildfire_gcp_benchmark.zip'
assert hashlib.sha256(p.read_bytes()).hexdigest() == '61ef861ffe461e60de45856b43cb1111d5ed80f5f9b8ac2f6aeb4bf98af783bb', 'Paket SHA farki'
dest = Path.home() / 'wildfire-gcp-benchmark-package'
dest.mkdir(exist_ok=True)
assert not dest.is_symlink()
with zipfile.ZipFile(p) as z:
    expected = {'summer.zip', 'requirements.txt', 'run_gcp_benchmark.py', 'benchmark_manifest.json'}
    assert len(z.namelist()) == 4 and set(z.namelist()) == expected
    assert z.testzip() is None
    assert all((dest / n).resolve().is_relative_to(dest.resolve()) for n in z.namelist())
    z.extractall(dest)
print('Benchmark paketi dogrulandi')
PY
```

Başarı mesajından sonra önceki doğrulanmış venv kullanılır:

```bash
~/wildfire-gcp-work/.venv/bin/python ~/wildfire-gcp-benchmark-package/run_gcp_benchmark.py
```

Kullanıcı adı/parola gizli giriş; karakterler görünmez. Ctrl+C iptal eder.
Alt süreçler kaydedilmeyen kimlik ortamını alır; ebeveyn kopyası finally ile
temizlenir. Yeniden pip kurulumu/upgrade yapılmaz; kilit sürümler ve pip check
doğrulanır. İlerleme her biten çift için yazılır. Hata halinde aynı komut
körlemesine tekrarlanmaz; `workers_*/l2_sample_*/run.log` ve korunan çalışma
dizini incelenir. SSH kopmasının işi sürdüreceği garanti edilmez.

Başarı: `gcp_two_arm_benchmark_completed`. Sonuç ZIP'i terminaldeki tam yoldan
indirilip yerelde `outputs/gcp_benchmark/received/` altına konur. ZIP, özet
JSON ve iki altı-geçişli sonuç ZIP'i içerir. Yerel kopya görüldükten sonra VM
Stop uygulanır; disk Stop ile silinmez. Sonuç doğrulanmadan VM/disk silinmez.

## Sınırlar ve yerel kanıt

Hız oranı bir kez, sabit bir-işçi/iki-işçi sırasıyla ölçülür. Sunucu, ağ ve
uzak önbellek etkileri ayrıştırılmaz; bütün yıllara doğrusal hız/bütçe
garantisi değildir. İşçi duvar süresi başlatma, indirme, denetim, geri okuma
ve temizliği içerir; birleştirme süreye dahil değildir. Bellek çocuk işlem
tepe RSS'idir, aynı anda VM toplamı değildir. Disk tepe örneklemesi kapalı;
eski uyumluluk alanındaki sıfır ölçüm değil, disk_sampling_enabled=false
ile işaretli yer tutucudur. Gözlem unknown ve negatif izin false kalır.

10 yeni test işçi sınırı/eksiksizlik, hata, eski paket SHA, bütün kod/metadata
geri okuması, sır/ortam ayrımı ve kayıt sonrası temizlik sırasını sınar.
Son test Colab ürünlerini yerelde yeniden okur; ham işleme veya Linux hız
testi değildir. Tam küme 366 test geçti; Ruff kod ve 125 Python dosyasının
biçimi başarılı. Yeni GCP paralel işi henüz çalıştırılmadı.

## Gerçek sonuç ve bağımsız denetim — 6 Ekim

Kullanıcı işi tamamlayıp 42.022.268 bayt ZIP'i received dizinine aldı ve VM'yi
Stop yaptığını bildirdi. Uzak VM durumunu veya faturayı API ile okumadık;
disk silinmiş sayılmaz. Sonuç ZIP SHA256:
`8658f6af2ebd05f69c13626e57738bb373a7fdb1c821e08a1ffb89e2573c97b5`.

| Kol | Soğuk işçi duvar süresi | Tamamlanan çift | Başarılı kaynak payload'ı |
|---|---:|---:|---:|
| 1 işçi | 432,3892 saniye | 6 | 1.097.404.203 bayt |
| 2 işçi | 229,2940 saniye | 6 | 1.097.404.203 bayt |

Oran yeniden hesaplandı: **1,88574 kat**, süre azalması **%46,97046**.
En yüksek tek çocuk RSS değeri sırasıyla 740.990.976 / 738.791.424 bayt;
eşzamanlı toplam VM RAM'i değil. Her iki kolda altı kaynak tekrar işlendi,
cache/checkpoint sonucu yeniden kullanılmadı. İki kola ait dosya SHA/byte
sayısı, CRC, manifest/worker/metadata kimliği, bütün checkpoint'ler ve pinli
paketler mevcut yerel bilimsel doğrulayıcıyla geçti. Gelen ZIP kodu çalıştırılmadı.

Her kolun altı tam QA raporu, kaynak SHA'ları, sayım ve üç tarama CSV'si
önceki Colab sonucuyla tam eşleşti. Kol başına 17.394 alan tablosu satırı ve
üç geometri grubundaki 52.182 kaydedilmiş geometri karşılaştırıldı. **İki GCP
kolu arasında bütün alan sütunları ve normalize edilmiş geometri koordinatları
tam eşit**, tolerans sıfır. Dolayısıyla bu denemede paralelleştirme bu ürünleri
değiştirmedi. GPKG dosyasının tamamının byte eşitliği iddia edilmiyor.

İlk Colab karşılaştırmasında alan/geometriyi bit düzeyinde eşit saymak doğru
olmadı. Son basamak farkları ayrıca ölçüldü:

- En büyük alan sütunu farkı 3,7124846e-7 m².
- En büyük oran sütunu farkı 5,2036153e-13.
- En büyük sınır Hausdorff uzaklığı 1,3170890e-9 EPSG:6933 koordinat metresi.
- En büyük simetrik alan farkı 3,9561682e-7 m².
- Bazı poligonlarda koordinat sayısı da farklı; yalnızca vertex sırasına
  dayalı structural equality yeterli olmadı. Sınır uzaklığı ve simetrik alan
  birlikte denetlendi. Bulut geometri grubunda bu fark görülmedi.

Colab alan sütunları için mutlak 1e-4 m², oranlar için 1e-12; geometri
sınırları için 1e-8 koordinat metresi ve simetrik alan için 1e-4 m² kapısı
uygulandı. Alan/oran sınırları mevcut bilimsel geri okumadaki mutlak hassasiyet
düzeylerini kullanır; göreli tolerans eklenmedi. Kimlik, kaynak/sayım/saat/etiket
alanları esnetilmedi. Farklar sayısal hassasiyet düzeyindedir; tam olarak hangi
ortam/CPU aşamasından kaynaklandığı ayrıştırılmadı. Bunlar fiziksel ayak izi
doğruluğu veya gerçek dünya konum hatası ölçümü değildir. İki GCP kolunun
karşılaştırmasında bu toleransların hiçbiri kullanılmadı.

Yeni doğrulayıcı: `scripts/cloud/verify_gcp_benchmark_results.py`.
Rapor: `outputs/reports/observation_coverage/gcp_benchmark_received_verification.json`,
durum `independent_gcp_two_arm_readback_passed`. Her sayısal fark raporda tutulur.
Eski Colab doğrulama raporları korunur. 20 yeni koruyucu test; tam küme **386
başarılı**, Ruff kod/128 Python dosyası biçimi geçti. Bozuk özet/hash, sıcak
kaynak, yanlış etiket, anlamlı alan/oran farkı ve aynı alanı koruyan kaymış
geometri reddediliyor; eş sınırdaki ek vertex tam eşitlik diye sunulmuyor.

Sırada kesintiden devam eden üretim kuyruğu ve VM dışı kalıcı küçük çıktı
kaydının hazırlanması var. Dört işçi, bütün aylar veya krediye sığacak toplam
zaman/fiyat bu sonuçla doğrulanmış sayılmadı. VM yeniden başlatılmadı;
mevcut boot disk korunuyor. Günlük gözlem unknown, negatif izin false.
