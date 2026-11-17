# Mersin arşiv saatleri ile VIIRS tarama zamanları — 13 Kasım 2026

2018–2023 dönemindeki 479 uygun arşiv satırından 24'ü seçildi. Her yıl
ve son yanan alan grubu için kaydedilen en erken ve en geç saatli
satır alındı. Seçimde uydu tespitleri kullanılmadı. Saat uçlarına
odaklanan bu örneklem, saat dilimi duyarlılığını incelemek içindir.
Mersin arşivindeki tüm yangınlara genellenebilecek bir örneklem değildir.
[Olay arşivi ve konum-saat bağlantısı](MERSIN_OPEN_INCIDENT_ARCHIVE_2026-11-08.md).

Her satırın saati Türkiye saati ve UTC olarak yorumlandı. Her yorumda
bildirilen dakikayı içeren proje penceresi için üç komşu nominal günün
tarama kayıtları geri okundu. Toplam 23 aydan 77 nominal gün kullanıldı.
48 karşılaştırmanın tamamında üç komşu gün dosyası mevcuttu. Taramanın
zaman aralığı bütünüyle proje penceresine giriyorsa hesaba katıldı.
Sonraki kara taraması, içinde en az bir seçili kara merkezi bulunan
ve bildirilen dakikadan sonra başlayan ilk tarama satırıdır.

| Saat yorumu | Son yanan alan | Sonraki kara taraması | İlk sonraki kara taramasına ortanca süre* | Bildirilen dakikada veya sonrasında ısıl merkezli tarama |
| --- | --- | ---: | ---: | ---: |
| Türkiye saati | 1 ha altı | 12/12 | 123 dk | 0/12 |
| Türkiye saati | En az 1 ha | 10/12 | 384 dk | 6/12 |
| UTC | 1 ha altı | 8/12 | 47 dk | 0/12 |
| UTC | En az 1 ha | 10/12 | 326 dk | 3/12 |

*Ortanca yalnız aynı proje penceresinde sonraki taraması olan satırlar
üzerinden hesaplandı. Karşılaştırma ısıl merkez için nominal ve yüksek
güven sınıflarını kullanır. Dokuz satırın yorumlanan UTC tarihi değişti.
Örneğin bir küçük yangın kaydındaki 23.59, Türkiye saati yorumuyla 20.59
UTC oluyor ve proje penceresinde 137 dakika sonra kara taraması var.
UTC yorumunda aynı pencerenin sonuna kadar sonraki kara taraması yok.

Tarama kayıtları 5 km hücrenin tamamına ait. Başlangıç noktasındaki
bulut, örtü, piksel geometrisi ve yangının ne kadar süre etkin kaldığı
bu ölçümle belirlenemiyor. Arşiv saati ve olay kimliği de doğrulanmayı
bekliyor. Birinci aşama açık. Sonraki inceleme, konumu kaynakta açıkça
belirtilen küçük yangınlarda nokta çevresindeki piksel sınıflarına
odaklanabilir. Günlük gözlem `unknown`, etiket izinleri kapalı.

`python scripts/quality/audit_mersin_scan_times.py` kaynak paketlerinin
ve kullanılan günlük üyelerin SHA-256 değerlerini denetler. 86 ilgili
test geçti. Yerel makbuz
`outputs/reports/dataset/mersin_scan_times_v1/20261113T163739Z_d391ce51/readback.json`.
SHA-256 `14921e99234fac1db8029dcd4b42a681f75c8b93a3f554a261e1116c31a704ef`.
