from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'raw' / 'nyc311_q1_2025.csv'
OUT.parent.mkdir(parents=True, exist_ok=True)
url = 'https://data.cityofnewyork.us/resource/erm2-nwe9.csv'
fields = 'unique_key,created_date,closed_date,agency,agency_name,complaint_type,descriptor,location_type,incident_zip,status,borough,latitude,longitude,open_data_channel_type'
params = {
    '$select': fields,
    '$where': "created_date >= '2025-01-01T00:00:00' AND created_date < '2025-04-01T00:00:00'",
    '$limit': 1000000,
    '$order': 'unique_key',
}
with requests.get(url, params=params, stream=True, timeout=300) as r:
    r.raise_for_status()
    with OUT.open('wb') as f:
        for chunk in r.iter_content(1024 * 1024):
            if chunk:
                f.write(chunk)
print(f'Downloaded {OUT.stat().st_size:,} bytes to {OUT}')
