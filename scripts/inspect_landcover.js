// Pilot iller
var provinces = ee.FeatureCollection('FAO/GAUL/2025/level1')
    .filter(ee.Filter.eq('ISO3_CODE', 'TUR'))
    .filter(ee.Filter.inList(
        'GAUL1_NAME',
        ['Antalya', 'Mugla', 'Izmir', 'Mersin']
    ));

// İlk inceleme: 2017 referans yılı
var collection = ee.ImageCollection(
    'COPERNICUS/Landcover/100m/Proba-V-C3/Global'
).filterDate('2017-01-01', '2018-01-01');

print('Seçilen görüntü sayısı:', collection.size());

var landcover = ee.Image(collection.first());

print('Kaynak görüntü:', landcover);
print('Veri katmanları:', landcover.bandNames());

// Piksel içindeki tahmini ağaç örtüsü yüzdesi
Map.addLayer(
    landcover.select('tree-coverfraction'),
    {
        min: 0,
        max: 100,
        palette: ['fff7ec', 'a1d99b', '006d2c']
    },
    '2017 — Ağaç örtüsü (%)'
);

// Çalı örtüsü: Layers menüsünden açılabilir
Map.addLayer(
    landcover.select('shrub-coverfraction'),
    {
        min: 0,
        max: 100,
        palette: ['fff7ec', 'fec44f', '993404']
    },
    '2017 — Çalı örtüsü (%)',
    false
);

Map.addLayer(
    provinces.style({
        color: 'FF0000',
        fillColor: '00000000',
        width: 2
    }),
    {},
    'Pilot il sınırları'
);

Map.centerObject(provinces, 7);

// Kaynağın arazi örtüsü sınıfları
var classes = landcover.select('discrete_classification');

// Kapalı ve açık orman sınıfları
var forest = classes.gte(111).and(classes.lte(116))
    .or(classes.gte(121).and(classes.lte(126)));

var shrubs = classes.eq(20);
var herbaceous = classes.eq(30);

// İlk inceleme kapsamı: orman + çalılık + otsu bitkiler
var naturalVegetation = forest.or(shrubs).or(herbaceous);

Map.addLayer(
    naturalVegetation.selfMask(),
    { palette: ['FF9900'] },
    'İnceleme — doğal bitki örtüsü',
    false
);

// Kaynakta sınıflandırılamayan alanlar
Map.addLayer(
    classes.eq(0).selfMask(),
    { palette: ['FF00FF'] },
    'Kontrol — bilinmeyen örtü',
    false
);

// Maskelenmiş pikselleri, bilinmeyen sınıftan ayrı işaretle
var checkedClasses = classes.toInt16().unmask(-9999, false);

var unknownPixels = checkedClasses.eq(0);
var missingPixels = checkedClasses.eq(-9999);

var pixelAreaKm2 = ee.Image.pixelArea().divide(1000000);

var qualityAreas = pixelAreaKm2
    .multiply(unknownPixels)
    .rename('unknown_class_km2')
    .addBands(
        pixelAreaKm2
            .multiply(missingPixels)
            .rename('missing_data_km2')
    );

var qualityReport = qualityAreas.reduceRegion({
    reducer: ee.Reducer.sum(),
    geometry: provinces.geometry(100),
    crs: classes.projection(),
    scale: 100,
    maxPixels: 100000000,
    tileScale: 4
});

print('Pilot alan — örtü veri kontrolü (km²):', qualityReport);

Map.addLayer(
    missingPixels.selfMask(),
    { palette: ['00FFFF'] },
    'Kontrol — eksik veri',
    false
);

// Kaynağın piksel hizasını koru
var sourceProjection = classes.projection().getInfo();

print('İndirilecek görüntü kimliği:', landcover.id());
print('Kaynak projeksiyonu:', sourceProjection);

// Ayrıntılı sınır kesişimini yerelde yapacağız.
// Burada dört ili çevreleyen dikdörtgeni indiriyoruz.
var exportRegion = provinces.geometry(100).bounds(100);

Export.image.toDrive({
    image: classes.toInt16().unmask(-9999),
    description: 'export_landcover_copernicus_2017',
    folder: 'wildfire-risk-prediction',
    fileNamePrefix: 'landcover_copernicus_2017',
    region: exportRegion,
    crs: sourceProjection.crs,
    crsTransform: sourceProjection.transform,
    maxPixels: 1000000000,
    fileFormat: 'GeoTIFF',
    formatOptions: {
        cloudOptimized: true,
        noData: -9999
    }
});