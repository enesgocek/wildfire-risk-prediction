// Türkiye'nin il sınırları
var turkey = ee.FeatureCollection('FAO/GAUL/2025/level1')
    .filter(ee.Filter.eq('ISO3_CODE', 'TUR'));

// Kaynaktaki il adlarını kontrol etmek için
print('Türkiye il adları:',
    turkey.aggregate_array('GAUL1_NAME').distinct().sort()
);

// Türkçe karakterler ve eski adlandırmalar için alternatifler
var provinceNames = [
    'Antalya',
    'Mugla', 'Muğla',
    'Izmir', 'İzmir',
    'Mersin', 'Icel', 'İçel', 'Içel'
];

var pilot = turkey.filter(
    ee.Filter.inList('GAUL1_NAME', provinceNames)
);

print('Seçilen il sayısı:', pilot.size());
print('Seçilen il adları:',
    pilot.aggregate_array('GAUL1_NAME').distinct().sort()
);

// Türkiye sınırları
Map.addLayer(
    turkey.style({
        color: '888888',
        fillColor: '00000000',
        width: 1
    }),
    {},
    'Türkiye illeri'
);

// Pilot iller
Map.addLayer(
    pilot.style({
        color: 'FF6600',
        fillColor: 'FF660033',
        width: 2
    }),
    {},
    'Pilot çalışma alanı'
);

Map.setCenter(31, 37.5, 6);

// Dört ilin geometrisini tek çalışma alanında birleştir
var merged = pilot.union(10);

var aoiFeature = ee.Feature(merged.first().geometry(), {
    aoi_id: 'TR_PILOT_V1',
    provinces: 'Antalya,Izmir,Mersin,Mugla',
    boundary_source: 'FAO/GAUL/2025/level1'
});

var aoi = ee.FeatureCollection([aoiFeature]);

print('AOI kayıt sayısı:', aoi.size());
print('AOI alanı (km²):',
    aoiFeature.geometry().area(10).divide(1000000)
);

Map.addLayer(
    aoi.style({
        color: '0066FF',
        fillColor: '00000000',
        width: 2
    }),
    {},
    'Birleşik çalışma alanı'
);

// Çalışma alanını Google Drive'a aktar
Export.table.toDrive({
    collection: aoi,
    description: 'export_pilot_aoi_v1',
    folder: 'wildfire-risk-prediction',
    fileNamePrefix: 'aoi',
    fileFormat: 'GeoJSON'
});
