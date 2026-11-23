# Deneysel S/U paketi sonrası tek sabit doğrusal olmayan sıralama önerisi

**Sonraki 23 Kasım kaydı:** Bu somut öneriden sonraki devam
talimatıyla ayrı yürütme yapılandırması oluşturuldu ve deney
tamamlandı. [Sonuç ve ayrı denetim](NONLINEAR_RANK_RESULTS_2026-11-23.md).
Aşağıdaki metin hazırlık anını anlatır; eski öneri izinleri değiştirilmedi.

23 Kasım 2026. Girdi ve grup desteği hesaplandı; **yeni model eğitimi,
paket kurulumu veya skor üretimi yapılmadı.** Kullanıcının son devam
talimatı yöntem/deney hazırlığı olarak uygulandı. Önceki açık A kararı
deneysel inceleme paketini kapsıyordu; yeni eğitimi kapsamıyordu.

## Hangi soruyu sınayabiliriz?

Tamamlanan doğrusal sıralama pilotu aynı hücre/ayda sınırlı günlük
ayrım sağladı; farklı Mersin kaynağına aktarımı zayıftı. FWI'nin küçük
Haziran kesitinde de belirgin model üstünlüğü çıkmadı. Bu sonuçlar
etiketleri düzeltmez veya doğrusal olmayan bir yöntemin daha iyi
olacağını kanıtlamaz.

Yeni, dar hipotez: **Sıcaklık, rüzgâr ve geçmiş bitki nemi arasındaki
doğrusal olmayan etkileşimler, aynı hücrenin aynı ayındaki aday-bağlamlı
gün sıralamasını iyileştirebilir mi?** Örneğin sıcaklığın etkisi rüzgâr
ve nem durumuna göre değişebilir; doğrusal model bu etkileşimi açıkça
öğrenmiyor. Bu, yüksek sayı bulana kadar model ailesi denemek için
açık yetki değil; bir sabit karşılaştırma önerisidir.

## Önerilen A: dokuz ayarda aynı küçük XGBoost sıralama modeli

XGBoost'un `XGBRanker` arayüzü gruplar içinde sıralama öğrenir.
`rank:pairwise` ikili sıralama lojistik kaybını kullanır; model çıktısı
bir sıralama skorudur. Girdiler sorgu/grup kimliğine göre sıralı olmalı.
Bizim gruplarımız hücre–takvim ayı olacak; grup kimliği girdiye
verilmeyecek. [Resmî öğrenme ve kayıp açıklaması](https://xgboost.readthedocs.io/en/stable/tutorials/learning_to_rank.html).

Mevcut dokuz öneri ayarı korunacak. Kütüphanenin 1/0 uygunluk değeri
yalnız eski S önerisi var/yok işaretinden gelecek; gerçek yangın Y
veya kabul edilmiş L alanlarına yazılmayacak. Bu kaynak koşullu
sıralamadır; gürültülü PU hedefini matematiksel olarak tanımlanabilir
veya düzeltilmiş yapmış sayılmayacak. Kütüphanenin arama sonucu/tıklama
konum yanlılığı seçeneği de yangın kaynağı seçim yanlılığını çözmüş
gibi kullanılmayacak.

Sabit plan:

| Konu | Hazırlanan kapsam |
|---|---|
| Öğrenme | Yalnız 2018–2021 |
| Keşif değerlendirmesi | Daha önce incelenmiş 2022; kör test değil |
| Girdi | Aynı 11 meteoroloji + 4 geçmiş bitki örtüsü alanı |
| Girdi dışı | Hücre kimliği, ay/tarih, koordinat, statik örtü/arazi, hedef penceresi ve kaynak bilgileri |
| Aday gruplaması | Dokuz ayar ayrı; üretim ayarı seçilmez |
| Öğrenmeye bilgi taşıyan gruplar | Aynı hücre–ayda en az bir eski S önerisi ve bir atamasız gün; iki tarafta dinamik alanlar tam |
| Eksiklik | Önceki pilotla aynı tam 15 alan desteği; eksikler kaynak paketten silinmez veya doldurulmaz |
| Ağaçlar | 100 ağaç, en fazla derinlik 3, öğrenme hızı 0,05 |
| Diğer sabitler | min_child_weight 5, L2 1, satır/sütun payı 1, CPU hist, 4 iş parçacığı, seed 20261123 |
| Çift oluşturma | topk 31; hücre–ay grubu en fazla 31 günlük satır içeriyor |
| Normalizasyon | İki LambdaRank normalizasyon seçeneği true; karşılaştırmada bu uygulama farkı açık |
| Ayar araması | Yok; 2022 ile erken durdurma, parametre seçme veya yeniden ayarlama yok |
| Yerel sınır | Kurulumdan sonra toplam en fazla 15 dakika; dokuz model sırayla, CPU; bulut yok |

`topk` ayarı grubun başındaki kayıtlarla çift kurmayı denetler.
31 seçimi burada listenin günlerini kesmemek içindir; kütüphane içi
çift ağırlıklarının/tekrarlarının eski doğrusal kodla birebir aynı
olduğu iddia edilmez. Ölçümde aynı sabit değerlendirme çiftleri
kullanılacak. [Resmî sıralama parametreleri](https://xgboost.readthedocs.io/en/stable/parameter.html#parameters-for-learning-to-rank-rank-ndcg-rank-map-rank-pairwise).

## Ölçülen girdi desteği

44.082 anahtarlık mevcut paketin hash ile bağlı özellik/üyelik
dosyaları kullanıldı; ana paket değiştirilmedi. Beş yıllık tam takvim
veya yeni U ağırlığı üretilmedi.

| Ayara göre | Hazır sayı |
|---|---:|
| 2018–2021 dinamik alanları tam takvim satırı | 35.376 |
| İki bağlamı da içeren öğrenme grubu | 938–1.160 hücre–ay |
| Bu öğrenme gruplarındaki tam satır | 28.068–34.887 |
| Potansiyel S–atamasız gün çifti | 28.081–39.014 |
| 2022 dinamik alanları tam satır | 5.982 |
| 2022 aynı-hücre/ay değerlendirme çifti | 5.733–6.406 |

Potansiyel öğrenme/değerlendirme çift sayıları dokuz eski doğrusal
deneyin sayılarıyla eşleşti. Bu, yeni kütüphanenin iç çift listesini
çalıştırıp doğrulamak değildir. Karşılaştırma sırasında anahtar ve
çift kimlikleri de denetlenecek.

Ayrıca **mevcut** ayrı Mersin takvimi hazır: 2.383 satır, 2.323 tam
dinamik satır, 2.329 aynı-hücre/ay çifti. Öğrenilen dokuz model
değişmeden bu kesitte de değerlendirilebilir; yeni X üretimine
gerek yok. Bu kaynak daha önce incelendi ve konum/zaman/kapsam
belirsizliği sürüyor; bağımsız gerçek yangın doğrulaması diye
sunulmayacak.

## Değerlendirme sözleşmesi

Eski doğrusal skorlar yeniden öğrenilmeden, aynı sonlu anahtar ve
çiftlerde karşılaştırılacak. Tüm ayarların genel, 1–3 gün aralığı,
önce/sonra ve il/hücre bağlamı sonuçları birlikte raporlanacak.
Kaynak koşullu yardımcı çift AUC, gerçek yangın AP'si değildir;
ana araştırmanın AP tercihi değişmiyor. Yakın gün ve farklı kaynak
aktarımı zayıf kalırsa yalnız genel sayıya dayanarak başarı denmeyecek.
Önceden gerekçelendirilmiş bir istatistiksel başarı eşiği olmadığı
için yeni bir sayısal kabul eşiği icat edilmedi.

Girdi grupları kaynak bağlamına koşullu; 1.670 öneri gerçek yangın
doğrulaması değil. Daha iyi sıra skoru bile gözlem, gerçek yeni olay,
PU karışım/pozitif seçimi ve operasyonel erişim boşluklarını kapatmaz.
Kırmızı/sarı/yeşil risk yayımlama veya kalibrasyon bu öneride yok.

## Ortam ve kullanıcı kararı

XGBoost bu yerel `.venv` içinde kurulu değil. A seçilirse proje
ortamına `xgboost==3.4.1` sabit sürümünü eklemek, bağımlılık kaydını
güncellemek ve uyumu kontrol etmek gerekiyor. Resmî PyPI kaydı
Windows x64 wheel için yaklaşık **48,9 MB** ve SHA-256
`2d30fa513673101f542fdcbd18f30c8f96c064046f798635ac08663e9969f81b`
veriyor. Henüz indirilmedi veya kurulmadı. Güncel resmî dokümanın
başlığında 3.4.2 görünmesi, bu kurulumun yapılmış olduğu sayılmadı;
seçilen 3.4.1 ortamı çalıştırmadan ayrıca doğrulanacak.
[Resmî paket ve Windows dosyası](https://pypi.org/project/xgboost/3.4.1/#files).

**A önerisi:** Bu tek sabit denemeyi, dokuz yeni model ve iki mevcut
2022 değerlendirme takvimiyle, belirtilen kurulum/süre sınırında
çalıştırmak. Daha karmaşık günlük ilişkilerin katkısını somut olarak
sınar; iyileşme veya ana hedef doğrulaması garantisi yok.

**B:** Yeni eğitim açmadan mevcut deneysel paketi ve sonuçları
koruyup yöntem/sunum yazımına odaklanmak. Bu yönde yeni bir model
başarımı elde edilmiş sayılmaz.

Bu seçim yeni model eğitimi içerdiği için araştırmacıya sunulur.
Genel devam, inceleme ekranı onayı ve önceki paket A kararı
bu eğitimin yetkisi olarak kaydedilmedi. 2023–2025 bilimsel değerleri,
yeni kurumsal yazışma, bulut işi, gerçek Y/L ve nihai etiketli
birleştirme kapsam dışında kalır.

## Tekrarlanabilir hazırlık

- Üretici: `scripts/quality/prepare_nonlinear_rank_comparison.py`.
- Açık öneri: `configs/nonlinear_rank_proposal_v1.json`; eğitim izni false.
- Makbuz: `outputs/reports/dataset/nonlinear_rank_preparation_v1/20261123T131121Z_14674f77/readback.json`.
- SHA-256: `cda37ee7be3820cc1396e939f7eeef78799ae262f21103da3029edd4710454c9`.
- Aynı dizinde dokuz ayar destek tablosu, ayrı Mersin grup envanteri,
  hücre–ay grupları ve 15 alanın şeması bulunur; öğrenilmiş model yok.
- Beş yeni grup/zaman/izin koruma testi dahil **33 ilgili test** geçti;
  üç yeni Python dosyası Ruff kod/biçim kontrolünden geçti.
