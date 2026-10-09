# İş yükü ve büyük gruplara geçiş — 5 Ekim 2026

> Dönemsel uygulama kaydı. Kurulum, maliyet ve bekleyen iş ifadeleri belgenin
> ilgili çalışma aşamasına aittir. Güncel durum [STATUS.md](STATUS.md), mevcut
> üretim yolu [devam rehberinde](GCP_SOURCE_AWARE_CONTINUATION_2026-10-09.md) izlenir.

Daha büyük işlem gruplarını değerlendirdim; mevcut iş yükünü ve kalan
adımları değerlendirdim. Yeni indirme başlamadı. Haftalık/aylık kapsam seçimi ve
Google Drive'daki kullanılabilir sonuç alanı soruldu.

Kapsam sorusuna yanıt olarak, Colab sekmesi kapanınca çalışmanın
devam etme koşullarını değerlendirdim; bu henüz haftalık/aylık kapsam seçimi değil.
Google'ın güncel [Colab FAQ'sı](https://research.google.com/colaboratory/faq.html)
kontrol edildi: kod uzak sanal makinede çalışır; boşta kalma ve azami ömür
sınırları var. Ücretsiz çalışma sonuna kadar garanti değil; belirtilen
12 saat azami süre de kaynak/kullanım koşullarına bağlı. Pro+ yeterli işlem
birimiyle 24 saate kadar sürekli yürütmeyi destekliyor. Ücretsiz planda
uzun işlerin sekme kapalı tamamlanacağına dayanarak takvim kurulmayacak.
Mevcut kayıt yolu kesinti sonrası yeniden oturum açıp hücreyi çalıştırınca
tamamlanan çiftleri geri yükler; kapanan oturumu kendiliğinden yeniden
başlatan bir zamanlayıcı yok. Haftalık ilk grup önerisi korunuyor.

## Tamamlananlar

- Dört il, 2.899 model hücresi ve coğrafi anahtar/alan denetimleri hazır.
- FIRMS kaynakları ve 33.255 aday tespit hazır. Nihai bağımsız olay/etiket değil.
- 2018–2024 meteorolojisi: 2.557 gün ve 7.412.743 hücre-gün hazır/denetlenmiş.
- Arazi örtüsü aday oranları hesaplandı; tarihsel kullanım kararı açık.
- Kış ve yaz doğal uydu kontrolleri, Colab yürütme ve kayıt/geri okuma yolu
  çalıştı. Bunlar tüm dönem uydu gözlem tablosunun tamamlandığı anlamına gelmiyor.

## Veri seti için kalan beş ana adım

1. **Günlük uydu gözlem hattı:** çakışan gözlem alanlarını günlük birleştirmek,
   kalite/zaman bilgilerini korumak, kompakt kalıcı formatı ve daha hızlı
   üretim yürütmesini doğrulamak; ardından seçilen büyük grupları işlemek.
   Yaklaşık geometri ve gözlem yetersizliğinin sınırları açık tutulacak.
2. **Yangın olay kataloğu:** aynı yangının tekrar tespitlerini olaylarda
   birleştirmek; sabit termal kaynakları ve belirsiz kayıtları ele almak.
   NASA Type teyidi ve 679 erken NOAA-20 katalog/zaman farkı açık konular.
3. **Günlük etiketler:** yeni olayın ilk uydu tespitine göre pozitif,
   seçilmiş gözlem kuralına göre negatif ve belirsiz durumları tanımlamak.
   Eksik gözlem otomatik negatif olmayacak. Uydu ilk tespiti gerçek tutuşma
   zamanı veya yangının nedeninin kanıtı değil.
4. **Çevresel özellikler:** geçmişe uygun bitki örtüsü/NDVI/NDMI ve
   yükseklik/eğim gibi arazi bilgilerini hazırlamak. Kaynak yayımlanma ve
   gözlem zamanları tahmin anına uygun olmalı.
5. **Nihai eğitim tablosu:** hava, yangın etiketleri ve çevresel özellikleri
   aynı hücre/tarih anahtarlarıyla birleştirmek; eksik/tutarsız kayıt,
   tekrar ve gelecek bilgi sızıntısını denetlemek ve sürümlemek.

Ardından basit model karşılaştırmaları, olasılık kalibrasyonu, harita/API ve
bitirme raporu var. Eğitim 2018–2023, doğrulama 2024; 2025 final testi hâlâ
kapalı. Mevcut durumdan güvenilir bir toplam tamamlanma yüzdesi çıkarılmadı.

## Büyüklük ve süre hesabı

Mevcut eğitim kataloğunda 18.711 nominal dosya çifti, yaklaşık 3.435 GB
eşleşmiş ham kaynak var. Tüm dört koleksiyonun eşleşmemiş dosyalar dahil
boyutu yaklaşık 3,17 TiB. Bunlar farklı kapsam/ölçü birimleri.
Eğitim dönemi 2.191 gün ve 72 takvim ayı; dosya çifti bağımsız yörünge
yeniden gözlemi veya model satırı sayısı değil.

Son yaz kontrolünde çift başına ortalama indirme/doğal işleme/ilk denetim
125,76 saniye. Aynı hızı 18.711 nominal çifte doğrusal uygularsak yaklaşık
654 saat / 27 gün sürekli işlem eder. Bu tek günlük tanı işleyicisinden
yapılan kaba ölçek hesabı; takvim süresi veya nihai üretim bütçesi değil.
Kurulum, kalıcı kayıt, başarısız denemeler ve oturum araları hariç.
Üretim kodunun aynı dizileri tekrar okuma/geometri tanısı giderleri azaltılabilir;
hız artışı ölçülmeden bir oran vaat edilmedi.

| Alternatif | Yeni çift | Yeni ham transfer tahmini | Mevcut hızdan kaba işlem süresi |
| --- | ---: | ---: | ---: |
| 13–19 Temmuz 2023 haftası, B günü hariç | 56 | 10,25 GB | 2 saat |
| Temmuz 2023 ayı, B günü hariç | 264 | 48,30 GB | 9,2 saat |

Ham veri Colab'da birer çift işlenebilir; grup boyutu bütün ham kaynakların
aynı anda diskte bulunmasını gerektirmez. Bununla birlikte toplam transfer
ve oturum süresi büyür. Bu iki seçeneğin gerçek InputPointer, bulut/QA ve
diğer doğal kontrolleri henüz çalıştırılmadı; katalog eşleşmesi ön koşul.

Sonuç ZIP'i 21,34 MB; bunun 20,39 MB'ı tanı geometrileri. Üretimde günlük
birleşik alan/kalite/zaman sonuçlarını doğrulayıp hangi çizimleri saklayacağımızı
belirlememiz gerekiyor. Çakışan alanları toplamadan, kaynak/çıktı izini
kaybetmeden ve eski kontrol kayıtlarını değiştirmeden ilerleyeceğiz.

Öneri: mevcut sonuçlarla günlük birleşim/format ve hız denetimi; ardından
**haftalık ilk büyük grup**. Başarılı ölçümden sonra aylık gruplara büyütme.
Kapsam kararı verilmeden haftalık/aylık yeni bulut işi hazırlığına geçilmedi;
Drive boş alanı bilinmeden tam dönem kalıcı alan bütçesi kesinleştirilmedi.

Kaynaklar: `l2_training_catalogue_inventory.json`, `summer_control_pairs.csv`
ve `colab_summer_completed_diagnostics.json`,
`outputs/reports/observation_coverage/` altında. Bu kayıtlar eğitim verisine
ait; hesap için 2024/2025 kullanılmadı.
