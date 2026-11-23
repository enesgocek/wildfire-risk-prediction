# Veri ve yöntem bölümü — mevcut deneysel sürüm taslağı

23 Kasım 2026. Bu metin tamamlanan işlere dayalı teslim hazırlığıdır;
ana yöntemin bilimsel kabulü, nihai etiketli veri seti veya yayın
metninin onayı değildir. Sonraki bulgular ayrı tarihli sürümle eklenir.

## Araştırma amacı ve gözlenebilir hedef

Araştırmanın amacı Antalya, Muğla, İzmir ve Mersin'de 5 km hücreler
için sonraki 24 saatlik yeni orman/çalılık yangını riskini incelemektir.
Günlük başlangıç 00:00 UTC, aday hedef penceresi `(T, T+24 saat]`
olarak tanımlanmıştır. İlk aktif uydu tespiti gözlenebilir bir
vekil göstergedir; fiziksel tutuşma zamanı ve bağımsız olay kimliği
olarak yorumlanmamıştır. Devam eden tespitler yeni yangına otomatik
çevrilmemiştir. [Bağlayıcı kapsam ve zaman sözleşmesi](../PROJECT.md).

## Çalışma alanı ve özellik hazırlığı

Tamamen su hücreleri için önceden tanımlanan kuraldan sonra 2.889
hücre hazırlık havuzunda korunmuştur. Hücredeki orman/çalılık oranı
ile ilk uydu adayının yerel örtüsü ayrı ele alınmıştır. Karma hücreler
asgari yüzde koşuluyla elenmemiş; sınırlı insan görsel notları bütün
alana genellenmemiştir. CGLS 2017 ana, CORINE 2018 yardımcı örtü
bağlamıdır; farklı tarihlerdeki harita uyumu doğruluk ölçümü değildir.

Meteoroloji, geçmiş bitki örtüsü ve statik arazi/örtü bilgilerinden
27 alanlık mevcut özellik hazırlığı kullanılmıştır. Anahtarı
`grid_id, prediction_timestamp_utc` olan CSV'ler; ayrı kaynak, zaman
ve eksiklik kayıtlarıyla korunmuştur. ERA5-Land geriye dönük yeniden
analizdir; geçmiş verinin T anında operasyonel olarak erişilebilir
olduğu ileri sürülmemiştir. Özelliklerin hedef penceresinden bilgi
taşımaması, yöntem kabulünden ayrı teknik kontrol konusudur.

## İncelenebilir deneysel örneklem

Mevcut deneysel paket 2018–2022 döneminden **44.082 farklı hücre–gün,
822 hücre ve 27 özellik** içerir. Bunların 41.358'inde 27 alanın
tamamı vardır; 2.724'ünde en az bir alan eksiktir. 2018–2021 rolünde
37.509, keşif amaçlı 2022 rolünde 6.573 satır vardır. Bu tablo dört
ilin bütün günlerini temsil eden bir nüfus paneli değildir: kaynak/
aday bağlamıyla seçilmiş hücre–ay takvimidir. Örnekleme tasarımının
genel saha dağılımına aktarımı kanıtlanmamıştır.

Dokuz başlangıç gruplama ayarı ayrı tutulmuştur: 500/1.000/2.000 m
ve 24/48/72 saat. 1.670 farklı anahtar en az bir olası S önerisinde
yer alır; 412 anahtarın öneri varlığı ayara duyarlıdır. Bu sayılar
bağımsız yangın sayısı değildir. 2017 örtü bağlamı ile aday üyeliği
koşulları da gerçek pozitif doğrulaması sağlamaz. Ayarlar sonuçlara
bakılarak üretim için seçilmemiştir.

S önerisi bulunmayan satırlar **atamasız/belirsizdir**; gerçek negatif
olarak adlandırılmamıştır. Eski rastgele U örnekleminin ağırlıkları
bu kaynak koşullu takvime taşınmamıştır. `target` ve
`accepted_L_membership` boş; `daily_observation_status=unknown`,
`negative_label_permitted=false` korunmuştur. HTML inceleme, CSV ve
ZIP çıktıları teknik olarak denetlenmiş; araştırmacı sayım, filtre
ve ayrıntı ekranını kontrol etmiştir. Bu kullanılabilirlik kontrolü
insan tarafından yangın etiketlemesi değildir.
[Paket, kabul sınırı ve hash'ler](../EXPERIMENTAL_SU_PACKAGE_2026-11-23.md).

## Dinamik sıralama deneyinin tasarımı

Ana yangın hedefi henüz doğrulanamadığından yapılan pilot, kaynak/
aday bağlamının sıralanmasını araştırır. 11 meteoroloji ve dört
geçmiş bitki örtüsü alanı kullanılmıştır: sıcaklığın ortalama/alt/üst
değerleri, çiy noktası, iki rüzgâr özeti, yüzey toprak nemi,
24/72/168/336 saat yağış birikimleri, 30/60 gün NDVI ve NDMI
medyan özetleri. Tam adlar deney makbuzunda bulunur. Kimlik, tarih,
koordinat ve statik örtü bu 15 alanlık karşılaştırmanın girdisi değildir.

Öğrenme yalnız 2018–2021; değerlendirme daha önce incelenmiş 2022'dir.
Aynı hücre ve takvim ayı içinde en az bir S önerisi ve bir atamasız
tam-girdili gün olan gruplar kullanılmıştır. Eksik alanlar doldurulmamış
ve kaynak paketten silinmemiştir. İlk doğrusal model, bu günlerin
özellik farklarından lojistik sıralama öğrenmiştir. Sonraki tek sabit
XGBoost `rank:pairwise` deneyi aynı 15 alanı ve uygunluk işaretini
kullanmıştır. Kütüphane içindeki 1/0 uygunluk değeri yangın Y=1/Y=0
değildir. Bu deney gürültü-düzeltilmiş PU kestiricisi veya PU
varsayımlarının doğrulandığı bir yöntem olarak sunulmamıştır.

XGBoost 3.4.1 için 100 ağaç, derinlik 3, hız 0,05, CPU hist,
dört iş parçacığı ve seed 20261123 önceden sabitlenmiştir.
`topk=31`, en çok 31 günlük hücre–ay gruplarını kesmemek içindir;
iki algoritmanın iç çift ağırlıkları/tekrarları eşit kabul edilmemiştir.
Parametre taraması, 2022 ile erken durdurma veya en iyi ayar seçimi
yapılmamıştır. Dokuz sabit modelin hepsi raporlanmıştır.

## Değerlendirme, referanslar ve sonuçların anlamı

Aynı hücre/ay kaynak günü ile atamasız gün çiftleri için üstün sıraya
1, eşitliğe 0,5 puan verilmiştir. Ortalama yardımcı çift AUC olarak
adlandırılmıştır. Ana araştırmada kararlaştırılan AP'nin yerine
geçmez; gerçek yangın doğruluğu veya olasılığı değildir. Bağımlı
çiftler bağımsız gözlem sayılmamış; sadece genel sonuç değil 1–3 gün,
4–30 gün, kaynak gününden önce/sonra ve il/hücre kesitleri incelenmiştir.

Farklı kaynağı araştırmak için mevcut Mersin arşivinden hazırlanmış
ayrı 2022 takvimi kullanılmıştır: 2.383 gün, 2.323 tam dinamik satır,
2.329 karşılaştırma çifti. Bu kaynak daha önce incelenmiş olup kör
doğrulama değildir; koordinatın rolü, saat standardı, kayıt birimi
ve kapsamındaki belirsizlikler sürmektedir. İki takvimin sayıları
toplanarak bağımsız tekil veri sayısı elde edilmemiştir.

Sabit XGBoost, ayrı Mersin genelinde dokuz ayarın tamamında eski
doğrusal skordan daha yüksek yardımcı ölçü üretmiştir; yeni aralık
0,553242–0,588235, eski 0,522542–0,540575'tir. Dört il uydu adayı
takviminde yeni 0,565731–0,609741; eski 0,585685–0,595230'dur ve
yalnız üç ayar iyileşmiştir. Yakın günler ve zamansal yön sonuçları
güçlü genel yangın tahmin becerisi kabulüne yeterli görülmemiştir.
[Tüm sonuçlar ve bağımsız hesap](../NONLINEAR_RANK_RESULTS_2026-11-23.md).

FWI ile önceki ayrı referans incelemesi, Haziran 2022'de yedi Mersin
hücresi/203 tarih/196 çiftle sınırlıdır. Önceki nominal günün FWI
değeri retrospektif kıyasta kullanılmıştır; yayımlanma veya operasyonel
erişim saati doğrulanmamıştır. Bu kıyas yeni XGBoost deneyiyle aynı
örneklem değildir; FWI ile XGBoost arasında ölçülmemiş üstünlük
çıkarılmamıştır. [FWI kıyasının kapsamı](../FWI_REFERENCE_RESULTS_2026-11-23.md).

## Tekrarlanabilirlik ve henüz desteklenmeyen iddialar

### Aynı gün sonraki kalite uyumu ve prototip yönü

İlk XGBoost koşusu 15 alanın doluluğunu esas alan geniş meteoroloji
desteğiyle öğrenmiştir. Kaynak alan payları ayrıca incelendiğinde,
sonlu değerin tam hücre desteği olmadığı gösterilmiştir. 3 Ekim'de
tanımlanmış tam alan ana profil / %90 duyarlılık / pozitif alan
izleme kuralları değişmeden, 540 sabit model ölçüsünde ayrı
denetlenmiştir. Meteoroloji eksiklerinin alan desteği sıfır;
bitki örtüsü eksiklerinde ilgili retained snapshot yoktur. Fiziksel
eksiklik nedeni veya bulut etkisi bu bayraklarla tekilleştirilmemiştir.

Aynı sabit XGBoost yaklaşımı, tam alan kuralına uyumlu 2018–2021
öğrenme satırlarıyla dokuz ayrı modelde uygulanmıştır. 2022'de
aynı tam-alan çiftlerinde eski geniş-alan model ve doğrusal skorla
karşılaştırma yapılmıştır. Öğrenme 23.280–29.140 satır/777–967
hücre–aydır. Yeni yardımcı AUC dört ilde 0,567280–0,601843,
ayrı Mersin'de 0,528110–0,566892'dir. Bu sayılar önceki farklı
paydalı sonuçların yerine yazılmamıştır. Otomatik iyileşme veya
gerçek yangın doğrulaması kabul edilmemiştir.
[Ortak-payda kıyas ve denetimler](../DATASET_SUPPORT_AND_WEATHER_REVIEW_2026-11-23.md).

Araştırmacı sonraki A seçimiyle teknik S/U sürümünün ardından yerel
araştırma prototipine geçişi seçmiştir. Mevcut iki 2022 takvimi ve
dokuz kaliteye uyumlu modelin sonuçları, kaynak/kalite/27 özellik
bağlantısıyla görüntülenir. Sıra grafiği aynı hücre/ay içinde
tanımlıdır; risk olasılığı, gerçek negatif veya canlı tahmin değildir.
[Prototip ve henüz otomatik yapılmamış tarayıcı kontrolü](../RESEARCH_PROTOTYPE_2026-11-23.md).
Ana yangın hedefine ilişkin bilimsel koşullar bu çalışma yönüyle
doğrulanmış sayılmamıştır.

Girdi/çıktı/üretici hash'leri, sürümlü açık yapılandırmalar, ayrı
denetleyiciler ve yerel MLflow kayıtları tutulmuştur. Son deneyde
yeniden yüklenen dokuz modelin skorları, aynı çift kimlikleri ve
4.420 sonuç satırı ayrı hesapla eşleşmiştir. Kod kontrolleri ve
araştırmacının manuel yorumları farklı kanıt türleri olarak kaydedilmiştir.
Yapay zekâ destekli hazırlık ve analiz [katkı kaydında](AI_USE.md) açıklanır.

Kaynak üyeliğinden gerçek yeni yangın hedef sırasına aktarım,
gürültü/seçim varsayımları, yeterli gözlem ve güvenilir değerlendirme
dayanağı açık kalmaktadır. Doğrulanmış yangın AP'si, kalibre olasılık,
doğrulanmış kırmızı/sarı/yeşil risk ürünü veya operasyonel erken uyarı
başarımı elde edildiği söylenemez. Genel plandaki 2023 kalibrasyon,
2024 karşılaştırma ve kapalı 2025 final rolleri bu pilotta açılmamıştır.
Ana hedef korunur; inceleme sürümünün tamamlanması hedefin başarıyla
tamamlandığı anlamına gelmez. Nihai etiketli birleştirme, güncel ayrı
parça denetimi ve rapor kimliğine bağlı kullanıcı onayını gerektirir.
