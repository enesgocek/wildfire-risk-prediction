# Mesogeos yanmış alan kaynağı inceleme önerisi

25 Kasım 2026. Yayımlanmış Mesogeos'un ayrı olay/yanmış alan dosyaları
için somut erişim, şema ve kapsam hazırlığı tamamlandı. Yeni kaynaktan
olay satırları açılmadı; önerilen yardımcı kanıt pilotu henüz yürütülmedi.
Bu çalışma yeni bir model kıyası yerine açık hedef/olay kanıtı konusuna yönelir.

## Neden bu kaynak ve hangi sınırla

Mesogeos önceden literatürde incelenmiş bir kaynaktır; burada yeni olan
ayrı dosyalarının güncel erişimini, başlıklarını ve yerel takvime teknik
uygunluğunu denetlemektir. Kaynak, EFFIS yanmış alanlarını MODIS tespitleriyle
ilişkilendirir. Bu yüzden bütün süreçten bağımsız saha gerçeği değildir.
İlk tespit ile fiziksel tutuşma ve nihai alan ile ilk hücre ayrımları korunur.
[Makale bölüm 3 ve 4](https://proceedings.neurips.cc/paper_files/paper/2023/file/9ee3ed2dd656402f954ef9dc37e39f48-Paper-Datasets_and_Benchmarks.pdf).

Makalede ülke/yıl kapsamının değişebildiği belirtilir. Hazır tehlike görevi
büyük yangınlara odaklıdır; buradaki 30 hektar kesimi ana projemize aktarılacak
bir eşik değildir. Başlangıç kayıtlarının MODIS/FIRMS kökeni ve EFFIS'in
uydu kökeni nedeniyle yeni kaynaktaki yokluk negatif etikete çevrilemez.
Bu pilot hedefi doğrulayacağını vaat etmez; ek olay alanı ve zaman bağlamının
ne kadar kullanılabilir olduğunu ölçmeyi amaçlar.

## Güncel erişim ve gerçek dosya başlıkları

[Yazar deposu](https://github.com/Orion-AI-Lab/mesogeos), veri küpünü ve
yardımcı dosyaları açık Drive klasörüne yönlendirir. Eski OVH/S3 yolu artık
desteklenmiyor. Zenodo 8036851 kaydı yazılım sürümüdür; 12 MB kod arşivi
büyük veri küpünün kendisi sanılmamalıdır.
[Zenodo kayıt türü ve kapsamı](https://zenodo.org/records/8036851).

Oturum açmadan kamuya açık kök ve alt klasör listeleri alındı. Ayrı
`burned_areas_shapefile` klasöründe aynı tabana ait beş üye var:

| Aşama | Üyeler | Bildirilen toplam bayt |
|---|---|---:|
| İlk tablo incelemesi | CPG, PRJ, DBF | 52.513.359 |
| İlk aşama ilgili kayıt verirse geometri | SHX, SHP | 107.309.200 |
| İki aşama toplamı | Beş üye | 159.822.559 |

Dosya boyutları iki açık liste alanında eşleşti. DBF/SHX/PRJ'den yalnız
1.755 bayt başlık okundu. 23.225 kayıtlık DBF bildirimi, indeks bildirimi
ve DBF'nin kayıt uzunluğu/boyut hesabı eşleşti. Bu sayı bütün kaynak dosyasının
bildirilen satır sayısıdır; dört ildeki veya bağımsız yangın sayısı değildir.
Tam dosya aktarımı ve gerçek olay içeriği henüz doğrulanmadı.

34 alanın şemasında `YEAR`, `IGNITION_D`, `ACQ_DATE`, `ACQ_TIME`,
`LATITUDE`, `LONGITUDE` ve `geometry_h` bulunur. Alanın var olması dolu,
doğru veya doğru anlamda kullanılmış olduğu demek değildir. Değerler pilotta
kontrol edilecektir. Nokta alanı ile nihai çokgen ayrı tutulacaktır.

## Yakalanan iki somut uyumsuzluk

**Tarih:** yayımlanmış `sample_positives.ipynb`, `IGNITION_D` alanından
bir gün çıkarır. Aynı kod ham tarih için 30 Eylül 2022'ye kadar filtre
kullanır. Veri küpünün yayımlanan son günü 29 Eylül'dür. Dolayısıyla hazır
öğrenme ekseni veya ham olay tarihi bizim UTC hücre–gün anahtarına doğrudan
kopyalanamaz. Ham alanlar korunacak; hazır eksi bir gün dönüşümü projemize
uygulanmayacaktır. [Sabit kod sürümü](https://github.com/Orion-AI-Lab/mesogeos/blob/828db48231637884a3fde5795760e42338cf780c/ml_tracks/a.fire_danger/dataset-extraction/sample_positives.ipynb).

NASA, MODIS `Acq_Time` alanını UTC geçiş zamanı olarak tanımlar. Ancak bu
dosyadaki alanların gerçekten korunmuş FIRMS değerleri olduğu satır bazında
incelenmeden UTC eşlemesi kabul edilmez. [NASA alan tanımı](https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_MODIS_Firehotspots.html).

**Konum:** ayrı vektörün PRJ tanımı EPSG:5643'tür, coğrafi derece değildir.
Yazarın kodu da WKT nokta geometrisine 5643 atayıp 4326'ya dönüştürür.
Dosyaya doğrudan 4326 atamak yanlış konum üretir. Nokta, lat/lon alanları
ve çokgenin sayısal tutarlılığı görülmeden zorunlu bir eşleşme yapılmaz.
Bu bulgular yalnız şema, koordinat tanımı ve kod incelemesine dayanır.

## Mevcut takvimde potansiyel destek

Yayımlanan dikdörtgen kapsam dört il AOI geometrisini içerir. Bu, kaynakta
bu illerin bütün olaylarının bulunduğu anlamına gelmez. İki olası üst tarih
yalnız mevcut 2022 metadata takvimine uygulanarak hazırlık sayısı elde edildi:

| Yerel takvim ölçüsü | 29 Eylül dahil | 30 Eylül dahil |
|---|---:|---:|
| Mersin 81 kaynak gününden tarihe kadar olan | 64 | 65 |
| Bunların 65 ana kaliteye uygun gün içindeki sayısı | 51 | 52 |
| Dört il 6.573 takvim satırından tarihe kadar olan | 4.574 | 4.594 |
| Ayrı Mersin 2.383 takvim satırından tarihe kadar olan | 1.881 | 1.894 |

Bu sayılar yeni kaynakla olay eşleşmesi veya değerlendirme başarımı değildir.
Tarih ekseni belirsizliğini görünür tutar. Sonbaharın kalan kısmının veya
2018–2022'nin tamamının yeni kaynakta kapsandığı ileri sürülmez.

## Hazırlanan öneri ve durma koşulları

Önerilen A, bu kaynağı yalnız yardımcı uydu kanıtı incelemesine almaktır.
İlk aşamada yaklaşık 53 MB tablo/koordinat tanımı edinilir. Ham kayıtların
yalnız yıl metadata'sı incelenip izinli 2018–2022 alanına girenler süzülmeden
diğer bilimsel alanlar veya geometriler çözülmez. `YEAR` ve `IGNITION_D`
yıl kısmı birlikte izinli olmalıdır; diğer yıllar opak tutulur. Kimlik,
kapsam, alan doluluğu, saat/tarih ve nokta tutarlılığı incelenir. İlgili kayıt
bulunursa, ikinci aşamada çokgenler alınarak aynı izinli kayıtlardaki alan
bağlamı incelenir. Yeni kaynaktan gerçek Y, kabul edilmiş L veya negatif
etiket atanmaz; bu kabul için ayrı kanıt gerekir.

Plan yerelde toplam 170 milyon bayt ve 900 saniye sınırı, dosya başına
bir deneme içerir. Aktarım boyutu/kimliği, şema veya kodlama uyuşmazlığında,
giriş/indirme onay sayfasında ya da ilk aşamada uygun kayıt bulunmadığında
durulur; dosyalar korunur. İlk başlık denemesinde büyük geometri başlığı
tamamlanmadı; küçük indeks/DBF/PRJ yolu ile metadata kontrolü tamamlandı.
Tam geometri indirmesinin çalıştığı varsayılmamıştır.

Alternatif B, bu yeni kaynak pilotunu açmamaktır; mevcut deneysel paket ve
bilimsel sınırlar korunur. A önerisi daha fazla bağlam sağlayabilir, fakat
bağımsız gerçek yangın doğrulamasını garanti etmez. İki yol da yeni eğitim,
2023–2025 bilimsel değerlerini açma, risk rengi veya final merge kararı değildir.
Yöntem kapsamındaki yeni kaynak seçimi araştırmacıya sunulacaktır.

## Denetim ve iz

14 yeni metadata/kapsam davranış kontrolü, referans hazırlığı ve nihai
birleştirme kapısıyla birlikte **43 ilgili test** geçti. Ayrı denetim,
19 hazırlık girdisinin hash'ini, 34 alanı, satır/indeks bildirimi ve dosya
boyutunu, sekiz tarih destek sayısını ve önerinin yürütülmemiş durumunu
geri doğruladı. Yayımlanmış üç küçük kod dosyası sabit Git commit'indeki
blob SHA'larıyla eşleşti; üçüncü taraf kod çalıştırılmadı.

Hazırlık: `mesogeos_reference_preparation_v1/20261124T224948Z_e1def508`.
Makbuz SHA-256:
`cd8ad5fd5517bdd7f698e33d26c8ac41ee70449d4004733eb36e1578ba691bd3`.

Ayrı audit: `mesogeos_reference_preparation_audit_v1/20261124T225146Z_5ae84eea`.
SHA-256:
`de8b848e7f46094b082114697d6fcfb2285670846b64531b8040b8d5079c2ac7`.

Yollar `outputs/reports/dataset` altındadır. Kimlikler UTC nedeniyle
24 Kasım ile başlar; Türkiye'deki çalışma/yorum tarihi 25 Kasım'dır.
Önceki veri/model/arayüz/rapor sürümleri değiştirilmedi. İlk tamamlanmayan
başlık sorgusu ve biçim/denetim ara sürümleri kabul edilmeden korundu.
