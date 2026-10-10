# Habitat, veri desteği ve olay inceleme paketi — 10 Ekim 2026

## Kapsam

Çalışan veri kuyruklarından bağımsız olarak, kabul edilmiş habitat,
meteoroloji ve keşif olay kayıtları bir araya getirildi. Amaç kapsam
kararı ve zor vaka incelemesi için izlenebilir kanıt hazırlamaktır.
Habitat eşiği, olay senaryosu veya eğitim etiketi seçilmedi; yeni uzaktan
veri isteği oluşturulmadı. Yöntem `decision_review.py`, giriş noktası
`scripts/quality/prepare_decision_review.py` içindedir.

## Meteoroloji–habitat destek kesişimi

Eğitimdeki 2.191 günün kayıtlı minimum/maksimum meteoroloji destekleri
sabit ve birbirine eşit. Üç grup 2.899 hücrenin tamamını kapsıyor:

| Meteoroloji desteği | Hücre | AOI alanı km² | 2017 orman sınıfı alanı km² |
|---|---:|---:|---:|
| Yok | 189 | 1.480,595 | 800,217 |
| Kısmi | 310 | 5.569,002 | 3.250,427 |
| Tam | 2.400 | 53.677,517 | 29.783,951 |

Grupların hücre sayıları × 2.191 gün, önceki meteoroloji raporundaki
414.099 eksik, 679.210 kısmi ve 5.258.400 birincil uygun hücre-gün ile
ayrı hesap yolunda eşleşti. Bu meteoroloji desteğidir; yangın gözlem
kapsamı veya habitat uygunluğu değildir. Destek eksikliği kaydının zaman
boyunca sabit oluşu, bu kayıtta geçici indirme hatası açıklamasını desteklemez.

Orman sınıfı alanı `forest_fraction × covered_area_km2`; AOI alanı farklı
bir paydadır. İki alan birbirinin yerine kullanılmadı. Tam meteoroloji
desteğiyle sınırlandırma, orman sınıfı bulunan kıyı/sınır alanlarını da
dışarıda bırakabilir; bu kapsam etkisi model başarı hesabından ayrı raporlanmalıdır.

Önceki 15 habitat eşiğinin hücre sayıları yeniden eşleşti. Örnek olarak
orman+çalılık sınıf payı en az %25 olan 2.353 hücrede meteoroloji desteği
135 yok, 257 kısmi, 1.961 tamdır. Bu eşik seçilmiş habitat politikası değildir.

Harita `support_review.png`, EPSG:6933 üzerinde yalnız kabul edilmiş dört
ilin AOI parçalarını gösterir. Basemap veya yeni harita verisi kullanılmadı;
görsel yerelde açılarak kontrol edildi.

## Seçim yöntemi ve inceleme dosyaları

**33 habitat örneği**: bütün 10 yalnız-su harita hücresi ve 17 arazi alan
desteği işareti; ayrıca doğal örtüsü yüksek olup meteoroloji desteği
yok/kısmi olan üçer örnek ve orman–tarım karışımı üç örnek. Seçim nedenleri
örtüşebilir; aynı hücre bir kez tutuldu. Puan eşitliğinde hücre kimliğiyle
kararlı sıra kullanıldı. Örneklem temsil edici yaygınlık tahmini değildir.

**53 olay-senaryo örneği**: her dokuz keşif senaryosunda uzun zamansal
zincir, mekânsal zincir, ilk anda çok hücre, takvim yılı/dönem sınırı
işaretleri için en uç örnek ve bir işaretsiz referans seçildi. Aynı
senaryoda aynı küme bir kez tutuldu; bütün seçim nedenleri korundu.
İşaretsiz referans, doğrulanmış yangın veya negatif örnek değildir.

53 örnekte **28 farklı tespit üyeliği deseni** bulunuyor; bunlar bağımsız
yangın sayısı değildir. Senaryolar arasında aynı tespitler tekrar eder.
Seçilen üyelerin senaryo tekrarlı toplam satırı 50.549'dur. Her örnekte
üyelik SHA-256, ilk/son tespit ve ilk andaki bütün hücreler özgün atama
dosyasıyla eşleştirildi. İlk hücrelerdeki orman+çalılık payının min/max
değerleri raporlandı; canonical hücre nihai hedef olarak seçilmedi.

En uzun seçili örnek 2.000 m/72 h senaryosunda 1.236,217 saat, 93 tespit
ve tek hücre içeriyor. Bu durum uzun süren yangın, farklı yangınların
birleşmesi veya kalıcı sıcak kaynak gibi alternatifleri incelemeye açar;
tek başına bunlardan birini kanıtlamaz. Aynı tespit kaynağından yeni
hesap yapmak bağımsız yangın doğrulaması değildir.

Çıktı: `outputs/reports/dataset/decision_review_v1/20261010T124447Z_f3e2eef2/`.

- `support_cells.csv`: 2.899 hücrenin tam destek/kapsam envanteri.
- `habitat_cases.csv`: 33 seçili hücre, konum noktası ve seçim nedenleri.
- `event_cases.csv`: 53 senaryo örneği, ilk hücreler ve inceleme işaretleri.
- `event_members.csv`: özgün seçili tespitlerin koordinat/zaman/kimlik bağlantısı.
- `expert_review_template.csv`: inceleyen, tarih, kaynak, yorum ve karar alanları boş form.
- `support_review.png`: kaynak kapsamı ve coğrafi inceleme işaretleri.
- `readback.json`: kaynak/çıktı/kod hash'leri, sayılar ve kabul sınırları.

Formun hazırlanması uzman incelemesinin yapıldığı anlamına gelmez.
Ham/ara tablolar ve bu vaka dosyaları GitHub'a gönderilmez.

## Kaynak tanımlarının incelenmesi

Resmî [Earth Engine Copernicus CGLS-LC100 tanımı](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_Landcover_100m_Proba-V-C3_Global)
ayrık sınıf bandını sürekli örtü payı bantlarından ayırır. Bu projedeki
`forest_fraction`, orman sınıfı piksellerinin alan payıdır; ağaç kapalılığı
bandı değildir. Kaynak açıklaması çok yıllık odunsu tarımın uygun orman
veya çalılık sınıfına girebildiğini belirtir. Dolayısıyla sınıf payı tek
başına doğal orman ile bahçe/plantasyonu ayıramaz. Haritanın referans yılı
2017, tarihsel yayımlanma zamanı yerine kullanılamaz. Kaynak tanımı
araştırma kapsamını gerekçelendirir; yerel habitat doğrusu sağlamaz.

[NASA FIRMS'in statik termal anomali açıklaması](https://wiki.earthdata.nasa.gov/spaces/FIRMS/blog/2025/02/28/425855667/FIRMS%2Bincorporates%2Bstatic%2Bthermal%2Banomalies%2Bdata%2Bto%2Bhelp%2Busers%2Bdifferentiate%2Bbetween%2Bvegetation%2Band%2Bnon%2Bvegetation%2Bfires.)
endüstriyel/doğal ısı kaynaklarının ek kanıtla incelenmesini açıklar;
anlatılan maske 2023 tespitlerinden türetilmiş, deneysel bir üründür.
Bu maskeyi erken eğitim yıllarına zaman bilgisi yokmuş gibi uygulamak
uygun olmaz. Bu, kaynak açıklamasından çıkarılan bir erişim/zaman
inceleme gereğidir; mevcut CSV Type alanının bu maskeden üretildiğinin
kanıtı değildir. NASA destek yazışmasının yanıtı beklenmeye devam eder.
Bu çalışmada maske indirilmedi, Type filtresi değiştirilmedi.

## Kabul ve açık kararlar

Kabul JSON SHA-256:
`ad0567e829719d4b2b45cb7b696ce4442c8fc083268a670c4696b1bd642aa5a9`.
Kaynaklar önce ve sonra aynı hash'te; CSV'ler yeniden okundu. Ağ bağlantısı
engellenmiş gerçek çağrı geçti. Beş yeni kontrol dahil **39 ilgili test**
geçti; Ruff/biçim kontrolü geçti. 2024'ün 2.960 ortak dosya satırının
tarihleri dönem filtresi için okundu; seçim/analiz yalnız 30.295 eğitim
adayıyla yapıldı. 2025 verisi açılmadı; kaynak çıkarımı ve dokuz grafik
yeniden hesaplanmadı.

Kapsamı daraltma, komşudan meteoroloji doldurma, kalıcı kaynak silme veya
olay eşiği seçme kararı verilmedi. Sonraki insan/uzman değerlendirmesinde
vaka başına dış kanıt ve gerekçe kaydedilmeli; belirsizler sessizce
pozitif/negatif yapılmamalıdır. [Veri seti kabul sözleşmesi taslağı](DATASET_ACCEPTANCE_CONTRACT_2026-10-10.md)
bu kararların hangi aşamada kabul gerektiğini tanımlar.
