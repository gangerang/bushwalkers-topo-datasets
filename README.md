# Bushwalkers Topo Datasets

Geospatial datasets for bushwalking and outdoor recreation in NSW, Australia.

## URL Pattern

```
https://raw.githubusercontent.com/<owner>/bushwalkers-topo-datasets/data/<path>
```

## Dynamic Datasets

Updated automatically by GitHub workflows.

| Dataset | Path | Format | Update Frequency |
|---------|------|--------|------------------|
| RFS Hazard Reduction Burns | `dynamic/rfs/hr_burns.geojson` | GeoJSON | Daily |
| GNB Naming Proposals | `dynamic/gnb/naming_proposals.geojson` | GeoJSON | Daily |
| Crown Road Sales (Active) | `dynamic/crown_roads/sales_active.geojson` | GeoJSON | Daily |
| Crown Road Sales (Inactive) | `dynamic/crown_roads/sales_inactive.geojson` | GeoJSON | Daily |
| Crown Road Sales (Raw) | `dynamic/crown_roads/sales.tsv` | TSV | Daily |
| BOM Stream Gauges (AU) | `dynamic/bom/au_stream_gauges.geojson` | GeoJSON | Manual |
| BOM Stream Gauges (NSW) | `dynamic/bom/nsw_stream_gauges.geojson` | GeoJSON | Manual |
| BOM Stream Gauges (AU) | `dynamic/bom/au_stream_gauges.gpkg` | GeoPackage | Manual |

## Static Datasets

Manually maintained reference data.

| Dataset | Path | Format |
|---------|------|--------|
| GetLostMaps Huts | `static/getlostmaps/huts.geojson` | GeoJSON |
| GetLostMaps Repeaters | `static/getlostmaps/repeaters.geojson` | GeoJSON |
| GetLostMaps Ruins | `static/getlostmaps/ruins.geojson` | GeoJSON |
| Water NSW Schedule 1 | `static/wnsw/schedule_1.geojson` | GeoJSON |
| Water NSW Schedule 2 | `static/wnsw/schedule_2.geojson` | GeoJSON |
| Water NSW Stream Height | `static/wnsw/stream_height_data.gpkg` | GeoPackage |
| Historic Aerial Imagery Index | `static/historic_imagery/nsw_index.gpkg` | GeoPackage |
| Historic Aerial Imagery (Sydney) | `static/historic_imagery/sydney_extract.geojson` | GeoJSON |
| BOM Rain/River Station List | `static/bom/rain_river_station_list.csv` | CSV |

## Data Sources

- **RFS**: [NSW Rural Fire Service](https://www.rfs.nsw.gov.au/)
- **GNB**: [NSW Geographic Names Board](https://www.gnb.nsw.gov.au/)
- **BOM**: [Bureau of Meteorology](http://www.bom.gov.au/)
- **Water NSW**: [WaterNSW](https://www.waternsw.com.au/)
- **GetLostMaps**: [Get Lost Maps](https://www.getlost.com.au/)
- **Spatial Services NSW**: [NSW Spatial Services](https://www.spatial.nsw.gov.au/)
