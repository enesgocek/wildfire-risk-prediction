# Tek uydu geçişiyle ücretsiz bulut denemesi

> Dönemsel uygulama kaydı. Kurulum, maliyet ve bekleyen iş ifadeleri belgenin
> ilgili çalışma aşamasına aittir. Güncel durum [STATUS.md](STATUS.md), mevcut
> üretim yolu [devam rehberinde](GCP_SOURCE_AWARE_CONTINUATION_2026-10-09.md) izlenir.

İlk öneri Colab'ın ücretsiz CPU ortamında küçük deneme. Colab,
Google Cloud/Vertex, Claude ve Kaggle seçenekleri değerlendirildi.
Bu seçim tüm dönemin platformunu kesinleştirmez; ücretli kaynak oluşturulmaz.

| Seçenek | Bu aşamadaki değerlendirme |
| --- | --- |
| Colab | İlk girişli NASA/Python pilotu için öneri. Ücretsiz kaynaklar garanti değildir; tam dönem için kalıcı ilerleme kaydı gerekecek. |
| Kaggle | Alternatif Python ortamı. İnternet ayarı, oturum ve kayıtlı çıktı sınırları ayrıca kontrol edilmeli. |
| Google Cloud hesaplama / Workbench | Uzun işler ve ayarlanabilir disk için aday; hesaplama/depolama maliyeti ayrıca bütçelenecek. Cloud Console yönetim arayüzüdür. |
| Claude / Vertex model API'si | Kod yardımı sağlayabilir; ham uydu dizilerini işleyen disk/CPU ortamının yerine geçmez. |

Resmi kaynaklar: [Colab sınırları](https://research.google.com/colaboratory/faq.html),
[Kaggle notebook belgesi](https://www.kaggle.com/docs/notebooks),
[Google Cloud fiyatlandırma](https://cloud.google.com/pricing/list),
[Claude model API'si](https://cloud.google.com/vertex-ai/generative-ai/docs/partner-models/use-claude),
[Earthaccess erişimi](https://earthaccess.readthedocs.io/en/latest/api/).
Ortam önerisi bu projedeki küçük denetimin ihtiyacına dayalı değerlendirmedir.
Tam dönemin ücretsiz bir oturumda bitmesi veya sonuçların kota içine sığması
garanti edilmez. Kamuya açık Kaggle veri seti oluşturulmaz.

## Hazırlanan dosyalar

`scripts/cloud/build_l2_pilot_bundle.py` şu yerel dosyaları üretir:

- outputs/cloud_pilot/l2_pilot_isolated.ipynb
- outputs/cloud_pilot/l2_pilot_isolated_bundle.zip — yaklaşık 1,4 MB

Paketin açık dosya listesi yalnızca denetim kodu, dört ilin AOI/grid bilgisi,
iki CMR metadata kaydı ve yerel karşılaştırma sonuçlarını kapsar. Ham uydu,
meteoroloji, .env veya hesap bilgisi içermez. Notebook paket SHA'sını sınar.
Paket ve notebook aynı üretimden kullanılmalıdır; birisi yeniden üretildiyse
ikisi birlikte güncellenir.

Pilot yalnızca **13 Ocak 2019 01:00 UTC S-NPP** geçişini indirir: yangın
dosyası 994.759 bayt, konum dosyası 193.708.209 bayt. Toplam 194.702.968 bayt
Colab'ın geçici diskine gelir; yerel bilgisayara gelmez. Paket kurulumları
da Colab ortamındadır. Ücretsiz CPU ortamı kullanılmalı.

## Manuel kimlik doğrulama ve çalıştırma

1. [Colab](https://colab.research.google.com/) aç; Google hesabınla giriş yap.
2. Notebook yükleme bölümünde l2_pilot_isolated.ipynb dosyasını seç. Ücretsiz CPU
   çalışma ortamını kullan; ücretli/GPU seçeneklerine geçmek gerekmez.
3. Hücreleri sırayla çalıştır. Paket yükleme hücresi sorunca yalnızca
   l2_pilot_isolated_bundle.zip seç. Earthdata giriş istemine NASA hesabını yaz;
   parola koda veya sohbete yazılmaz. Kimlik bilgileri dosyaya kaydedilmez.
4. Başarıdan sonra son hücre l2_pilot_results.zip dosyasını bilgisayarına
   indirir. Bu dosyayı proje outputs/cloud_pilot içine koy; denetleyebiliriz.
   Bir hata olursa dur ve hata metnini paylaş; farklı ürün/tarih seçme.

Python 3.12 ortamı tercih edilir; seçilebilir sürümler için
[Colab çalışma ortamı sürümleri](https://research.google.com/colaboratory/runtime-version-faq.html).
Önceki notebook'un ilk hücresi Colab'ın hazır pandas/numpy/fsspec paketleriyle
çakıştı. O eski kurulumu çalıştırdıysan **çalışma zamanını silip temiz bir
çalışma zamanı aç**, sonra yeni notebook ve yeni ZIP'i birlikte kullan.
Yeni sürüm Colab sistem paketlerine kurulum yapmaz; ayrı venv içine 47 sabit
bağımlılık kurar. pip check ve HDF5 sürücü kontrolü NASA indirmesinden önce
çalışır. Python 3.12/Linux paket çözümleme denetimi ve 4 Ekim'deki gerçek
Colab çalıştırması geçti. HDF5 sürücüsü yoksa kod durur; farklı
dizi yönüne geçmez.

İşleme ayrı Python sürecinde yürür. Kullanıcı adı ve parola gizli istemle alınır,
yalnızca o alt sürecin ortamına aktarılır ve hata olsa da geçici sözlük temizlenir.
Kimlik bilgileri notebook koduna, komut argümanlarına veya sonuç ZIP'ine yazılmaz.
Yalıtım: [Python venv](https://docs.python.org/3/library/venv.html),
[pip --python](https://pip.pypa.io/en/stable/topics/python-option/).

## Denetimin kapsamı

`run_l2_pilot.py` iki dosyanın boyut/SHA'sını mevcut özgün kaynaklarla,
gerçek geolocation girdisini ve bütün seyrek yangın koordinatlarını kontrol eder.
Piksel sınıfları, QA sayımları, native dizi boyutları ve 2.899 hücrenin bütün
CSV sütunları yerel referansla tam karşılaştırılır. Sıfır merkezli hücreler de
korunur; günlük gözlem unknown ve negatif etiket izinleri false kalır.

Yerel paketten çalıştırmada 195 MB kaynak yaklaşık 0,21 MB sonuç verdi.
Bu, tek geçişteki merkez sayımlarının küçüldüğünü gösterir; tüm dönemin nihai
tablo boyutunu veya fiziksel gözlem alanı yönteminin doğruluğunu göstermez.
Colab girişli indirme ve Linux ortamı 4 Ekim'de doğrulandı. Pilot sonucu süre,
paket sürümleri ve disk önce/sonra değerlerini kaydeder; tepe RAM/disk ve toplam
protokol trafiği ölçümü değildir. Tam dönem planı için daha geniş örnek gerekir.

## 4 Ekim gerçek Colab sonucunun bağımsız kontrolü

Bütün hücreleri çalıştırdım. İndirilen `l2_pilot_results.zip` dosyası
24.472 bayt; yerel kopyası outputs/cloud_pilot/received altında tutuluyor.
`verify_l2_pilot_results.py` ZIP'i çıkartmadan veya içerikten kod çalıştırmadan
okudu. Dosya listesi/CRC, referans paket özetleri, kaynak ve çalışan kod kimliği,
tam QA raporu ve 2.899 hücrenin bütün CSV sütunları doğrulandı. Yalnızca çalışma
zamanı damgası ve kaynak dosya yollarının biçimi karşılaştırmada normalleştirildi.

Colab 194.702.968 bayt özgün uydu kaynağını indirip denetledi; indirme ve denetim
35,1 saniye sürdü. Ortam kurulumu bu süreye dahil değil. Python 3.12.13 ve
raporlanan yedi paket sürümü sabit sürümlerle eşleşti. Küçük sonuçta 127.668
pilot piksel merkezi ve üç nominal güvenli termal piksel korunuyor; bunlar
teyit edilmiş üç orman yangını anlamına gelmez. Günlük gözlem hâlâ unknown,
negatif etiket izni false.

Bağımsız rapor:
outputs/reports/observation_coverage/colab_pilot_received_verification.json.
Değiştirilmiş sayım/QA/kaynak, yanlış ortam/sürüm, negatif etiket izni ve
eksik/çift/fazladan ZIP dosyalarını reddeden 10 test geçti. Bu tek geçiş denemesi
bulut erişimini ve hesapların yeniden üretilebilirliğini doğruluyor; bütün
dönemin kapasitesi, tepe RAM/disk kullanımı veya fiziksel ayak izi doğruluğu
henüz doğrulanmış değil. Sonraki öneri, her iki sensörü içeren bir eğitim günü
üzerinde bellek/disk ve kesintiden devam ölçümü; henüz başlatılmadı.

Ham örnekler otomatik silinmez. Oturum sona erince Colab geçici dosyaları
kaybolabilir; küçük sonuç ZIP'i manuel olarak indirilmelidir.
