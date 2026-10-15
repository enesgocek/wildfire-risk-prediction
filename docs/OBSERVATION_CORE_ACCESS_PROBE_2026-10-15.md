# Kota kesintisi sonrası devam ve erişim teşhisi — 15 Ekim 2026

## Tamamlanmış işlemin korunması

Kullanıcının kota kesintisi bildirimi sonrasında son tek çift makbuzu ve
mevcut dosyalar yeniden kontrol edildi. Önceki çalışma yarım kalmamış:
`SNPP:2018045.0000` çiftinin bayt/native başlık kabulü ve `13036f9` Git
kaydı tamamlanmış. [Önceki ölçüm ve kapsam](OBSERVATION_CORE_DIAGNOSTICS_2026-10-15.md#ilk-yeni-çiftin-çevrimdışı-bayt-ve-native-başlık-kontrolü)
korunur; başlık okuyucusu bu devam kontrolünde yeniden çalıştırılmış sayılmaz.

Yeni devam denetiminde önceki rapor/kapanış hash'i, aynı kaynak planının
**117 girdisi**, **22 donmuş üretim girdisi** ve iki ham dosyanın toplam
**191.244.528 baytı**, tarihsel SHA ve mevcut sağlayıcı checksum'ları
doğrulandı. Önbellekte yazıcı kilidi yok. Yeni makbuz:
`outputs/reports/dataset/observation_core_resume_v1/20261015T100240Z_bc43fd53/`;
`readback.json` SHA-256
`e43e9d207a34ed042f1496a0504b993dfcc04eefde6cc3cc6fb90e9e7615c5de`.
Eski rapor, plan, ham dosya ve canlı bulut paketleri değiştirilmedi.

## Ayrı erişim teşhisinin amacı

Otomatik aktarımda gerçek 303 hedefinin yalnız `other` sınıfı biliniyor.
Tarayıcıda indirme çalışması bearer ile otomatik erişimin düzeldiğini
kanıtlamaz. Normal tek çift komutu artık önbellekteki iki dosyayı kullanıp
geçebilir; bu da uzak erişim testi sayılmamalıdır.

Yeni `scripts/firms/probe_observation_core_access.py` yalnız aynı planın
ilk çiftindeki yangın/konum kaynakları için **iki GET yanıt başlığı**
inceler. Önce kaynak/kod hash kapanışı ve iki rol koşulu doğrulanır.
Önbellek başarı kanıtı olarak kullanılmaz. `stream=True`,
`allow_redirects=False`, 10 saniye bağlantı/20 saniye okuma timeout'u,
girişten sonra alt süreç için **120 saniye** sert süre sınırı vardır.
Yanıt gövdesi okunmaz; yönlendirme izlenmez, ham dosya yazılmaz.
Requests'in `allow_redirects=False` durumunda bile `Response.next`
hazırlarken yönlendirme gövdesini tüketebildiği yerel kaynak kodunda
görüldü. Bu teşhise özel oturumun `resolve_redirects` yöntemi boş iteratör
döndürür; gerçek Requests Session/adapter regresyonu gövde okuma girişimini
hata sayarak bunu sınadı. Ortak indirme veya kurulu paket değiştirilmedi.
Başlık okuma yine ağ isteğidir; hiç trafik oluşmadığı iddia edilmez.

Taze requests oturumu yalnız bellekteki bearer ile kurulur; netrc/proxy
enjeksiyonu kapalıdır, tarayıcı çerezleri veya Earthaccess yanıt hook'ları
alınmaz. Kütüphane değiştirilmez. Giriş özel terminalde, `persist=False`
ile yapılır; alt süreç yalnız token ortam değişkenini alır, kullanıcı adı/
parola ve token komuta veya dosyaya konmaz. Alt süreç çıktısı bastırılır.

Kayda yalnız sayısal HTTP durumu; izin listesindeki sabit kamuya açık
NASA host adı veya aws/unclassified sınıfı; sabit error/login/authorize/
science-filename sınıfı; sorgu varlığı; literal OAuth hata kodlarından
bilinen biri; tam imzalı CMR nesnesi kontrolü ve Content-Length eşleşmesi
girer. Keyfi host/yol, sorgu değeri, Location, token, gövde ve traceback
kaydedilmez. 200 başlık veya geçerli imzalı nesne yönlendirmesi bile
tam içerik/boyut/hash ya da otomatik aktarım kabulü değildir.

## Kontroller ve çalıştırma

**Dokuz yeni test dahil 168 ilgili test** geçti; deprecation/future
uyarıları hata sayıldı. Özel sorgu değerlerinin kayda geçmemesi, sabit
hedef sınıfları, gövdenin okunmaması/yanıtın kapanması, yönlendirmenin
izlenmemesi, farklı origin reddi, boyut uyuşmazlığı, cache yerine HTTP
isteği ve 120 saniye sınırı/komut gizliliği denetlendi. İlk testlerde
sentetik kaynak fikstürünün zorunlu gün/hash alanları eksikti; fikstür
tamamlandı, bilimsel kaynak guard'ı gevşetilmedi. İki yeni dosyada
lint/format geçti. Önceki 900 saniyelik indirme planı değiştirilmedi.

Kullanıcının özel PowerShell terminalinde:

```powershell
Set-Location "C:\PROJELERIM\wildfire-risk-prediction"
.\.venv\Scripts\python.exe scripts\firms\probe_observation_core_access.py --prompt-login
```

Terminalde yalnız genel sonuç ve yerel rapor dizini gösterilir. Ayrıntı,
`outputs/reports/dataset/observation_core_access_v1/` altındaki yeni,
hash ile kapanmış makbuzdan yerelde okunur. Giriş başarısızlığı teşhis
başarısı sayılmaz; alt süreç hatası/timeout ayrıca kaydedilir. Bu hazırlık
anında yeni kimliği doğrulanmış teşhis sonucu yoktur. Kimlik bilgileri
saklanmadığından kullanıcı özel girişini tamamlamalıdır; sohbette
kimlik bilgisi veya tarayıcı oturumu istenmez.

## Kaynaklar ve bilimsel sınır

[Earthaccess resmî API'si](https://earthaccess.readthedocs.io/en/latest/api/)
bearer oturumunu ve private/environment girişini açıklar; kurulu 0.17.0
giriş/oturum kodu ayrıca okundu.
[NASA dağıtım API'si](https://nasa.github.io/cumulus-distribution-api/)
kimliği doğrulanan veri isteğinin imzalı S3 nesnesine yönlendirilmesini
açıklar. [NASA kaynak deposundaki bearer açıklaması](https://github.com/nasa/cumulus-distribution-api/blob/master/content/s3credentials.md)
ayrı S3 credentials uç noktası içindir; bu projenin dosya uç noktasının
aynı davranışı gösterdiği sonucuna otomatik genellenmedi. Belge incelemesi
gerçek 303 nedeninin veya servis düzeltmesinin kanıtı değildir.

Yeni ham toplu iş, VM/EE işi, 2024/2025 erişimi, etiket/model veya nihai
birleştirme başlatılmadı. Unknown/kapalı negatif izni korunur. Sonraki
teknik karar, gerçek iki başlık kaydı görüldükten sonra verilecek;
keyfi yönlendirme takibi veya kaynak/sürüm ikamesi yapılmaz.
