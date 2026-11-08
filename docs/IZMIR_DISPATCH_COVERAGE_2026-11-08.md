# İzmir İtfaiyesi 2023 kayıtlarının yayın kapsamı — 8 Kasım 2026

İzmir Büyükşehir Belediyesinin aynı 2023 kaynağı için yayımladığı
indirilebilir dosya, açık API tablosu ve yıllık rapor karşılaştırıldı.
İnceleme, belediye müdahale kayıtlarının bağımsız olay araştırmasında
hangi kapsamla kullanılabileceğini belirlemek için yürütüldü.
[Açık veri kaynağı ve sözlüğü](https://acikveri.bizizmir.com/dataset/izmir-itfaiyesi-yangin-mudahale-istatistigi/resource/f718e29e-0e3f-4b63-8019-e1920ca94330) ·
[2023 yıllık raporu](https://itfaiye.izmir.bel.tr/YuklenenDosyalar/Dokumanlar/23012024_2023.pdf).

## Ölçülen yayın farkı

| Sayım, 2023 belediye müdahale kayıtları | İndirilebilir dosya | Yıllık rapor | Açık API | Dosyada var, API'de yok |
| --- | ---: | ---: | ---: | ---: |
| Tüm müdahaleler | 12.986 | 12.986 | 12.250 | 736 |
| Orman/fidanlık | 194 | 194 | 193 | 1 |
| Makilik/çalı | 82 | 82 | 81 | 1 |

API sayfaları satır numarasına göre sıralandı. Tekil ve sıralı
12.250 API satırı, indirilen dosyanın ilk 12.250 satırıyla
tarih, tür ve ilçe alanlarında sırayla eşleşti. Bir sonraki
sorgu boş döndü. Bu eşitlik üç alanı kapsıyor. İndirilebilir
dosyada ek **736 satır** var. Bunlar dosyanın %5,67'sine karşılık
geliyor. 129 satır Kasım, 607 satır Aralık ayına ait. Fark
9 Kasım–31 Aralık arasında 38 tarihe yayılıyor. Bu tarihlerden
36'sında API'de hiçbir kayıt yok. 25 Kasım'da ise dosyada
19, API'de 4 satır var. Bu örnek, API'nin son tarihinden
önceki günlerin de ayrıca kontrol edilmesi gerektiğini gösteriyor.
Yayın farkının nedeni ve 2019–2022 dosyalarının kapsamı bu
karşılaştırmada belirlenmedi.

## Olay doğrulamasında kullanım

2023 için bağlam kaydı aranırken indirilebilir dosya esas alınır.
Orman/fidanlık ve makilik/çalı kategorilerindeki 276 satır belediye
müdahale kayıtlarıdır. Portal komşu illere yapılan takviyelerin
de kapsamda olduğunu belirtiyor. Bu toplam, İzmir'deki benzersiz
yeni orman ve çalılık yangınlarının sayısı olarak kullanılamaz.
Sözlükteki saat, ekibin çıkışına ait. Kaynakta tutuşma koordinatı
veya koordinat belirsizliği alanı yok. Adres bölgesi alanı
eşleştirmeye ve analiz çıktısına alınmadı. Başlangıç konumu
ve olay kapsamı için bağımsız kanıt gereksinimi sürüyor. Hedef
alanı boş, günlük gözlem `unknown` ve etiket izinleri kapalı.
[Portal kapsamı](https://acikveri.bizizmir.com/dataset/izmir-itfaiyesi-yangin-mudahale-istatistigi) ·
[Önceki İzmir vaka denetimi](PUBLIC_EVENT_CONTEXT_2026-11-08.md).

## Yeniden üretim

Üretici `python scripts/quality/audit_izmir_dispatch_coverage.py`.
İki kaynak kimliği, üç sütunda satır karşılaştırması, tarih farkları
ve kurumun yıllık toplamları denetlendi. Çalışma kitabı ikinci bir
okuyucuyla yeniden sayıldı ve sonuçlar eşleşti. Referans alımı ve
hedef kurallarındaki 73 ilgili test geçti.

| Yerel kanıt, `outputs/reports/dataset/izmir_dispatch_coverage_v1` altında | SHA-256 |
| --- | --- |
| `sources/izmir_dispatch_2023.xlsx` | `2082ac26367c89364d8cf18d814c8a2e45b517c7cd887ef8cb9ec54bd6b4dcdf` |
| `20261108T033936Z_765251ae/api_projection.json` | `4bf5d59552368ee4dd7fc03d4912d9e5ea870999e51d40282e695c7200d2b036` |
| `20261108T034200Z_ab9d1358/readback.json` | `afffc9d6b805eda514da49e0878afda71c898fbaffc99cc57040b5cbb4b4fc1d` |
