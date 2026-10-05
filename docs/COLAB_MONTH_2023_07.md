# Temmuz 2023 aylık Colab işi

Kullanıcı yaklaşık dokuz saatlik aylık grubu seçti ve Drive'da 1,5 TB boş alan
bildirdi. Kullanıcı işi tamamladı; **31 günlük küçük sonuç ZIP'i yerel
tablo/kaynak/zaman denetiminden geçti**. Resmî FIRMS boşluğuyla örtüşen
61 termal kayıt farkı ayrıca raporlandı.
[Gerçek sonuçlar ve sınırlar](COLAB_MONTH_RESULTS_2023_07.md).

## Çalıştırma

1. `outputs/cloud_month/l2_month_2023_07.ipynb` dosyasını Colab'a yükle.
2. Ücretsiz CPU ve Python 3.12 seç. Önceki notebook yerine bu notebook'u aç;
   eski kurulum sistem paketlerini değiştirdiyse yeni çalışma zamanı kullan.
3. Hücreleri sırayla çalıştır. Paket seçimi isteyen hücreye yalnızca
   `outputs/cloud_month/l2_month_2023_07_bundle.zip` dosyasını yükle.
4. Drive erişimini onayla, NASA kullanıcı adı/parolanı gizli istemlere gir.
   Uzun işlem hücresi 264 yeni çifti tek çalıştırmada sırayla işler.
5. Tamamlanınca sonraki hücre Drive'ı yeniden bağlayıp 31 günlük kaydı doğrular.
   Son hücre `l2_month_2023_07_results.zip` dosyasını indirir. Dosyayı yerelde
   `outputs/cloud_month/received/` klasörüne koy. Sonrasında bağımsız denetim yapılır.

Sekme açık, bilgisayar uyanık kalsın. Sürekli tıklamak gerekmez. Yaklaşık dokuz
saat önceki altı çiftin ölçümünden hesaplandı; kurulum, günlük birleşim ve kalıcı
kayıt ek süre getirir. Ücretsiz Colab'ın süre/erişim sınırları değişkendir;
tek oturumda bitirme garantisi yok. [Resmî Colab açıklaması](https://research.google.com/colaboratory/faq.html).

## Kapsam ve depolama

| Konu | Seçilen kapsam |
|---|---|
| Dönem | 1–31 Temmuz 2023, eğitim dönemi |
| Hazır gün | 16 Temmuz; doğrulanmış altı çiftin sonucu yeniden kullanılır |
| Yeni iş | 264 çift / 528 kaynak; iki sensör |
| Ham toplam transfer | 48.301.330.714 bayt, yalnızca Colab'a |
| Paket | Yaklaşık 24,81 MB; kod, sınırlar, metadata ve hazır gün sonucu |
| Geçici alan | Ham çiftler sırayla; bütün 48,30 GB aynı anda tutulmaz |
| Drive | Ayrı çift denetim paketleri ve günlük küçük tablolar |
| İşe özel sınır | 20 GB; toplam Drive kapasitesini temsil etmez |
| Yerel sonuç | Geometri yerine günlük CSV'ler ve kaynak denetim raporları |

Drive yolu:
`MyDrive/wildfire-risk-prediction/colab_checkpoints/month_2023_07/`.
Tam geometri çift denetim paketlerinde korunur. Bu işi başlatırken yerel
bilgisayara 48 GB veya 3 TB arşiv indirmek gerekmiyor. Diğer eğitim ayları
bu paketin kapsamına dahil değil; sonraki büyük gruplar ölçüme göre seçilecek.

## Kesintiden sonra devam

Aynı notebook ve aynı paketle yeni Colab oturumunda hücreleri tekrar çalıştır.
Tamamlanmış günler günlük kayıtlarından alınır. Yarım günün tamamlanmış
çiftleri ayrı denetim kayıtlarından alınır; bunlar yeniden indirilmez.
Henüz kaydedilmemiş çiftin işi tekrar gerekebilir. Oturumu yeniden başlatmak
kullanıcının işlemidir; kod otomatik Colab oturumu açmaz.

Kayıt akışı: ZIP kopyala → SHA/CRC ve sayısal geri okuma → tamamlanma kaydı
yaz → Colab'daki ham çifti temizle. Bozuk/sürümü farklı kayıt işlemi durdurur.
Drive'daki önceki kayıtları elle silme veya farklı paketlerle karıştırma.
Kesintide son hücre varsa kısmi sonuç ZIP'ini de indirebilir; kısmi çıktı
tam ay olarak kabul edilmez. Paket SHA'sı notebook içinde sabittir; işe
başladıktan sonra paketi yeniden üretmek yerine aynı dosyayı sakla.

## Kontroller ve bilimsel sınırlar

528 public CMR metadata dosyası ürün/üretici kimliği, sürüm, zaman, veri URL'si
ve boyut açısından denetlendi. İş sırasında indirilen kaynaklar ayrıca boyut,
varsa CMR checksum, native girdi eşleşmesi, sınıf/QA, coğrafya ve tarama
saatleri açısından denetlenir. Çakışan alanlar geometrik olarak birleştirilir;
alan toplamı kullanılmaz. Her günlük tabloda 2.899 hücre vardır.

Hazır altı çiftle günlük birleşim tüm hücreler/üç sınıfta ayrı ikili geometri
birleşimiyle kontrol edildi; en büyük fark yaklaşık 0,0000096 m². Bütün zaman
sütunları önceki doğrulanmış günlük sonuçla uyuştu. Günlük ZIP yaklaşık
0,514 MB oldu; aylık boyut için tek gün ölçümü kesin garanti değildir.
Aylık paketle hazır günün kaydı ve yeni klasöre geri yükleme de yerel provadan
geçirildi. Yerel prova gerçek Drive sunucusunu veya 264 yeni çifti sınamaz.

Yaklaşık piksel iç alanları fiziksel/sertifikalı uydu ayak izi değildir.
Uzamsal birleşim nominal tarihteki granülleri içerir; UTC sınırını kesen
taramalar ayrıca belirsiz tutulur. Zaman metriklerinde yalnızca tamamen
`(T,T+24h]` içinde kalan merkez tarama zarfları kullanılır. Zarflar sürekli
gözlem anlamına gelmez. Günlük durum `unknown`, negatif etiket izni `false`
kalır; nihai olay kataloğu, günlük etiket veya model üretilmez.

Gelen sonuç kontrolü:

```powershell
.\.venv\Scripts\python.exe scripts/cloud/verify_l2_month_results.py outputs/cloud_month/received/l2_month_2023_07_results.zip
```

Eksik aya bakmak için açıkça `--allow-partial` gerekir. Yerel denetim paket
sürümünü, anahtar/kapsamı, kaynak izlerini, sayısal alan sınırlarını, sınıf
sayımlarını ve bağımsız zaman birleşim/boşluk hesabını kontrol eder. Küçük
ZIP'te tam geometri olmadığı için bütün ayın alanlarını sıfırdan geometriyle
yeniden hesapladığını veya uzak Drive kaydını bağımsız kanıtladığını iddia etmez.
