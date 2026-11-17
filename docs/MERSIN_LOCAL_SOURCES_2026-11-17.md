# Mersin nokta incelemesi için yerel kaynaklar — 17 Kasım 2026

13 Kasım saat örnekleminin 24 arşiv satırı ve iki saat yorumu korundu.
Proje pencerelerinin 77 komşu nominal günü sabit yöntem pilotunun kaynak
planıyla karşılaştırıldı. Örneklem saat uçlarına göre seçilmişti.

Önbellekte 196 NetCDF dosyası var. Tarih kesişiminde sekiz tam yangın
maskesi–konum çifti bulundu. Bunların 16 dosyası toplam 1.478.340.187 bayt.
Tamamı 15 Ağustos 2021 nominal gününe ait. Boyut ve SHA-256 değerleri
sabit pilot planıyla doğrulandı. Tarih kesişimi olay noktasının gerçekten
tarandığını veya açık gözlendiğini belirlemiyor.

Sonraki işlemde arşiv koordinatı ile yerel piksel geometrisi karşılaştırılacak.
Koordinatın başlangıcı temsil etmesi, saat standardı ve yangının etkinlik
süresi açık konular. Birinci aşama sürüyor. Günlük gözlem `unknown`,
negatif etiket izni `false`.

`python scripts/quality/audit_mersin_local_sources.py` yerel envanteri
yeniden üretir. İlgili 110 test, geçici dosyalar depo içinde tutulduğunda
geçti. İlk çalıştırmada iki test, depo dışındaki geçici dizin için göreli
yol üretilemediğinden hata verdi. Ruff kontrolü geçti.

Yerel makbuz
`outputs/reports/dataset/mersin_local_sources_v1/20261117T204342Z_e2380a4a/readback.json`.
SHA-256 `b367e738160b6490e6e3d1c21fd0366cbb14afaa69230afe529cf9f76f436dfb`.
