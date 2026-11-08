# Menderes Hona Boğazı için yer ve uydu kanıtı — 8 Kasım 2026

10 Temmuz 2023 Menderes vakası için olay anlatıları, bir ağaçlandırma
krokisi ve önceki İzmir incelemesindeki 14 VIIRS kaydı karşılaştırıldı.
Amaç, daha dar bir başlangıç yeri doğrulanabilir mi ve 5 km çevresindeki
tespitlerin hepsi aynı keşif grubuna mı ait sorularını incelemekti.
[Önceki İzmir denetimi](IZMIR_JULY_EVENT_CONTEXT_2026-11-08.md).

## Yer adları ve belge kapsamı

- İzmir Orman Bölge Müdürlüğü, 10 Temmuz 2023 ve Oğlananası
  adını birlikte veriyor. İzmir İtfaiyesinin 2023 yıllık raporu
  Hona Boğazı adını kullanıyor. 10 Temmuz'daki saha görüşmesinde
  belediye başkanı başlangıç için Hona Boğazı çevresini, DHA'nın
  saha haberi ise Develi–İncirlik mevkisini bildiriyor. Bu
  metinlerde özgün tutuşma koordinatı bulunmadı.
  [İzmir OBM](https://www.ogm.gov.tr/izmirobm/haberler/sehidimiz-mustafa-gurpinar%E2%80%99i-torenle-ugurladik) ·
  [İtfaiye 2023 raporu](https://itfaiye.izmir.bel.tr/YuklenenDosyalar/Dokumanlar/23012024_2023.pdf) ·
  [Belediye başkanıyla saha görüşmesi](https://10haber.net/gundem/izmirde-iki-ayri-yangin-ormanlik-alana-konteyner-koymak-istediler-dikkatsizlikleriyle-ormani-yaktilar-215872/) ·
  [DHA saha haberi](https://www.dha.com.tr/gundem/izmirin-2-ilcesinde-orman-yangini-2279041).
- Ege Orman Vakfının 2001 projesi Oğlananası ve Hona Boğazı
  adlarını aynı 34 hektarlık ağaçlandırma için kullanıyor.
  Kroki, yaklaşım yolunu ve bağış parsellerini gösteriyor.
  Koordinat ağı veya projeksiyon bilgisi bulunmadığı için bu
  çizimden bir başlangıç noktası ya da olay sınırı türetilmedi.
  Menderes Belediyesinin 2024 raporundaki 15 Temmuz müdahalesi
  Hona Boğazı'nı Develi ile Tekeli arasında tarif ediyor.
  Farklı yıldaki kayıt yalnız yer adı bağlamında kullanıldı.
  [Vakıf krokisi](https://www.egeorman.org.tr/images/belgeler/20honabogaz.pdf) ·
  [Menderes Belediyesi 2024 raporu, s. 411](https://menderes.bel.tr/wp-content/uploads/2025/07/afet-faaliyet-2024.pdf).

## 10 Temmuz UTC penceresindeki uydu kayıtları

HGM Oğlananası yerleşim noktasının 5 km çevresinde, bildirilen
yaklaşık başlangıçtan itibaren aynı UTC penceresindeki 14 seçili
VIIRS kaydı incelendi. En erken kayıt NOAA-20'ye ait, saat
11.03 UTC. Bu piksel merkezi Oğlananası, Develi ve Tekeli
temsil noktalarından sırasıyla **2,68 km, 3,53 km ve 4,24 km**
uzakta. Bu mesafeler yerleşim noktalarına aittir.
[HGM yer adları, 2123](https://www.harita.gov.tr/uploads/files/products/turkiye-ve-cevresi-cografi-ad-dizini-ingilizce-pdf-107.pdf) ·
[Develi](https://mapcarta.com/12979272) · [Tekeli](https://mapcarta.com/12944602).

| 5 km hücre kodunun son bölümü | 5 km çevre seçkisindeki kayıt | Hücrede yerel tarama ve katalog sayımı |
| --- | ---: | --- |
| C524_R905 | 5 | 11.54 UTC S-NPP, 5 |
| C524_R906 | 7 | 11.03 UTC NOAA-20, 1 ve 11.54 UTC S-NPP, 6 |
| C525_R906 | 2 | 11.54 UTC S-NPP, 2 |

Üç komşu kaynak günü paketinden alınan yerel taramalar
`(T,T+24h]` penceresinde incelendi. Üç hücrede dört sensör ve
dakika toplamı katalogla eşleşti. Yüklenen taramalarda pencere
sınırını kesen satır yok. Eşleşme hücre toplamları düzeyinde
ve aynı uydu kaynak ailesi içinde.

Dokuz kayıtlı gruplama ayarının tamamında ilk iki hücredeki
**12** seçili tespit bir gruba, C525_R906'daki **2** tespit
başka bir gruba düştü. Bu ayrım seçili tespitler için geçerli.
5 km çevresindeki 14 tespitin tek olaya bağlanması için
mesafe ve saat bilgisi yetersiz. İki keşif grubunun fiziksel
olay kimlikleri, tutuşma noktası ve günlük gözlem yeterliliği
açık. Hedef alanı boş ve iki etiket izni kapalı kaldı.

Üretici `python scripts/quality/audit_menderes_hona_context.py`.
5 km seçkisi ayrı UTM hesabıyla, dokuz gruplama ve dört
sensör-dakika toplamı özgün yerel tablolardan ikinci kez
doğrulandı. 94 ilgili test geçti.
Yerel çıktı `outputs/reports/dataset/menderes_hona_context_v1/20261108T035543Z_f2cfcec3/readback.json`.
SHA-256 `05b59ebb981cce0f367df145f3a663f54f627662ab407124a506dcfc42e28b92`.
