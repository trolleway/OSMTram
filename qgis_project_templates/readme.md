
## tinyblack

simple style on black background, just lines

palette: https://colorbrewer2.org/#type=qualitative&scheme=Pastel1&n=3

## get test data
```
osmconvert russia.osm.pbf -b=34.179684,61.711345,34.51614,61.866409 --out-pbf -o=petrozavodsk.pbf
mkdir test
python3 ../core/process_basemap.py --dump_path petrozavodsk.pbf --bbox 34.179684,61.711345,34.51614,61.866409 --output test

```