# Colab yaz kontrolü — seçilen B kapsamı

> Dönemsel uygulama kaydı. Kurulum, maliyet ve bekleyen iş ifadeleri belgenin
> ilgili çalışma aşamasına aittir. Güncel durum [STATUS.md](STATUS.md), mevcut
> üretim yolu [devam rehberinde](GCP_SOURCE_AWARE_CONTINUATION_2026-10-09.md) izlenir.

5 Ekim'de B seçeneğini seçtim: **16 Temmuz 2023, S-NPP ve NOAA-20,
altı dosya çifti / 12 kaynak dosyası**. CMR metadatasıyla doğrulanan toplam
1.097.404.203 bayt; en büyük kaynak çifti 187.472.929 bayt. Hazırlık paketi
yaklaşık 2,95 MB. Yaz ham kaynakları yerel bilgisayara indirilmedi.
Gerçek Colab işi tamamlandı; altı çift yerel sonuç denetiminden geçti.
[Sonuç ve sonraki seçenekler](COLAB_SUMMER_RESULTS_2026-10-05.md).

## Çalıştırma

1. Colab'da **Dosya → Not defteri yükle** ile
   `outputs/cloud_summer/l2_summer_B.ipynb` dosyasını aç.
2. **CPU ve Python 3.12** çalışma zamanını kullan; GPU gerekmiyor.
3. Hücreleri sırayla çalıştır. Paket yükleme hücresinde yalnızca
   `outputs/cloud_summer/l2_summer_B_bundle.zip` seç.
4. Drive'ı kendi Google hesabına bağla. NASA kullanıcı adı/parolasını yalnızca
   gizli istemlere yaz. Tek işlem hücresi altı çifti sırayla işler.
5. Sonraki hücre Drive yazılarını eşitler ve yeniden bağladıktan sonra altı
   kaydı tekrar denetler. Son hücre `l2_summer_results.zip` dosyasını indirir.
6. Sonucu `outputs/cloud_summer/received/` altında sakla ve kontrol için bildir.

Oturum kesilirse aynı notebook/paketle yeniden çalıştır. Tamamlanma kaydı
olan çiftler Drive'dan doğrulanarak geri yüklenir; yeniden indirilmez.
Kaydetme başarısız olduğunda o ham çift temizlenmez. Başka paket sürümüne
ait veya bozulmuş kayıtlar otomatik kabul edilmez; hata çıktısıyla inceleme
yapılır. Dosya/metadata eşleşmesi hatası alınırsa dosya adını değiştirerek
veya kalite kuralını gevşeterek devam edilmez.

Drive klasörü:
`MyDrive/wildfire-risk-prediction/colab_checkpoints/summer_B/<manifest SHA>/`.
Her çiftin ayrı sonuç ZIP'i ve son yazılan tamamlanma kaydı var. Ham arşiv
Drive'a yüklenmez; sonuç boyutu yeni yaz işi bitince ölçülecek. Önceki
Drive/kış pilotlarının kayıtları değiştirilmez.

## Neden sırayla işliyoruz; daha büyük grup mümkün mü?

Parça, sistemin bellek/geçici disk kullanımını sınırlayan bir kaynak çifti.
Grup, tek çalıştırmanın otomatik tamamladığı çiftler listesi. Bu denemede bir
grup altı çift; altı ayrı komut çalıştırmak gerekmiyor.

Deneme doğrulandıktan sonra hafta/ay grupları planlanabilir. Büyük grupta da
birer çift işlemek ve her çiftte kayıt almak, ham dosyaları aynı anda diskte
tutmadan ilerlemeyi sağlar. Grup büyümesi tek oturumun süresini, toplam
internet trafiğini ve kalıcı sonuç boyutunu artırır. Dolayısıyla B sonucundaki
süre/bellek/disk/çıktı ölçümleri görülmeden tam dönem grubu seçilmedi.

2018–2023 eğitim dönemi 72 takvim ayı. Aylık gruplama seçilse 72 mantıksal
grup olur; bunun 72 elle çalıştırma olması gerekmez. Mevcut eğitim kataloğunda
18.711 nominal çift var; bazı kayıtlar eşleşmemiş olduğundan bu sayı kesin
üretim iş sayısı değil. Yaklaşık 3,17 TiB tam kaynak hacmi toplu diskte tutma
zorunluluğu olmadan işlenebilir; sırayla işleme aynı kaynaklar tamamen
indirilecekse toplam transferi azaltmaz. Tam dönem kapsamı ve gözlem kuralı
açık; hiçbir aylık/tam dönem iş otomatik başlatılmadı.

## Yapılan kontroller ve sınırlar

Yeni işleyici eski doğrulanmış kış dosyalarını/kodunu değiştirmiyor. Aynı
doğal HDF5 sınıf/QA denetimi, tarama içi merkezlerden türetilen yaklaşık alan
ve doğal tarama zamanı yordamlarını kullanıyor. Kaynak CMR boyutu, varsa
sağlayıcı checksum'u, gerçek geolocation InputPointer ve doğal dizi yönü
kontrol ediliyor. Veri indirilince yeni kaynak SHA'ları kaydedilecek.

Her çiftte 2.899 hücre korunur. Bağımsız doğal tarama sayımları ilk sınıf/QA
CSV'siyle karşılaştırılır; kayıtlı GPKG geometrisinin alanı ve CSV oranı geri
okunur. UTC tarama zamanları, yörünge ve kalite alanları saklanır. Kayıt ZIP'i
SHA/CRC, kod/manifest kimliği ve tekrar geri yüklemeyle doğrulanır. Kayıt
başarısından sonra yalnızca o işin listelenmiş geçici ham dosyaları temizlenir.

Yerel prova, mevcut kış ham kaynaklarıyla sıfır merkezli S-NPP parçası ve
35.394 merkezli NOAA-20 parçasında doğal denetim/alan/tarama, sonuç kaydı ve
yeni sonuç dizinine geri yüklemeyi geçti. Ham kaynaklar değişmedi. Bu,
yerel dosya sistemi provası; yeni yaz işi veya yeni gerçek Drive kaydı değil.

Yeni yaz dosyaları için henüz donmuş yerel ham referans yok. Bu nedenle
yerel referansla birebir ham karşılaştırması iddia edilmiyor; CMR/native
kontroller ve yeni çıktı tutarlılığı uygulanıyor. Tam yaz sonucu geldiğinde
ayrıca yerel bağımsız geri okuma yapılacak:

```powershell
.\.venv\Scripts\python.exe scripts/cloud/verify_l2_summer_results.py outputs/cloud_summer/received/l2_summer_results.zip
```

Bu kontrol nihai etiket/model üretmez. Günlük gözlem `unknown`, negatif izin
`false`. Yaklaşık merkez geometrisi resmî fiziksel ayak izi değil; tarama
zaman zarfı sürekli gözlem süresi değil. Önceki 679 erken NOAA-20 eşleşmesi
ve NASA Type teyidi açık. Bu gün bütün yaz/bulut koşullarını temsil etmez.

Yeniden hazırlamak: `scripts/cloud/build_l2_summer_bundle.py`. Yalnızca
seçilen 12 kaynağın kamuya açık UMM metadatasını alır; NASA giriş bilgisi veya
ham uydu indirmesi gerektirmez. Paket hazırlandıktan sonra kod değişirse
paket yeniden hazırlanmalı; eski ve yeni sürüm sonuçları birleştirilmemeli.
