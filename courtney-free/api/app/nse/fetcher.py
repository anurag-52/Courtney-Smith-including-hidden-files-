from __future__ import annotations
from datetime import datetime, timedelta
import httpx, io, zipfile, pandas as pd
BASE = "https://archives.nseindia.com/content/historical/EQUITIES/{year}/{mon}/cm{day}{mon}{year}bhav.csv.zip"
def latest_bhavcopy(session: httpx.Client, asof: datetime) -> pd.DataFrame:
    for delta in range(0, 7):
        d = asof - timedelta(days=delta)
        mon = d.strftime("%b").upper()
        url = BASE.format(year=d.strftime("%Y"), mon=mon, day=d.strftime("%d"))
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/zip", "Referer": "https://www.nseindia.com/"}
        r = session.get(url, headers=headers, timeout=30)
        if r.status_code == 200:
            zf = zipfile.ZipFile(io.BytesIO(r.content))
            name = zf.namelist()[0]
            with zf.open(name) as f:
                df = pd.read_csv(f)
                df.columns = [c.strip().upper() for c in df.columns]
                return df
    raise RuntimeError("Could not fetch recent Bhavcopy")