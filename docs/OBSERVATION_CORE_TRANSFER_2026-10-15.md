# Sınırlı ham kaynak kontrolüne geçiş — 15 Ekim 2026

Amaç, [katalogda doğrulanan 584 kaynağı](OBSERVATION_CORE_CATALOGUE_2026-10-15.md)
kontrollü yerel işleme açmadan önce tek bir gerçek çiftte indirme, içerik
ve native dosya eşleşmesini sınayacak düzeni hazırlamaktır. **Yeni çekirdek
çiftinin indirme denemesi henüz çalıştırılmadı.** Yerel Earthdata girişi
araştırmacının özel terminalinde yapılacaktır; bu hazırlık etiket kabulü değildir.

## Hazırlanan somut kapsam

292 çiftin sırası kaynak günü ve örnek kimliğine göre sabittir. Kaynaklar
sonuca, yerel bulunabilirliğe veya küçük boyuta göre yeniden seçilmedi.
Komut yalnız ilk çifti çalıştırır; diğer 291 çift envanterdir.

- İlk çift: **`SNPP:2018045.0000`**, nominal kaynak günü **14 Şubat 2018**.
- İki dosyanın tarihsel tam boyutu: **191.244.528 bayt**, yaklaşık **191,24 MB**.
- Bütün envanterde en büyük çift: **198.844.597 bayt**. Toplam tarihsel
  kaynak yükü **53.517.820.515 bayt**; bu toplam yeni indirme değildir.
- Hazırlıkta ölçülen boş disk: **97.769.041.920 bayt**, yaklaşık **97,77 GB**.
  Bu anlık ölçüm sürekli kapasite garantisi değildir; çalışma yeniden kontrol eder.
- Plan başına ham önbellek tavanı **2 GB**, korunacak boş disk **20 GB**,
  tek işçi ve girişten sonraki alt süreç için **900 saniye** sert sınır.

Bu ilk çift bir erişim/içerik denemesidir. Rastgele doğruluk örneklemi,
tam gözlem yeterliliği veya yeni yangın sayısı değildir. Ana 156 hücre-günlük
yöntem kohortu ve 72 aylık araştırma kapsamı değişmedi.

## Dosya bütünlüğü ve kesinti davranışı

`prepare_observation_core_transfer.py` çevrimdışıdır. Kabul edilmiş katalog
yanıtlarını, kaynak planını, kod/kilit dosyalarını ve donmuş girdileri
hash ile bağlar; yalnız tam kimlik ve metadata eşleşen referansları alır.
`earthaccess==0.17.0`, mevcut bulut gereksinimiyle aynı sürümde ayrı
`earthdata` isteğe bağlı bağımlılığı olarak kilitlendi ve yerelde kuruldu.
Temel bilimsel bağımlılıklar değiştirilmedi.
Yeni kurulumda isteğe bağlı grup, proje kökünde
`.venv/Scripts/uv.exe --cache-dir outputs/cache/uv sync --frozen --extra earthdata`
ile aynı kilitten kurulabilir; bu komut Earthdata girişi yapmaz.

İndirme işçisi şu koşulları uygular:

- Tam dosya adı ve eğitim dönemi guard'ı; yalnız iki NASA cloud alanı,
  HTTPS ve varsayılan/443 portu. URL içinde kullanıcı/parola/query bulunamaz.
- Özel oturumdaki bearer yalnız isteğin belleğindedir; veri uç noktasında
  yönlendirme takip edilmez. 302/401/403 veya başka başarısız yanıt kabul
  edilmez; farklı URL/sürüm otomatik seçilmez.
- Dosyalar sırayla akar. Beklenen boyuttan fazla veri yazılmaz; `Content-Length`
  varsa karşılaştırılır. Her parçada süre ve boş disk kontrol edilir.
- Yeni dosya `.part` olarak başlar. Tam boyut, geçmiş SHA-256 ve varsa
  sağlayıcı MD5/SHA-256 geçmeden asıl `.nc` adına geçirilmez. Böylece
  sağlayıcı checksum'u olmayan yangın dosyasının tarihsel SHA'sı da sınanır.
- Tam dosya yeniden okunup doğrulanırsa tekrar indirilmez. Aynı boyuttaki
  bozuk dosya veya yarım dosya sessizce üzerine yazılmaz. Kısmi bayttan
  HTTP Range devamı yoktur; hata durumunda dosyalar incelenmek üzere korunur.
- Aynı planın önbelleğinde tek yazıcı kilidi bulunur. Sert zaman aşımında
  alt süreç sonlandırılır; yarım dosya/kilit korunabileceği için sonuç
  incelenmeden kör yeniden deneme yapılmaz. Otomatik ham veri silme yoktur.

İçerik kontrolü geçerse mevcut, değiştirilmemiş native eşleştiriciyle yangın
ürününün konum `InputPointer`/girdi adı, konum dosyasının `LocalGranuleID`'si,
iki dosyanın zaman aralığı, fire/QA/lat/lon boyutları ve fire/QA veri türleri
kontrol edilir. Zaman CMR ile, yörünge kimliği konum başlığıyla bağlanır.
Bu işlem tarama alanı/kalite değerlerinin bütün hücrelerde yeniden hesaplanması
değildir; sonuçta `array_values_spatially_audited=false` korunur.

## Gerçekleştirilen yerel sınama

Yeni başlık okuyucu ayrıca daha önce kabul edilmiş yerel
**`SNPP:2019014.0042`** çiftinde çevrimdışı çalıştırıldı. İki ham dosyanın
önceki SHA-256 kimliği korundu. Gerçek girdi bağı, **6.464 × 6.400** native
boyut ve **`SNPP:37379`** yörüngesi önceki kayıtla eşleşti. Bu çift yeni
çekirdekte değildir; yeni kaynağın indirme başarısı olarak sayılmaz.

**22 yeni davranış testi dahil 137 ilgili test** geçti. Bozuk/eksik/fazla
baytlar, checksum çelişkisi, disk/önbellek yetersizliği, süre aşımı, HTTP
hatası/yönlendirme, tam dosyanın tekrar kullanımı, kısmi dosyayı koruma,
tokenın komut/rapor dışında kalması ve etkileşimsiz gizli girişin reddi
denetlendi. İlk testte alt süreç taklidinin bağımlılık importuna da etki
ettiği görüldü; isteğe bağlı import özel giriş yoluna taşındı ve ilgili
testler yeniden geçti. Dört yeni Python dosyasında lint/format ve kilit
dosyasında çevrimdışı tutarlılık kontrolü geçti.

Yeni hazırlık **117 giriş/iki çıktı** hash kapanışını ve **22 donmuş üretim
girdisinin** korunmasını doğruladı. Yeni ham indirme, VM/EE işi, model,
etiket veya 2024/2025 veri erişimi başlatılmadı.

## Çalıştırma ve özel giriş

Bu bilgisayarda önceden yapılandırılmış Earthdata kullanıcı/parola/token
veya `.netrc` bulunmadığı için gerçek indirme otomatik başlatılmadı.
Kimlik bilgileri sohbete veya proje dosyasına yazılmaz. Kullanıcı kendi
bilgisayarındaki PowerShell'de proje klasöründen şu komutu çalıştırabilir:

```powershell
.\.venv\Scripts\python.exe scripts\firms\run_observation_core_pair.py --plan outputs\reports\dataset\observation_core_transfer_v1\20261015T000803Z_d27b748a\native_plan.json --run-one --prompt-login
```

Kullanıcı adı ve parola gizli terminal istemlerinde alınır. Ekranda yazılan
karakterlerin görünmemesi normaldir. `persist=False` kullanılır; kimlik
bilgileri yerel diske kaydedilmez. Giriş kütüphanesinin mesajları ve alt
süreç çıktısı bastırılır; hata raporunda yalnız faz/hata türü ve varsa
sayısal HTTP durumu tutulur. Giriş, Earthdata'nın normal hesap/token
işlemlerini kullanır; yeni bulut kaynağı oluşturmaz.

[earthaccess resmî giriş API'si](https://earthaccess.readthedocs.io/en/latest/api/)
environment stratejisi ve `persist` davranışı için incelendi; yerelde
0.17.0 sürümünün `login`/`Auth.get_session` arayüzü ayrıca kontrol edildi.

Sonuç `outputs/reports/dataset/observation_core_native_v1/` altında yeni
bir dizine yazılır. Yalnız `PASS` veya genel hata satırı paylaşılabilir;
giriş bilgisi, token veya ayrıntılı terminal dökümü istenmez. Hata ya da
kapanma durumunda kısmi dosyalar korunur; önce yerel rapor incelenir.

## Hazırlık kabul kimliği ve açık kapılar

Dizin:
`outputs/reports/dataset/observation_core_transfer_v1/20261015T000803Z_d27b748a/`.

`native_plan.json` SHA-256:
`c55f03dc6df0e8d6855c7459b12bb0e1405f30a93238ec5854314d1e55aeaca9`.
`readback.json` SHA-256:
`654ddeba6f29f3ffbe649246b3b0e5c4444ba6f5970e0d2b6e930d3709e3dafa`.
`completion_readback.json` SHA-256:
`8ff8077e1c3e37a7a919f3618817ac83597b24b5b001c02c0a12bbf92c5bb7d0`.

Tek yeni çiftin içerik/girdi denemesi henüz açık; onun sonucu görüldükten
sonra 156 hücre-gün için alan/zaman/kalite hesabı sınırlı partilerde
genişletilecektir. Toplu 292 çift yürütmesi hazırlanmış veya başlatılmış
sayılmaz. `daily_observation_status=unknown`, `negative_label_permitted=false`,
boş hedefler ve nihai birleştirme için son kontrol/onay kapısı korunur.
