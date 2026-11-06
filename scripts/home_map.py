from pathlib import Path
import csv,json,html
root=Path.cwd(); (root/'assets').mkdir(exist_ok=True)
rows=list(csv.DictReader(open('data/water_municipal.csv')))
geo=json.load(open('data/municipios.geojson'))
vals={r['divipola']:r['irca'] for r in rows if r['year']=='2023' and r['zone']=='rural'}
colors=['#72ddc6','#b3dd92','#f0d47d','#ed946a','#d96567']
paths=[]
for f in geo['features']:
    g=f['geometry']; polys=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
    v=vals.get(str(f['properties']['divipola']).zfill(5),'')
    col='#354e59' if not v else colors[next((i for i,b in enumerate([5,14,35,80,100]) if float(v)<=b),4)]
    ds=[]
    for poly in polys:
        for ring in poly:
            ds.append('M'+'L'.join(f'{(x+82)*35:.1f},{(13-y)*35:.1f}' for x,y,*_ in ring)+'Z')
    paths.append(f'<path d="{"".join(ds)}" fill="{col}"/>')
svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 560 650" role="img" aria-labelledby="title desc"><title id="title">Colombia: rural water quality, 2023</title><desc id="desc">Municipal boundaries colored by IRCA (utility-supplied, INS open data). Grey means no reported value. Source: local DANE boundaries and municipal data.</desc><g stroke="#102d39" stroke-width=".35" stroke-linejoin="round" fill-rule="evenodd">'+''.join(paths)+'</g></svg>'
(root/'assets/colombia-water.svg').write_text(svg)
print('Map created from',len(geo['features']),'local boundaries.')
