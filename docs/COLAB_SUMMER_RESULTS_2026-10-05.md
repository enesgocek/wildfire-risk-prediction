# B yaz kontrolü sonucu — 5 Ekim 2026

Kullanıcı bütün hücreleri yaklaşık 15 dakikada çalıştırdı ve sonucu
`outputs/cloud_summer/received/l2_summer_results.zip` altına koydu.
**Altı çiftin tamamı yerel sonuç denetiminden geçti.**

| Ölçüm | Sonuç |
| --- | ---: |
| Eğitim günü / kaynak | 16 Temmuz 2023 / iki sensör, 6 çift, 12 dosya |
| Colab'a başarılı ham transfer | 1,10 GB |
| Gelen sonuç ZIP'i | 21,34 MB |
| Çiftlerin indirme/işleme/ilk denetim süre toplamı | 754,54 saniye — 12,58 dakika |
| En yüksek çocuk süreç RSS | Yaklaşık 704 MB |
| En yüksek örneklenen disk artışı | Yaklaşık 200 MB |
| Hücre / hücre-çift satırı | 2.899 / 17.394 |
| Hücre-tarama / bütün tarama satırı | 29.379 / 1.211 |
| Sensör/yörünge kimliği | 6 |

12,58 dakika ortam kurulumu, kalıcı kayıt ve özet ZIP üretimini kapsamıyor.
Yaklaşık 15 dakika kullanıcının bildirimi; bağımsız tam süre ölçümü değil.
Disk ölçümü 0,2 saniye örneklemeli; ortamın kesin toplam tepe alanı değil.

## Denetimin kapsamı

Paket/kod/manifest ve çıktı SHA, ZIP CRC/üye listesi, kaynak boyutu/metadata,
Python/paket sürümleri ve bütün hücre anahtarları doğrulandı. Sınıf/QA
CSV'leri bağımsız doğal tarama sayımlarıyla; kayıtlı geometrilerin alan ve
oranları geri okunan GPKG ile eşleşti.

FIRMS'ın n/h güvenli 46 termal tespiti altı çiftin doğal yangın sınıflarıyla
**güven sınıfı ve 5 km hücre bazında tam eşleşti**: 43 nominal, 3 yüksek
güvenli kayıt. Bu tek tek koordinat eşleşmesi veya 46 bağımsız bitki yangını
kanıtı değil. Type 0/2 kayıtları korunuyor; NASA teyidi açık.

Günlük merkez zaman tanısı oluşturuldu. 11.596 zaman değeri bağımsız
olay-süpürme hesabıyla geçti. Uygun kara merkezi bulunan 2.866 hücrenin en
uzun tarama zarfı boşluğu medyanı 11,494 saat; 33 hücrede bu merkez grubu
yok. Bunlar sürekli gözlem, fiziksel alan veya yangının yokluğu kanıtı değil.

Son özette yeni işlem 0 / yeniden kullanılan kayıt 6 var; notebook'un son
verify-only akışıyla uyumlu. ZIP tek başına uzak Drive yeniden bağlamasını
bağımsız kanıtlamıyor. Yaz ham dosyaları yerelde yok; birebir yerel ham
referans karşılaştırması yapılmadı. CMR/native ve çıktı tutarlılığı uygulandı.
Günlük gözlem `unknown`, negatif izin `false`; nihai etiket/model yok.

Yerel raporlar `outputs/reports/observation_coverage/` altında:
`colab_summer_received_verification.json`, `colab_summer_completed_diagnostics.json`
ve `summer_control_2023-07-16_daily_center_diagnostics.csv`. Veriler/çıktılar
Git kapsamı dışında; kaynak ve donmuş Colab paketi değiştirilmedi.

## Büyük gruplar için sonraki seçenekler

Seçilen altı kaynakta çalışma alanındaki bulut sınıfı merkezi sayısı sıfır.
Bu, bütün gün/hava durumu için bulutsuzluk kanıtı değil. Önceki kış gününde
bulut vardı; iki gün bütün dönem gözlem kuralını kesinleştirmek için yeterli değil.

21,34 MB sonucun yaklaşık 20,39 MB'ı GPKG çizimleri; diğer üyelerin sıkıştırılmış
içeriği toplam 0,93 MB. Bu, henüz hazır bir 0,93 MB üretim ZIP'i değil.
Günlük alan hesabında çakışan geometriler önce birleştirilmeli; çiftlerin alanları
doğrudan toplanamaz. Geometrileri mevcut checkpoint'ten silmek kayıt sözleşmesini
bozar. Üretimde hangi günlük sonuçları tutacağımızı belirleyip eşdeğerliği
denetlemeden mevcut çıktıları kırpmayacağız.

| Yol | İlave kapsam | Tahmini yeni ham transfer |
| --- | --- | ---: |
| Günlük birleşim ve kompakt üretim formatı — öneri | Mevcut sonuçlarla tasarım/denetim | 0 GB |
| Ek yaz kontrolü | 18 Ağustos 2018 ve 31 Temmuz 2021; 16 yeni çift | 2,93 GB |
| Haftalık kapasite kontrolü | 13–19 Temmuz 2023; tamamlanan B dışında 56 yeni çift | 10,25 GB |

İki indirme seçeneğinin bulut çeşitliliği katalogdan doğrulanmış değil.
Temmuz 2023'ün tüm katalog kapsamı 270 çift/49,40 GB; B dışında 264 çift/48,30 GB.
Büyük gruplar süre/kalıcı çıktı boyutunu artırır; birer çift işleyerek geçici
ham disk kullanımı sınırlanabilir. Transferler katalog tahmini; B'nin kaynak
boyutu UMM ile doğrulandı. Yeni grup/nihai etiket eşiği seçilmedi, indirme
başlatılmadı. Kullanıcının 27 GB ek yerel disk sınırı korunuyor.
