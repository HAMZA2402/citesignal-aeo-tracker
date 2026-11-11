"""Manual import of Google Search Console GENERATIVE AI Search page report.

This report is a separate data type from independently sampled AI answers.
"""
from io import BytesIO
import re
import pandas as pd


def load_gsc_pages(payload: bytes, filename: str) -> pd.DataFrame:
    if filename.lower().endswith('.xlsx'):
        raw=pd.read_excel(BytesIO(payload))
    else:
        raw=pd.read_csv(BytesIO(payload),encoding='utf-8-sig')
    names={c:re.sub(r'[^a-z0-9]+','_',str(c).strip().lower()).strip('_') for c in raw.columns}
    raw=raw.rename(columns=names)
    page=next((x for x in ('page','pages','top_pages','url','landing_page') if x in raw.columns),None)
    impressions=next((x for x in ('impressions','ai_impressions','impression') if x in raw.columns),None)
    if not page or not impressions:
        raise ValueError('Expected columns such as Pages and Impressions from the dedicated GSC Generative AI performance report.')
    d=raw[[page,impressions]].copy()
    d.columns=['Page','AI Search impressions']
    d['Page']=d['Page'].fillna('').astype(str).str.strip()
    d['AI Search impressions']=pd.to_numeric(d['AI Search impressions'].astype(str).str.replace(',','',regex=False),errors='coerce').fillna(0)
    d=d[d['Page'].str.startswith(('https://','http://'))].copy()
    d=d.groupby('Page',as_index=False)['AI Search impressions'].sum()
    return d.sort_values('AI Search impressions',ascending=False)
