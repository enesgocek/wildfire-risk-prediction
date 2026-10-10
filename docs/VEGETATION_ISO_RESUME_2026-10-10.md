# Bitki örtüsü zaman çözümlemesi ve devam — 10 Ekim 2026

## Gerçek duruşun teşhisi

İlk 24 saatlik yerel çağrı `training_2018_2023_20261010_26d6769c`,
14 eğitim ayını (Ocak 2018–Şubat 2019) kabul ettikten sonra Mart 2019
hazırlığında durdu. Üst raporun son kaydı 10 Ekim 03:14:45,502942 UTC;
alt kuyruk RuntimeError, aylık çocuk ValueError sınıfı bildirdi.
Serbest hata/kimlik bilgisi çıktısı paylaşılmadı. VPN/kota açıklaması yapılmadı.

Ağ kullanmadan özgün `verify_vegetation_full_grid.verify` çalıştırıldı.
1, 8 ve 15 Mart kesimleri geçti; **22 Mart 2019** kesiminde ham
`scene_acquisition_utc` listesini okuyan Pandas çağrısı hata verdi.
92 grubun 20'sinde tam saniye ile kesirli saniye biçimleri karışıyor.
Örnek ilk grupta altı zamanın beşi kesirli, biri tam saniye. Açık ISO
çözümleme, 92 grubun toplam 868 zamanını tek tek `Timestamp` dönüşümüyle
nanosaniye biriminde eşleştirdi. Birleştirilmiş kesim tablosundaki
`source_acquisition_latest_utc` alanı da varsayılan toplu parser'da hata verdi.

Bu, mevcut dosyalarla yeniden üretilmiş bir **tarih çözümleme hatasıdır**.
Ham verinin bozulduğu, EE kotasının tükendiği veya kullanıcı bağlantısının
kesildiği anlamına gelmez. 29 Mart kesimi henüz indirilmemiş; ayın günlük
tablosu/manifesti bulunmuyor. İlk dört kesim korunmuştur.

## Düzeltmenin kapsamı ve kanıtı

Yeni `vegetation_iso_adapter.py`, dondurulmuş fonksiyonların yalnız kendi
Pandas isim alanlarına proxy bağlar. Global Pandas ve özgün kaynak dosyaları
değişmez. UTC ISO dizgilerinde tam/kesirli saniye açık `ISO8601` biçimiyle,
`errors=raise` ve nanosaniye birimiyle okunur. UTC olmayan, belirsiz,
geçersiz veya dokuz basamaktan hassas dizgiler reddedilir. Eksik değerler
korunur. Milisaniye birimli sayısal Landsat dönüşümü ve gerçek datetime
nesneleri özgün çağrıya bırakılır. Takvim, geçmiş pencere, QA, alan,
integral, hücre sayısı ve görüntü yaşı kontrolleri korunur.

Dinamik tam-grid verifier importu da yalnız ilgili aylık modülün isim
alanında sarılır. Proxy'ler hata veya bitişte geri yüklenir. Yeni kesim/ay
manifestlerine `datetime_parser_adapter` kimliği eklenir; eski manifestler
yeniden yazılmaz. Yeni bağımsız aylık raporlar parser kimliği ve çağrı
sayımını taşır. Eski helper/builder hash'i dondurulmuş dosya kimliğidir;
yürütmenin adaptersız olduğu iddiası değildir.

Gerçek kabul dosyası:
`outputs/reports/landscape/iso_adapter_v1/proof_2019_03_22.json`.
SHA-256 `0e62593189533ad6223035e1260cd40306c23d860d667fd228adc8e57970b397`.
Adapter SHA-256 `147199244790ae41b2465c9c60ad8a68c8ac44417a2439c340f6b217be1f44be`.
Özgün hata yeniden üretildi; adapter altında aynı 5.798 satır bütün
integral/alan/zaman kontrollerinden geçti. 94 girdi (manifest, tablo ve
92 ham grup) değişmedi; parser isim alanı geri yüklendi. İndirme sıfır.

12 yeni kontrol dahil **105 ilgili test geçti**; Ruff/biçim denetimleri
geçti. Son format düzenlemesinden sonra 12 yeni kontrol tekrar geçti.
Gerçek eski Ağustos 2018 ayının 179.738 satırı ağ engellenerek yeni child
entrypoint'inde kabul edildi; eski ürünler değişmedi. Ayrıca Mart 2019'un
dört hazır kesimi aynı entrypoint'te ağ engellenerek yeniden kullanıldı;
eksik beşinci kesimde beklenen çevrimdışı duruş gerçekleşti.

## Yeni sınırlı devam çağrısı

`run_vegetation_training_v2.py`, özgün üst/alt kuyrukların iş kilitlerini,
24 saat toplam/dört saat alt çağrı sınırlarını, 10 GiB disk rezervini,
tek ay/iki EE isteğini ve hata halinde duruşunu korur. Yalnız bilinen iki
çocuk komutu adapter entrypoint'ine yönlendirilir; uyarı seçeneği, log,
timeout ve hata işleme özgün kuyrukta kalır. Başlangıç, proof SHA'sını,
11 özgün kaynak pinini ve 94 gerçek girdi SHA'sını doğrular. Yeni iki
dosyanın hash'leri her kabul öncesi fingerprint'e eklenir. Yeni runtime
kaydında proof/adapter/V2 kimliği açık tutulur.

Devamdan önce yetkili salt okunur süreç sorgusunda eski iş/çocuklar yoktu;
iki iş kilidi bırakılmıştı. Kilit veya eski veri silinmedi. Eski 14 aya ve
Mart'ın korunan kesimine ait 136 dosya hash'i baseline'a alındı.

Yeni iş `training_iso_v2_2018_2023_20261010_50d439a4`:

- Başlatma 10 Ekim 11:45:01,352716 UTC (14:45:01 Türkiye).
- Üst rapor başlangıcı 11:45:06,607083 UTC; PID 22892 `running`.
- Yetkili süreç sorgusu üst süreç ve readback çocuklarının canlılığını doğruladı.
- İlk evre Ocak 2018 yeniden okuması; yeni veri indirmesi başlamış sayılmadı.
- Sonraki yerel kontrolde eski 14 ay yeniden doğrulandı; Mart 2019'un eksik
  kesiminin hazırlanmasına geçildi. Üst durum `running`; Mart henüz tam ay kabulü değildir.
- 136 baseline dosyası başlangıç sonrasında da aynı hash'te.
- 24 saat sınırı 11 Ekim yaklaşık 14:45 Türkiye; bütün 72 ayın bitiş garantisi değil.

Progress:
`outputs/reports/landscape/training_supervisor_v1/training_iso_v2_2018_2023_20261010_50d439a4/progress.json`.
V2 SHA `64f1447e171149b3209c42b4dfe92d56671dd2cdc2149f13033ee7fc6789d47e`.
Başlangıç ve baseline kayıtları aynı iş dizinindedir. Eski 14 ay önce
doğrulanır; Mart'ın dört kesimi kullanılabilir ve yalnız eksik kesim
indirilecek. Sonraki aylar aynı kabul düzeniyle devam eder. Progress listesi
ilk evrede kısa olabilir; mevcut ürünlerin silindiği anlamına gelmez.

Çalışan kuyruk varken ikinci kez çağrılmaz. Bu yeni dosya ile daha sonraki
normal duruşta yapılacak açık çağrı:

```powershell
.\.venv\Scripts\python.exe scripts/landcover/run_vegetation_training_v2.py run --proof-sha 0e62593189533ad6223035e1260cd40306c23d860d667fd228adc8e57970b397 --start 2018-01 --end 2023-12 --hours 24 --batch-minutes 240 --min-free-gib 10
```

Bu yerel iş GCP VM'den bağımsızdır. Bilgisayar açık/uyanık ve internete bağlı
kalır. 2025 final test, yangın etiketi, tarihsel erişim zamanı ve model
eğitimi açılmaz. Adaylar geçmiş 30/60 günlük pencerelerden haftalık kesim
ve en fazla sekiz günlük taşıma ile hazırlanır; her gün yeni görüntü iddiası yok.
