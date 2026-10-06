# GCP iş sonu: sonuçları koru, kaynakları kaldır, faturalandırmayı kapat

Kullanıcının 6 Ekim 2026 talimatı: cebinden ödeme çıkmayacak; GCP işi bitince
kullanılan bulut kaynakları açık veya saklanmış olarak bırakılmayacak.
Bu belge plan ve kabul ölçütüdür; canlı hesap/kaynak temizliği yapılmış değildir.
Şu anki en son kullanıcı bildirimi VM Stop, Free Trial, TRY13,623 kredidir.

## Çalışırken

- Free Trial korunur; Upgrade / Activate paid account uygulanmaz. Google bu
  statüde kullanıcının faturalandırılmadığını ve yükseltme olmadan kredi/süre
  bittiğinde kaynakların duracağını belirtir. Bu, başka bir ücretli hesabın veya
  sonradan değişen statünün kontrol edildiği anlamına gelmez.
- İlk üretim oturumu en çok 8 saat / Stop / automatic restart Off. Sonraki süre
  ilk ölçüme göre seçilir; aynı paket en çok 24 saatlik yeni son zamanı kabul eder.
- Ara duruşta VM diski korunur; kısa sürede sıradaki oturuma dönülür. Uzun ara
  verilecekse gerekli kayıtlar dışarı doğrulanarak alınır ve VM/disk silinmesi
  seçeneği uygulanır. Drive'a tamamlanmış işler yeni VM'de tekrar işlenmez;
  ortam kurulumu ve kayıt geri okuması yine zaman alır.
- `--poweroff` iş sonunda kapatma ister; Google süre sınırı bağımsız Stop
  korumasıdır. **Stop disk silmez**; kalıcı disk ve varsa diğer saklanan kaynaklar
  tüketim oluşturabilir. Kod kredi bakiyesini okuyup otomatik fatura limiti
  uygulamaz; süre/byte sınırları para sınırı değildir.

## Tam temizliğin sırası

1. **Kayıtları doğrula.** Kalan 71 ayın uzak tamamlanma kayıtları ve aylık
   ürünleri geri okunup bilimsel kontrolden geçer; mevcut Temmuz 2023 sonucu da
   korunur. Sonuçları OAuth bağlantısından bağımsız açılabilen dosyalar olarak
   Drive'da ve ikinci kalıcı konumda tut. Küçük manifest, SHA listeleri, çalışma
   raporları ve gerekli günlükler dışarı alınır. Kuyruk bitti yazısı tek başına
   yeterli değildir; bu aşama bitmeden tek kopya olan VM dosyası silinmez.
2. **VM'yi durdur ve sil.** Console → Compute Engine → VM instances →
   `wildfire-cpu-pilot` → Stop, ardından Delete. Silme ekranında 30 GB boot
   diskinin de silindiği kontrol edilir. Diskin auto-delete ayarı önceden `yes`
   idi; canlı sonucu ayrıca doğrula. VM'yi yalnızca Stop durumunda bırakma.
3. **Kalan kaynakları denetle.** Doğru proje `dogalafetonlemesistemi` seçiliyken
   Disks, Snapshots, Images/Machine images, rezervasyonlar, Cloud Storage
   buckets ve VPC IP addresses sayfalarını kontrol et. Oluşturulmuş proje
   kaynaklarını kaldır; statik IP varsa release uygula. Disk/VM listelerinin
   boş olması başka hizmetlerde kaynak kalmadığını tek başına kanıtlamaz.
   Ek snapshot, yedekleme, bucket veya rezervasyon oluşturmak bu planın parçası
   değildir. Başka projelere/servislere ait verileri silme.
4. **Faturalandırmayı kapat.** Billing → Account management → bu proje için
   Disable billing; ilgili Cloud Billing hesabının bağlı projelerini inceleyip
   bu işe ait kullanım sona erdiğinde Close billing account uygula. **Closed**
   durumunu ve proje bağlantılarını yeniden kontrol et. Kapatma daha önce
   doğmuş ücretli kullanım borcunu iptal etmez; Free Trial ve ücretli Upgrade
   yasağı çalışma boyunca korunur.
5. **Bağlantıyı sonlandır.** Drive kayıtları ve bağımsız kopya doğrulandıktan
   sonra bu işe ait Drive OAuth erişimini iptal et; özel bağlantı dosyalarını
   kaldır. GCP projesi yalnızca bu iş için kullanılıyorsa, başka gereken verisi
   olmadığı doğrulanınca proje kapatma/silme işlemi de uygulanır. OAuth projesini
   erken silmek kayıtları kullanan uygulamanın erişimini kesebilir; bu nedenle
   bağımsız dosya kopyası önce hazırlanır. Drive sonuç klasörü saklanır.
6. **Son durumu kaydet.** Kaynak envanteri, Closed hesap, devre dışı proje
   billing bağlantısı ve kredi sonrası net tutar kontrolü kayda alınır. Gecikmeli
   kullanım raporları dikkate alınır; canlı doğrulama olmadan “temizlendi” denmez.

## Ödeme yöntemi ve saklanan hesap kayıtları

Yeni harcamayı durdurmanın esas adımları kaynakların kaldırılması ve Cloud
Billing'in kapatılmasıdır. Kart silmeye güvenerek çalışan hizmet bırakılmaz.
Google, Cloud Billing hesabının elle silinemediğini; kapatılmış hesap bilgisinin
denetim için saklandığını belirtir. Dolayısıyla faturalanabilir kaynakları
kaldırmak ile bütün hesap geçmişini silmek aynı işlem değildir.

Kart kaldırma ayrıca incelenebilir; Google'ın ödeme yöntemi kuralları tek/ana
kartın kaldırılmasını sınırlayabilir. Yeni kart ekleme veya başka Google
aboneliklerini etkileyebilecek genel ödeme profili kapatma otomatik yapılmaz.
Kullanıcının Drive depolama aboneliği bu GCP temizliğiyle iptal edilmez.

## Resmî dayanaklar

- [Free Trial](https://docs.cloud.google.com/free/docs/free-cloud-features)
- [Stop ve saklanan kaynaklar](https://docs.cloud.google.com/compute/docs/instances/suspend-stop-reset-instances-overview)
- [VM silme / disk silme ayarı](https://docs.cloud.google.com/compute/docs/instances/deleting-instance)
- [Billing kapatma](https://docs.cloud.google.com/billing/docs/how-to/close-or-reopen-billing-account)
- [Billing hesabı kayıtlarının saklanması](https://docs.cloud.google.com/billing/docs/how-to/manage-billing-account)
- [Ödeme yöntemi kuralları](https://docs.cloud.google.com/billing/docs/how-to/payment-methods)
