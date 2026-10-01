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


var cellSize = 5000;

// Testte başarılı olan açık koordinat sistemi tanımı
var crsWkt =
    'PROJCS["Pilot_CEA_WGS84",' +
    'GEOGCS["WGS 84",' +
    'DATUM["WGS_1984",' +
    'SPHEROID["WGS 84",6378137,298.257223563]],' +
    'PRIMEM["Greenwich",0],' +
    'UNIT["degree",0.0174532925199433]],' +
    'PROJECTION["Cylindrical_Equal_Area"],' +
    'PARAMETER["standard_parallel_1",30],' +
    'PARAMETER["central_meridian",0],' +
    'PARAMETER["false_easting",0],' +
    'PARAMETER["false_northing",0],' +
    'UNIT["metre",1]]';

var metreProjection = ee.Projection(crsWkt);

var gridProjection = ee.Projection(
    crsWkt,
    [cellSize, 0, 0, 0, cellSize, 0]
);

var aoiGeometry = aoiFeature.geometry();

// Ayrıntılı sınır yerine, onu çevreleyen basit dikdörtgen
var boundingBox = aoiGeometry.bounds(100, metreProjection);

// Şimdilik yalnızca aday hücreleri üret
var candidateGrid = boundingBox.coveringGrid(gridProjection);

print('Aday hücre sayısı:', candidateGrid.size());

var firstCell = ee.Feature(candidateGrid.first());

print(
    'İlk hücrenin alanı (km²):',
    firstCell.geometry()
        .area(100, metreProjection)
        .divide(1000000)
);

// Ekranda yalnızca 200 hücre göstererek önizlemeyi hafif tut
Map.addLayer(
    candidateGrid.limit(200).style({
        color: '333333',
        fillColor: '00000000',
        width: 1
    }),
    {},
    'Aday grid — ilk 200 hücre'
);

Map.centerObject(aoiFeature);

// Aday hücrelere konumdan türetilen kalıcı kimlikler ver
var candidateGridWithIds = candidateGrid.map(function (cell) {
    var centre = cell.geometry().centroid(10, metreProjection);
    var coordinates = centre.coordinates();

    var column = ee.Number(coordinates.get(0))
        .divide(cellSize).floor();

    var row = ee.Number(coordinates.get(1))
        .divide(cellSize).floor();

    var gridId = ee.String('E6933_5K_V1_C')
        .cat(column.format('%d'))
        .cat('_R')
        .cat(row.format('%d'));

    return cell.set({
        grid_id: gridId,
        grid_version: 'E6933_5K_V1',
        grid_crs: 'EPSG:6933',
        cell_size_m: cellSize,
        column: column,
        row: row
    });
});

print('Kimlik verilen hücre sayısı:', candidateGridWithIds.size());

print(
    'Benzersiz kimlik sayısı:',
    candidateGridWithIds
        .aggregate_array('grid_id')
        .distinct()
        .size()
);

print('Kimlikli örnek hücreler:', candidateGridWithIds.limit(3));

Export.table.toDrive({
    collection: candidateGridWithIds,
    description: 'export_grid_5km_candidates_v1',
    folder: 'wildfire-risk-prediction',
    fileNamePrefix: 'grid_5km_candidates',
    fileFormat: 'GeoJSON'
});