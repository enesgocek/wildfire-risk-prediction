# Kaynak ve hedef kabulü için protokol taslağı — 19 Kasım 2026

**Aynı gün sonraki somutlaştırma:** Salur için ham tespit, kaynakla
eşleşen hücre ve gerçek pozitif kabulü ayrı tutuldu. Araştırmacının
iki A yönüyle hata içerebilen pozitif/PU girdi hazırlığı ve tek hücrelik
olası L üyeliği önerisi hazırlandı. L önerisi Y=1 kabulü değildir;
bütün PU yöntemleri için kusursuz pozitif zorunluluğu konmadı.
Seçilme/karışım ve değerlendirme dayanağı yine gerekçelendirilmeli.
[Somut vaka, yöntemler ve geçiş sınırı](NOISY_POSITIVE_PU_PILOT_2026-11-19.md).

Durum yöntem hazırlığı. Bu metin mevcut kapalı kabul kodunun yerine
geçmez ve yeni bir etiket üretim yetkisi sağlamaz. Kaynak kökeni,
olay eşleşmesi ve model değerlendirmesi ayrı kanıt düzeylerinde tutulur.

## Kaynaktan modele geçiş

| Düzey | Gereken bilgi | Sağladığı kullanım |
|---|---|---|
| Kaynak bağlamı | Erişilebilir belge, veri kökeni, kullanım şartları | Belgeye dayalı olay anlatımını ve veri alanlarını inceleme |
| Eşleştirme incelemesi | Kayıt birimi/anahtarı, konumun anlamı, zaman anlamı ve aralığı, belgelenmiş belirsizlik | Kaydı aday hücre/gün ve başlangıç hipotezleriyle karşılaştırma |
| Pozitif kabul önerisi | Bağımsız olayla ilişki, yeni başlangıç/devam ayrımı, yerel örtü ve belirsizliğin hedefe etkisi | Sürümlü bilimsel protokolde pozitif kabulün gerekçelendirilmesi |
| Modellemeye geçiş | Pozitif seçilme varsayımları, hedef nüfus, PU yaklaşımı ve değerlendirme dayanağı | Kabul edilmiş protokolle hedef parçası üretimine hazırlık |

Bir düzeyin karşılanması sonraki düzeyi otomatik açmaz. Kayıtların
geometri ve zaman belirsizliği korunabilir. Kusursuz koordinat veya
bütün yangınları içeren bir envanter yeni zorunluluk olarak eklenmiyor.
Mevcut nokta eşleştirme kodu kesin grid/zaman incelemesine özgüdür;
belirsiz geometriye dayalı başka bir protokol yeni sürüm ve gerekçe ister.

PU yaklaşımında belirsiz takvim satırları negatif yapılmaz. Pozitif
örneklerin nasıl seçildiği ve hangi iddianın değerlendirilebileceği
gerekçelendirilmelidir. Tek bir güçlü olay eşleşmesi bütün dört ilin
modellemeye hazır olduğunu göstermez.

## Mersin kaynağına eklenen yöntem bilgisi

18 Kasım'daki doğrudan yayınevi istekleri 403 vermişti. 19 Kasım'da
web erişim aracıyla yayınevinin yöntem ve veri erişimi bölümleri
okunabildi. Önceki erişim kaydı değiştirilmedi. Kaydedilen kopyalar
aracın sayfa görünümüdür; doğrudan HTTP HTML kopyası olarak sunulmadı.

Yayın, arşivi müdahale personelinin belgelediği olay satırları olarak
tanımlıyor. Koordinat elemesi bölgesel uygunluk kontrolü; kullanımı
betimleyici haritalama. Veri erişimi bölümü, anonim kayıtların kamuya
açılma iznini ve CC BY 4.0 lisansını belirtiyor.
[Yayınevi yöntem ve erişim metni](https://journals.sagepub.com/doi/full/10.1177/00368504261495731).

Bu açıklamalar kaynak düzeyini güçlendiriyor. İncelenen bölümlerden
koordinatın gerçek başlangıç noktası olduğu, saat standardı, iki
dosyanın ortak olay anahtarı ve bir yangının kaç idari satır
oluşturabileceği belirlenemedi. Saat alanının adında `ignition` yazması
tek başına zamanın operasyonel anlamını doğrulamıyor.

Önceki 2018–2023 yerel bağlantı raporu korundu. İki dosyada ortak görünen
503 anonim kimliğin yalnız birinde tarih/yıl/ilçe/alan alanları birlikte
uyumlu. 500 tekil imza eşleşmesi inceleme amaçlı olası bağlantı olarak
kalıyor. Bu sayılar yeni ölçüm veya gerçek olay doğruluk oranı değil;
hash'i yeniden kontrol edilen önceki raporun kapsamı.
[Arşiv ve bağlantı incelemesi](MERSIN_OPEN_INCIDENT_ARCHIVE_2026-11-08.md).

## Sunulan seçenekler ve araştırmacı kararı

Öneri, yayımlanan dosyanın teknik alan açıklamasını yazarlardan birine
sormak için hazırlanan taslağın araştırmacı tarafından iletilmesi.
Bu yol, veri istemeden konum/saat/anahtar/kayıt kapsamına açıklık
getirebilir. Yanıt veya kullanılabilir açıklama garantisi yok.
Mersin'e ilişkin yanıt dört ilde değerlendirme sorununu tek başına çözmez.

[Gönderime hazırlanmış dört soruluk taslak](research/MERSIN_AUTHOR_QUESTION_DRAFT_2026-11-19.md).
Diğer seçenek yeni yazışma açmadan açık kaynak araştırmasını sürdürmek.
Bu durumda mevcut alan anlamları açık kalır ve veri kabulü bu varsayımlarla
otomatik tamamlanmış sayılmaz. Araştırmacı 19 Kasım'da yeni yazışma
açmadan açık kaynak araştırmasını sürdürmeyi seçti. Soru taslağı tarihsel
hazırlık olarak korundu; etkin gönderim görevi değil. İleti gönderilmedi.

## İzlenebilirlik ve mevcut kabul durumu

Yöntem/erişim görünüm kopyaları, önceki bağlantı raporu ve açık
kalan dört konu [yapılandırılmış kanıt kaydında](research/mersin_semantics_evidence_2026-11-19.json)
bağlıdır. Dosya hash'leri, yayın kimliği ve yerel bağlantı sayımları
geri okundu. Anahtar sözcük kontrolü kaynak yorumunun doğruluk kanıtı
olarak kullanılmadı. Yöntem incelemesi yapay zekâ desteğiyle yürütüldü.

Kaynak metninde yayımlanan farklı hedefin model başarıları, kendi
projemizin başarısı veya değerlendirme verisi olarak kullanılmadı.
Yerel 2024/2025 olay dosyaları açılmadı. Gözlem `unknown`, pozitif ve
negatif etiket izinleri kapalı; model ve nihai birleştirme yapılmadı.
Bu taslak birinci aşamayı kabul edilmiş olarak kapatmıyor.
