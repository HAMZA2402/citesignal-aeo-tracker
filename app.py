"""CiteSignal V1 — an agency-focused, evidence-first AEO tracker."""
from pathlib import Path
from datetime import date
from uuid import uuid4
from io import BytesIO
from urllib.parse import urlsplit
import hashlib
import pandas as pd
import plotly.express as px
import streamlit as st
from aeo_engine import (SCHEMA, ENGINES, INTENTS, normalize, clean_domain, evidence,
                        rates, engine_summary, competitor_summary, prompt_gaps,
                        quality_notes, weekly_trend, prompt_builder, split_items)
from reporting import export_excel
from gsc_ai import load_gsc_pages

st.set_page_config(page_title='CiteSignal — AI Visibility Intelligence',page_icon='📡',layout='wide')
st.markdown('''<style>
[data-testid="stMetric"] {border:1px solid #d7e5e7;border-radius:12px;padding:12px;background:rgba(35,140,135,.04)}
.block-container {padding-top:1.4rem}
.small-note {color:#667487;font-size:0.92rem}
</style>''',unsafe_allow_html=True)

st.title('📡 CiteSignal | AI Answer Intelligence')
st.caption('Evidence-first brand mentions, cited sources, prompt coverage and competitor presence • V1')
st.info('**Measurement note:** V1 evaluates answers you record or upload. It does not automatically query ChatGPT, Google AI Overviews, AI Mode, Gemini, or Perplexity. All sample visibility rates refer only to your observations.')

if 'observations' not in st.session_state:
    st.session_state.observations=pd.DataFrame(columns=SCHEMA)
if 'file_hash' not in st.session_state:
    st.session_state.file_hash=None
if 'upload_serial' not in st.session_state:
    st.session_state.upload_serial=0

with st.sidebar:
    st.header('Client settings')
    brand=st.text_input('Brand name',value='Harborline Legal',help='Fictional demo brand; change before importing client evidence.')
    domain=st.text_input('Official website domain',value='harborlinelegal.example')
    domain=clean_domain(domain)
    location=st.text_input('Target location',value='Exampleville, California')
    service=st.text_input('Primary service',value='estate planning attorney')
    st.divider()
    st.header('Evidence source')
    uploaded=st.file_uploader('Import observation ledger',type=['csv','xlsx'],key=f'observations_{st.session_state.upload_serial}',help='Use the supplied template; uploading replaces observations in this browser session.')
    if uploaded is not None:
        payload=uploaded.getvalue()
        digest=hashlib.sha256(payload).hexdigest()
        if st.session_state.file_hash!=digest:
            try:
                raw=pd.read_excel(BytesIO(payload)) if uploaded.name.lower().endswith('.xlsx') else pd.read_csv(BytesIO(payload),keep_default_na=False)
                st.session_state.observations=normalize(raw)
                st.session_state.file_hash=digest
                st.success(f'Loaded {len(st.session_state.observations)} observations')
            except Exception as exc:
                st.error(f'Could not read file: {exc}')
    if st.button('Load fictional demo',use_container_width=True):
        st.session_state.observations=normalize(pd.read_csv(Path(__file__).parent/'demo'/'fictional_observations.csv',keep_default_na=False))
        st.rerun()
    if st.button('Clear evidence from session',use_container_width=True):
        st.session_state.observations=pd.DataFrame(columns=SCHEMA)
        st.session_state.file_hash=None
        st.session_state.upload_serial+=1
        st.rerun()
    st.caption('Uploaded observations are held in this Streamlit session. Export before refreshing. A publicly accessible app is not a private client database.')
    st.divider()
    st.header('Google AI Search evidence')
    st.caption('Optional: only from GSC → Generative AI performance (Search) → Pages export.')
    gsc_confirm=st.checkbox('This is the dedicated GSC Generative AI report',value=False)
    gsc_upload=st.file_uploader('GSC AI pages CSV or XLSX',type=['csv','xlsx'],key='gsc_upload')

gsc_pages=None
if gsc_upload is not None and gsc_confirm:
    try:gsc_pages=load_gsc_pages(gsc_upload.getvalue(),gsc_upload.name)
    except Exception as exc:st.sidebar.error(f'GSC file issue: {exc}')

dataset=evidence(st.session_state.observations,domain)
with st.expander('Add a manually observed AI answer',expanded=dataset.empty):
    with st.form('manual_observation',clear_on_submit=True):
        a,b,c=st.columns(3)
        with a:
            observed=st.date_input('Observation date',value=date.today())
            engine=st.selectbox('AI surface',ENGINES)
            p_location=st.text_input('Location used',value=location)
        with b:
            intent=st.selectbox('Prompt intent',INTENTS)
            mentioned=st.selectbox('Brand mentioned?', ['Unknown','Yes','No'])
            recommended=st.selectbox('Explicitly recommended?', ['Unknown','Yes','No'])
        with c:
            citation_checked=st.selectbox('Citation URLs checked?', ['Unknown','Yes','No'],help='Yes: you checked citation links (including none); No/Unknown: not verified. Any non-empty cited URLs need Yes.')
            verified=st.selectbox('Observation verified?', ['No','Yes'])
            analyst=st.text_input('Analyst',value='')
        prompt=st.text_area('Exact prompt entered',height=80)
        cited=st.text_area('Cited URLs (one per line or separated by |)',height=80)
        competitors=st.text_input('Competitor brands mentioned (separate by |)')
        excerpt=st.text_area('Relevant answer excerpt (optional)',height=80)
        ref=st.text_input('Evidence reference (saved screenshot ID, link or file reference)')
        submitted=st.form_submit_button('Add evidence row',type='primary')
        if submitted:
            if not prompt.strip():st.error('Please enter the exact prompt.')
            elif cited.strip() and citation_checked!='Yes':st.error('Choose Yes for Citation URLs checked if you supply cited URLs.')
            else:
                record={'record_id':'obs-'+uuid4().hex[:10], 'observed_date':observed.isoformat(),
                    'engine':engine,'prompt':prompt.strip(),'location':p_location.strip(),'intent':intent,
                    'brand_mentioned':mentioned,'brand_recommended':recommended,'citations_checked':citation_checked,
                    'cited_urls':' | '.join(split_items(cited)),'competitor_mentions':competitors.strip(),
                    'verified':verified,'evidence_reference':ref.strip(),'answer_excerpt':excerpt.strip(),'analyst':analyst.strip()}
                st.session_state.observations=pd.concat([st.session_state.observations,pd.DataFrame([record])],ignore_index=True)
                st.success('Recorded. Export the evidence ledger to preserve your work.')
                st.rerun()

if dataset.empty:
    st.warning('No observations loaded. Choose **Load fictional demo**, import your CSV, or add an answer above.')
else:
    with st.expander('Dashboard filters',expanded=False):
        cols=st.columns(2)
        selected=cols[0].multiselect('AI surfaces',sorted(dataset.engine.unique()),default=sorted(dataset.engine.unique()))
        verified_only=cols[1].checkbox('Only verified observations',value=True)
    filtered=dataset[dataset.engine.isin(selected)]
    if verified_only:filtered=filtered[filtered.verified=='Yes']
    filtered=filtered.copy()
    if filtered.empty:st.warning('No records match your filters. Uncheck verified-only or select another AI surface.')
    else:
        summary=rates(filtered)
        def p(key):return '—' if summary[key] is None else f'{summary[key]:.1f}%'
        m=st.columns(5)
        m[0].metric('Observed answers',summary['observations'])
        m[1].metric('Brand mentioned',p('mention_pct'))
        m[2].metric('Domain cited',p('citation_pct'))
        m[3].metric('Explicitly recommended',p('recommendation_pct'))
        m[4].metric('Competitor present',summary['competitor_observations'])
        st.caption(f"Denominators: mentioned {summary['mention_measured']}, cited {summary['citation_measured']}, recommended {summary['recommendation_measured']}. A small or manually selected sample is not platform-wide market share.")
        tab1,tab2,tab3,tab4,tab5=st.tabs(['📊 Visibility','🧾 Evidence ledger','⚔️ Competitors & sources','🧭 Prompt gaps','📤 Exports & QA'])
        with tab1:
            st.subheader('Answer presence by AI surface')
            platform=engine_summary(filtered)
            st.dataframe(platform,use_container_width=True,hide_index=True)
            if len(platform):
                shown=platform[['Engine','Mention rate %','Citation rate %','Recommendation rate %']].melt('Engine',var_name='Outcome',value_name='Observed rate %').dropna()
                if len(shown):st.plotly_chart(px.bar(shown,x='Engine',y='Observed rate %',color='Outcome',barmode='group',title='Sample-based rates (not market share)'),use_container_width=True)
            trend=weekly_trend(filtered)
            if len(trend)>1:
                st.subheader('Weekly changes in selected observations')
                st.plotly_chart(px.line(trend,x='Week',y=['Brand mention %','Domain citation %'],markers=True),use_container_width=True)
                st.caption('A change may reflect different prompts, surfaces or sample sizes. Use matched prompt sets for reliable comparisons.')
            else:st.caption('A trend chart needs observations spanning at least two different weeks.')
        with tab2:
            st.subheader('Traceable answer observations')
            st.dataframe(filtered,use_container_width=True,hide_index=True,height=390)
            st.download_button('Download evidence ledger CSV',data=dataset[SCHEMA].to_csv(index=False).encode('utf-8-sig'),file_name='CiteSignal_Evidence_Ledger.csv',mime='text/csv')
            st.caption('The CSV export includes **all** session observations, including filtered-out and unverified records. Re-upload it to continue your analysis later.')
        with tab3:
            competitor=competitor_summary(filtered)
            st.subheader('Competitors mentioned in recorded answers')
            if competitor.empty:st.info('No competitor brand names recorded in this sample.')
            else:
                st.dataframe(competitor,use_container_width=True,hide_index=True)
                st.plotly_chart(px.bar(competitor.head(15),x='Competitor',y='Observed answers',title='Competitor mentions in sample'),use_container_width=True)
            st.subheader('Cited source domains')
            from collections import Counter
            domains=Counter()
            for raw in filtered['cited_urls']:
                for url in split_items(raw):
                    try:
                        host=(urlsplit(url).hostname or '').lower()
                        if host:domains[host]+=1
                    except ValueError:pass
            if domains:
                source=pd.DataFrame([{'Cited domain':d,'Linked URLs observed':n} for d,n in domains.most_common(20)])
                st.dataframe(source,use_container_width=True,hide_index=True)
            else:st.info('No cited URLs entered.')
        with tab4:
            gap=prompt_gaps(filtered)
            st.subheader('Where answer coverage is weak')
            if len(gap):st.dataframe(gap,use_container_width=True,hide_index=True,height=460)
            st.caption('These are review actions inferred from the **recorded observations**. They are not claims that an AI platform will cite a page after editing it.')
        with tab5:
            qa=quality_notes(dataset)
            st.subheader('Evidence QA')
            st.write(f'Unresolved evidence-quality flags: **{len(qa)}**')
            if not qa.empty:st.dataframe(qa,use_container_width=True,hide_index=True)
            output=export_excel(brand,domain,filtered,engine_summary(filtered),prompt_gaps(filtered),competitor_summary(filtered),quality_notes(filtered),prompt_builder(service,location,brand),gsc_pages)
            st.download_button('Download agency-style Excel report',data=output,file_name='CiteSignal_AEO_Visibility_Audit.xlsx',mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',type='primary')

st.divider()
st.subheader('🔎 Google AI Search Console: page-level impressions')
if gsc_pages is not None and not gsc_pages.empty:
    st.metric('Imported Google AI-feature link impressions',f"{gsc_pages['AI Search impressions'].sum():,.0f}")
    st.dataframe(gsc_pages.head(100),use_container_width=True,hide_index=True)
    st.bar_chart(gsc_pages.head(12).set_index('Page')['AI Search impressions'])
    st.download_button('Download GSC AI pages CSV',gsc_pages.to_csv(index=False).encode('utf-8-sig'),'CiteSignal_GSC_AI_Pages.csv','text/csv')
else:
    st.caption('Optional: upload a Pages CSV from Google Search Console’s dedicated Generative AI performance report and confirm its source in the sidebar.')
st.caption('GSC AI link impressions are NOT the same as prompt-level citations, brand mentions, or AI referral visits. These metrics are deliberately kept separate.')

st.divider()
st.subheader('🧠 Prompt Intelligence Builder')
st.caption('Generates a controlled prompt set across buyer intent; it does not automatically submit prompts to AI platforms.')
plan=prompt_builder(service,location,brand)
st.dataframe(plan,use_container_width=True,hide_index=True)
st.download_button('Download prompt plan CSV',plan.to_csv(index=False).encode('utf-8-sig'),file_name='CiteSignal_Prompt_Plan.csv',mime='text/csv')
st.caption('Track identical prompts, locations, surfaces and capture conditions over time. Record evidence before reporting a citation as fact.')
