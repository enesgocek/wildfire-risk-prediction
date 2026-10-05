# Drive'da küçük sonuçların kalıcı saklanması — 5 Ekim 2026

Kullanıcı Google Drive'a otomatik kaydetmeyi seçti. İlk aşama, 4 Ekim'de
doğrulanmış sekiz geçişli sonucu Drive'a kopyalayıp yeni bağlantıda geri
okumak. Yeni ham uydu indirilmez; NASA parolası istenmez. Mevcut tek geçiş ve
günlük pilot paketleri değiştirilmedi; kaynak/etiket kuralları aynı kalıyor.

Terim notu: “sekiz geçiş” sekiz işlenen dosya parçasını ifade eder; 5 Ekim
yörünge denetiminde yedi farklı sensör/yörünge kaydı bulundu. Drive kayıt
birimi granule sonucu; bağımsız yeniden gözlem sayısıyla karıştırılmaz.
[Zaman denetimi](OBSERVATION_TIMING_2026-10-05.md).

## Kullanıcının yapacağı deneme

Dosyalar outputs/cloud_drive altında:

1. l2_drive_storage.ipynb dosyasını Colab'a yükle. Python 3.12 / ücretsiz CPU
   kullan; önceki yalıtılmış ortam varsa tekrar kullanılabilir.
2. Hücreleri sırayla çalıştır. Paket sorulduğunda yalnızca l2_drive_bundle.zip
   seç. Paket yaklaşık 1,79 MB ve dünün doğrulanmış 198 KB sonucunu içeriyor.
3. Google Drive bağlantısına kendi hesabınla onay ver. Notebook'un kullandığı
   klasör: MyDrive/wildfire-risk-prediction/colab_checkpoints.
4. Sonraki hücre Drive yazılarını eşitleyip bağlantıyı kapatır ve yeniden
   bağlar. Google tekrar onay isteyebilir. Kopyalanmış ZIP ve sekiz geçişin
   tüm QA/CSV sonuçları tekrar doğrulanır.
5. Son hücre l2_drive_proof.zip indirir. Bu küçük paketi sakla ve tamamlandığını
   bildir; sonuç bağımsız olarak denetlenecek.

Google'ın verdiği Drive izni notebook koduna teknik olarak geniş Drive erişimi
sağlar; bizim kod yalnızca belirtilen proje klasöründeki kendi kayıtlarını
okur/yazar. Klasör paylaşılmaz; kişisel dosyalar taranmaz veya silinmez.
[Colab resmi Drive açıklaması](https://research.google.com/colaboratory/faq.html#drive-timeout).

## Kayıt düzeni

Her ZIP, içerik SHA256'sını taşıyan yeni bir dosya adıyla saklanır. Yerel ZIP
taşınmaz; kopyalanır. Önce kopya SHA ile geri okunur ve bütün checkpoint/QA/CSV
sonuçları yeniden denetlenir. Sonra tamamlanma kaydı yazılır. Eski doğrulanmış
ZIP'ler üzerine yazılmaz. Yarım .pending dosyaları devam adayı sayılmaz.
Tamamlanma kaydı veya ZIP bozulmuşsa işlem durur; sessizce eski sonuca geçmez.
Yeni oturum, kendi iş manifestinin klasöründeki doğrulanmış kaydı yerel geçici
diske alır. Otomatik eski sürüm silme yapılmaz; aynı iş için tek Colab oturumu
kullanılmalıdır.

Üretim işleyicisine bağlanabilen kayıt kancası da eklendi: yerel sonuç ZIP'i
üretildikten sonra Drive kopyası/geri okuması başarılı olmadan kontrol ham
temizleme adımına dönmez. Depolama/kota hatasında yerel checkpoint ve ham çift
korunur. Bu notebook sadece mevcut tamamlanmış sonucu kullanır; tüm dönem veya
yeni gün işleme döngüsünü başlatmaz.

Drive dosya sistemi geri okuması tek başına sunucuya kalıcı yazımı kanıtlamaz.
Bu nedenle denemede Google'ın flush_and_unmount işleviyle bekleyen yazılar
eşitlenip bağlantı yeniden kurulur; ikinci geri okuma ayrıca raporlanır.
Uzun işler için senkronizasyon ve kesinti aralığı bu denemeden sonra planlanacak.
[Google'ın Drive entegrasyon kodu](https://github.com/googlecolab/colabtools/blob/main/google/colab/drive.py).

Google çok sayıda küçük Drive işlemi yerine ZIP gibi arşivlerin yerelde
işlenmesini öneriyor. Kaynak dizileri Colab diskinde işlenecek; Drive'a küçük
checkpoint ZIP'leri gidecek. Boş Drive kotası henüz bilinmiyor; bu pilot
yaklaşık 200 KB saklar. Tam dönem için kota ve nihai alan/zaman çıktılarının
boyutu ayrıca ölçülecek. Drive satın alma veya ücretli hizmet açılmadı.
[Drive sınırları](https://research.google.com/colaboratory/faq.html).

## Denetim

```powershell
.\.venv\Scripts\python.exe scripts/cloud/verify_l2_drive_proof.py outputs/cloud_drive/received/l2_drive_proof.zip
```

Rapor: outputs/reports/observation_coverage/drive_storage_received_verification.json.
Yerel prova açıkça ayrı raporlanır ve Drive bağlantısı doğrulanmış sayılmaz.
Yerel kaydetme/geri yükleme provası bütün sekiz geçişle geçti. Tamamlanmamış
yayın, bozuk içerik/kayıt, yanlış klasör, kota/aktarımı kesilme ve ham temizliği
öncesindeki depolama hata kapısı için koruyucu testler eklendi. Gerçek Drive
bağlantısı ve yeniden bağlama sonucu aşağıdaki gerçek denemeyle doğrulandı.
16 yeni testle tam kümede 226 test başarılı; kod/biçim, notebook ve paket
kontrolleri geçti. Yerel rapor:
outputs/reports/observation_coverage/drive_storage_local_rehearsal.json.

5 Ekim'de gerçek Colab sonucu bağımsız doğrulamadan geçti. İndirilen kanıt
ZIP'i 187.959 bayt; SHA256:
`2df1829722dae4471ca92721e9328d41c89a6658820053e812d6b742b2b95342`.
Ortam `mounted_google_drive`, yeniden bağlama kontrolü true. Drive'a saklanan
197.607 baytlık sonuçtan sekiz çiftin bütün QA raporları ve 23.192 hücre/geçiş
satırının tüm sütunları referanslarla eşleşti. Paket/kod/manifest kimliği,
tamamlanma kaydı, içerik özetleri ve proje klasörü de denetlendi. Yeni ham
indirme veya Drive'a ham arşiv yükleme yapılmadı. Kaynak indirme dosyası
korunarak `outputs/cloud_drive/received/` içine özet adlı kopya alındı.

Bu, mevcut küçük sonucun eşitleme ve yeniden bağlama sonrasında geri
yüklenmesini doğrular. Tam dönem işinin her geçişi sırasında kesinti,
Drive kota kapasitesi ve sunucu tarafında uzun vadeli saklama garantisi
bu denemeyle kanıtlanmış sayılmaz. Sıradaki alan yöntemi kontrolü ayrı ilerler.

Gözlem alanının fiziksel doğruluğu ve NASA Type teyidi açık. Bu depolama adımı
yeni yangın etiketi üretmez; günlük gözlem unknown, negatif izin false.
