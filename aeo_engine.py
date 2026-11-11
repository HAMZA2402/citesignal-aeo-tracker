"""Evidence-based AEO visibility analytics; not a search engine scraper."""
from urllib.parse import urlsplit
from collections import Counter
import re
import pandas as pd

SCHEMA = ['record_id','observed_date','engine','prompt','location','intent',
          'brand_mentioned','brand_recommended','citations_checked','cited_urls',
          'competitor_mentions','verified','evidence_reference','answer_excerpt','analyst']
ENGINES = ['ChatGPT Search','Google AI Overview','Google AI Mode','Gemini','Perplexity','Copilot','Other']
INTENTS = ['Discover','Compare','Decision','Educational','Local','Branded','Other']


def clean_domain(value):
    s = str(value or '').strip().lower()
    if not s: return ''
    if not s.startswith(('https://','http://')): s = 'https://' + s
    try: host = (urlsplit(s).hostname or '').lower().rstrip('.')
    except ValueError: return ''
    return host[4:] if host.startswith('www.') else host


def host_matches(url, domain):
    domain = clean_domain(domain)
    url = str(url or '').strip()
    if not domain or '.' not in domain or not url.startswith(('https://','http://')): return False
    try: host = (urlsplit(url).hostname or '').lower().rstrip('.')
    except ValueError: return False
    return host == domain or host.endswith('.' + domain)


def split_items(value):
    value = str(value or '').strip()
    if not value or value.lower() in ('nan','none'): return []
    return list(dict.fromkeys(x.strip() for x in re.split(r'[|\n;]+',value) if x.strip()))


def ternary(value):
    s = str(value or '').strip().lower()
    if s in ('yes','true','y','1','present'): return 'Yes'
    if s in ('no','false','n','0','absent'): return 'No'
    return 'Unknown'


def normalize(raw):
    if raw is None: return pd.DataFrame(columns=SCHEMA)
    d = raw.copy()
    d.columns = [str(c).strip().lower().replace(' ','_') for c in d.columns]
    if not {'engine','prompt'}.issubset(d.columns):
        raise ValueError('File must contain engine and prompt columns. Use the CSV template.')
    for c in SCHEMA:
        if c not in d.columns: d[c] = ''
    d = d[SCHEMA].fillna('').astype(str)
    for c in ['brand_mentioned','brand_recommended','citations_checked','verified']:
        d[c] = d[c].map(ternary)
    d['observed_date'] = pd.to_datetime(d['observed_date'],errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
    d['engine'] = d['engine'].str.strip()
    d['prompt'] = d['prompt'].str.strip()
    return d[(d['engine']!='')&(d['prompt']!='')].reset_index(drop=True)


def evidence(raw, domain):
    d = normalize(raw)
    d['brand_cited'] = [
        'Yes' if ck=='Yes' and any(host_matches(u,domain) for u in split_items(urls)) else ('No' if ck=='Yes' else 'Unknown')
        for urls,ck in zip(d['cited_urls'],d['citations_checked'])]
    d['competitor_count'] = d['competitor_mentions'].map(lambda s:len(split_items(s)))
    d['evidence_quality'] = [
        'Verified + reference' if v=='Yes' and str(ref).strip() else
        'Verified - missing reference' if v=='Yes' else 'Unverified'
        for v,ref in zip(d['verified'],d['evidence_reference'])]
    return d


def rates(d):
    r = {'observations':len(d),'verified_observations':int((d['verified']=='Yes').sum())}
    for col, name in [('brand_mentioned','mention'),('brand_cited','citation'),('brand_recommended','recommendation')]:
        den = int(d[col].isin(['Yes','No']).sum())
        num = int((d[col]=='Yes').sum())
        r[name+'_yes'] = num
        r[name+'_measured'] = den
        r[name+'_pct'] = num/den*100 if den else None
    r['competitor_observations'] = int((d['competitor_count']>0).sum())
    return r


def engine_summary(d):
    rows=[]
    for engine,g in d.groupby('engine'):
        r=rates(g)
        rows.append({'Engine':engine,'Observations':r['observations'],
                     'Mention rate %':r['mention_pct'],'Mention measured':r['mention_measured'],
                     'Citation rate %':r['citation_pct'],'Citation measured':r['citation_measured'],
                     'Recommendation rate %':r['recommendation_pct'],
                     'Recommendation measured':r['recommendation_measured'],
                     'Competitor observations':r['competitor_observations']})
    return pd.DataFrame(rows)


def competitor_summary(d):
    counts=Counter(); platforms={}
    for _,row in d.iterrows():
        for name in split_items(row['competitor_mentions']):
            counts[name]+=1
            platforms.setdefault(name,set()).add(row['engine'])
    return pd.DataFrame([{'Competitor':name,'Observed answers':n,
       'Engines':', '.join(sorted(platforms[name]))} for name,n in counts.most_common()])

def prompt_gaps(d):
    rows=[]
    if d.empty: return pd.DataFrame()
    for (eng,prompt,loc,intent),g in d.groupby(['engine','prompt','location','intent']):
        r=rates(g)
        if r['mention_measured']==0:
            finding,action='Not measured','Record an observation with known Yes/No brand mention.'
        elif r['mention_yes']==0 and r['competitor_observations']>0:
            finding,action='Competitor-only answer','Review competitors and cited sources; identify service evidence absent from your site.'
        elif r['mention_yes']==0:
            finding,action='Brand absent','Check if a relevant service or location page answers the prompt intent.'
        elif r['citation_yes']==0 and r['citation_measured']>0:
            finding,action='Mention without domain citation','Inspect source citations; improve relevant pages with verifiable factual information.'
        elif r['recommendation_yes']==0 and r['recommendation_measured']>0:
            finding,action='Mentioned but not recommended','Review service fit, documented proof, and source trust.'
        else:
            finding,action='Present in sample','Monitor repeated captures under consistent conditions.'
        rows.append({'Engine':eng,'Prompt':prompt,'Location':loc,'Intent':intent,
                     'Observations':len(g),'Brand mentions':r['mention_yes'],
                     'Domain citations':r['citation_yes'],
                     'Competitor observations':r['competitor_observations'],
                     'Finding':finding,'Suggested review action':action})
    return pd.DataFrame(rows).sort_values(['Competitor observations','Observations'],ascending=[False,False])


def quality_notes(d):
    issues=[]
    for i,row in d.iterrows():
        id_=row['record_id'] or f'row-{i+1}'
        if row['verified']!='Yes':issues.append([id_,'Unverified','Review the original answer.'])
        elif not row['evidence_reference'].strip():issues.append([id_,'Missing reference','Add screenshot ID or saved evidence location.'])
        if row['brand_mentioned']=='Unknown':issues.append([id_,'Mention unmeasured','Mark Yes or No after checking.'])
        if row['citations_checked']!='Yes':issues.append([id_,'Citations unconfirmed','Record whether citation links were checked.'])
        if row['brand_recommended']=='Unknown':issues.append([id_,'Recommendation unmeasured','Mark explicit recommendation Yes or No.'])
    return pd.DataFrame(issues,columns=['Record ID','Issue','Suggested fix'])


def weekly_trend(d):
    if d.empty: return pd.DataFrame()
    dated=d.copy()
    dated['date']=pd.to_datetime(dated['observed_date'],errors='coerce')
    dated=dated.dropna(subset=['date'])
    if dated.empty:return pd.DataFrame()
    dated['Week']=dated['date'].dt.to_period('W').dt.start_time.dt.strftime('%Y-%m-%d')
    rows=[]
    for week,g in dated.groupby('Week'):
        r=rates(g)
        rows.append({'Week':week,'Responses observed':len(g),'Brand mention %':r['mention_pct'],
                     'Domain citation %':r['citation_pct']})
    return pd.DataFrame(rows)


def prompt_builder(service, location, brand=''):
    service=service.strip() or 'estate planning lawyer'
    location=location.strip() or 'Exampleville'
    templates=[
      ('Discover',f'Who are reputable {service}s in {location}?'),
      ('Compare',f'How do I compare {service}s in {location}?'),
      ('Decision',f'Which {service} would suit a first consultation in {location}?'),
      ('Local',f'Where can I find a {service} near {location}?'),
      ('Educational',f'What should I ask a {service} before hiring?'),
      ('Educational',f'What does a {service} typically help with?'),
      ('Decision',f'What might a {service} cost in {location}?'),
      ('Compare',f'What are alternatives to hiring a {service} in {location}?')]
    if brand.strip():templates.append(('Branded',f'What should I know about {brand.strip()} before contacting them?'))
    return pd.DataFrame([{'Intent':i,'Prompt':p,'Location':location,'Suggested cadence':'Monthly',
                          'Status':'Not measured'} for i,p in templates])
