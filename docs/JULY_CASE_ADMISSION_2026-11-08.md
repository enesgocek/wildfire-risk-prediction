# Menderes ve Anamur için hedef kabul karşılaştırması — 8 Kasım 2026

İki Temmuz 2023 vakasının beş ısıl tespitli 5 km hücre-günü,
aynı `(T,T+24 saat]` UTC kuralıyla karşılaştırıldı. Menderes'teki
seçili tespitlerin dokuz keşif ayarındaki tam küme üyelikleri
okundu. Menderes EFFIS poligonu ve Anamur Sentinel-2 değişim
parçası eşit alan projeksiyonunda proje hücreleriyle kesiştirildi.
İki geometri farklı kaynak ve yöntemlere aittir.
[Menderes örtü ve saha kaydı](MENDERES_PATCH_CONTEXT_2026-11-08.md) ·
[Anamur UTC pencereleri](ANAMUR_OBSERVATION_WINDOWS_2026-11-08.md) ·
[Hedef kabul sözleşmesi](TARGET_ADMISSION_REVIEW_2026-10-10.md).

## Isıl tespit, ilk aday ve etkilenen hücre

| Seçili grup | Isıl tespit görülen hücre-günler, UTC | Dokuz ayarda aynı ilk uydu tespiti | Alan kanıtı |
| --- | --- | --- | --- |
| Menderes güney | 10 Temmuz, C524_R906'da 7 ve C524_R905'te 5 | 10 Temmuz 11.03, C524_R906 | EFFIS poligonunun 69,03 ha'sı C524_R906'da, 347,40 ha'sı C524_R905'te |
| Menderes kuzey | 10 Temmuz, C525_R906'da 2 | 10 Temmuz 11.54, C525_R906 | En büyük optik değişim parçası 0,15 eşiğinde 7,68 ha ve CORINE 2018'de tarım sınıfında. EFFIS kesişimi yok |
| Anamur Belensazak | C632_R864'te 10 Temmuz 3, 11 Temmuz 2 | 10 Temmuz 22.33, C632_R864 | 0,15 eşiğindeki optik parça eşit alan hesabıyla 5,68 ha ve tümü C632_R864'te |

Menderes'teki 12 güney ve 2 kuzey tespitinin oluşturduğu tam
bileşenlerde dokuz ayarın hiçbirinde ek üye veya daha erken
kayıt bulunmadı. Anamur'un kayıtlı tam kümesinde aynı beş
üye dokuz ayarda da korunuyor. İlk tespit zamanı kuralıyla
beş ısıl hücre-günden üçü ilk aday oluyor. Menderes güneyde
komşu hücrenin beş kaydı aynı gün saat 11.54'te, Anamur'un iki
geç kaydı ise ertesi UTC penceresinde. Bu iki hücre-gün
keşif gruplarının devam bağlamında tutuldu.

Menderes güneyde ilk aday hücre, haritalanan 416,43 ha'nın
yaklaşık %16,6'sını içeriyor. Yanık alanı en büyük hücreyi
başlangıç saymak bu örnekte hücreyi değiştirirdi. EFFIS'in
416 ha kaynak alanı ile 416,43 ha yerel geometri hesabı
ayrı kaydedildi. Anamur'da ilk aday hücre ve optik parça
aynı hücrede. Buna karşın yaklaşık Belensazak mevki
noktasının 1 km senaryosu iki hücreye uzanıyor. Bu
senaryo başlangıç konumunun ölçülmüş belirsizliği sayılmadı.
[EFFIS yöntem sınırı](https://forest-fire.emergency.copernicus.eu/about-effis/technical-background/rapid-damage-assessment) ·
[Anamur konum duyarlılığı](JULY_2023_START_CONTEXT_2026-11-08.md).

## Her vaka için açık kabul koşulu

| İnceleme birimi | Mevcut saha bağlamı | Kabul için gereken ek dayanak |
| --- | --- | --- |
| Menderes güney | İzmir OBM 10 Temmuz'da Oğlananası'nda orman yangını bildiriyor. Yayınlanan yaklaşık saat ve ekip çıkışı, ilk uydu tespitiyle aynı UTC hedef gününde. | Olaya bağlanabilen özgün başlangıç konumu veya belgelenmiş konum belirsizliği, başlangıç zamanının anlamı ve ilk örtü. Bunlar ilk hücre ve pencereyi sınamak için gerekli. |
| Menderes kuzey | Tarımsal bağlam ve ayrı ısıl grup var. Taranan saha kayıtları bu parçaya konumuyla bağlanmadı. | Önce ayrı bir yangın kaydıyla veya Menderes olayının devamına ilişkin konumlu kanıtla ilişki kurulması gerekir. Başlangıç ve örtü değerlendirmesi bu ilişki kurulursa yapılabilir. |
| Anamur Belensazak | OGM yaklaşık 01.30 Türkiye saati (10 Temmuz 22.30 UTC) ve 4,45 ha meyve bahçesi ile 0,70 ha orman hasarı bildiriyor. İlk seçili uydu dakikası 22.33 UTC. | Gerçek başlangıç konumu veya belgelenmiş belirsizliği, saat aralığının dayanağı ve tutuşmanın ilk örtüsü. Üç dakikalık fark algılama gecikmesi olarak kullanılmadı. |

Kurum anlatıları vaka bağlamını, EFFIS ve optik değişim etki
alanını, VIIRS ise kayıtlı ısıl tespitleri destekliyor.
Beş hücre-günün hedefi boş kaldı. Gözlem durumu `unknown`,
pozitif ve negatif izinler kapalı. Üç ilk aday, veri
setine kabul edilen olay sayısı olarak kullanılmaz.
İki seçili vakadan olay sıklığı veya tespit oranı hesaplanmadı.
Yeni kanıt geldiğinde önce olay kaydının alım kontrolü ve
eşleştirmesi yapılır. Değerlendirme için il, dönem, olay
türü ve bilinen eksikleri kapsayan kayıt kapsamı ayrı koşuldur.
[İzmir OBM kaydı](https://www.ogm.gov.tr/izmirobm/haberler/sehidimiz-mustafa-gurpinar%E2%80%99i-torenle-ugurladik) ·
[Mersin OBM kaydı](https://www.ogm.gov.tr/mersinobm/haber-sitesi/Sayfalar/anamur%E2%80%99da-orman-yangini0712-2774.aspx) ·
[Bağımsız kaynak alımı](REFERENCE_INTAKE_2026-10-15.md).

## Yeniden üretim

Üretici `python scripts/quality/compare_july_case_admission.py`.
24 girdi kimliği, dokuz Menderes küme ayarı ve UTC pencere
anahtarları ayrı okumayla doğrulandı. Alan kesişimleri ikinci
geometri okuyucusuyla ve Anamur'un 142 piksellik parçası ayrı
bağlantı hesabıyla kontrol edildi. 128 ilgili test geçti.
Yerel makbuz
`outputs/reports/dataset/july_case_admission_v1/20261108T122815Z_6b4e98d6/readback.json`.
SHA-256 `ee5575a918833b4e28df2032c5a28f9f630177252bb8648c7c744a9ebd416b77`.
