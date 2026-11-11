"""Excel export with traceable evidence and formula-driven KPI summary."""
from io import BytesIO
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.workbook.properties import CalcProperties

NAVY='172943'; TEAL='0E766D'; WHITE='FFFFFF'; PALE='E7F4F3'
METHODS=[
 ('Metric','Definition / limitation'),
 ('Observation','One recorded answer for one prompt, engine, date, and location; repeat observations may be retained.'),
 ('Mention rate','Count Yes / count (Yes + No) for brand_mentioned; Unknown excluded.'),
 ('Citation rate','Count Yes / count (Yes + No) for brand_cited, based on exact configured domain in explicitly checked cited URLs.'),
 ('Recommendation rate','Count Yes / count (Yes + No) for brand_recommended; requires an explicit positive recommendation.'),
 ('Confidence','This is a selected observational sample, not representative AI-search market share or user traffic.'),
 ('Google AI Search Console','The optional Google Generative AI performance report measures impressions of site links in Google AI features, not AI prompt-specific citations.'),
 ('Platforms','Grounded API responses can differ from the consumer UI experience. Do not label API observations as consumer UI observations.'),
 ('Privacy','V1 does not save uploads across sessions. Export the evidence ledger before refreshing. Use demo data on public apps.'),
 ('Methodology','Missing/unknown measurements are not treated as negative results.'),
 ('Google reference','https://support.google.com/webmasters/answer/16984139?hl=en'),
 ('OpenAI reference','https://developers.openai.com/api/docs/guides/tools-web-search'),
]


def add_frame(wb,name,df):
    ws=wb.create_sheet(name)
    if df is None or df.empty:
        ws.append(['No data recorded'])
    else:
        ws.append(list(df.columns))
        for row in df.itertuples(index=False,name=None):
            ws.append([None if pd.isna(v) else v for v in row])
    decorate(ws)
    return ws


def decorate(ws):
    ws.sheet_view.showGridLines=False
    ws.freeze_panes='A2'
    if ws.max_row>=2:ws.auto_filter.ref=f'A1:{get_column_letter(ws.max_column)}{ws.max_row}'
    for c in ws[1]:
        c.fill=PatternFill('solid',fgColor=NAVY)
        c.font=Font(color=WHITE,bold=True)
        c.alignment=Alignment(vertical='center',wrap_text=True)
    ws.row_dimensions[1].height=32
    for col in ws.columns:
        items=list(col); title=str(items[0].value or '').lower()
        size=max([len(str(c.value or '')) for c in items[:min(len(items),60)]]+[14])
        size=min(54,max(16,size+2))
        if any(k in title for k in ('prompt','url','action','evidence','definition','excerpt')):size=min(74,max(38,size))
        ws.column_dimensions[items[0].column_letter].width=size
    for row in ws.iter_rows(min_row=2):
        ws.row_dimensions[row[0].row].height=29
        for c in row:
            c.alignment=Alignment(vertical='top',wrap_text=True)
            if c.row%2==0:c.fill=PatternFill('solid',fgColor='F3F7F9')
            if ws.title=='Evidence Ledger': c.font=Font(color='00703C',size=10)


def export_excel(brand,domain,ledger,engine_stats,gaps,comp,quality,prompt_plan,gsc_pages=None):
    wb=Workbook()
    wb.calculation=CalcProperties(calcMode='auto',fullCalcOnLoad=True)
    summary=wb.active
    summary.title='Executive Summary'
    summary.merge_cells('A1:C1')
    summary['A1']='CITESIGNAL | AI ANSWER EVIDENCE REPORT'
    summary['A1'].fill=PatternFill('solid',fgColor=NAVY)
    summary['A1'].font=Font(size=15,bold=True,color=WHITE)
    summary.row_dimensions[1].height=40
    end_row=max(1001,len(ledger)+101)
    values=[('Brand',brand),('Domain',domain),('Data classification','Selected observational sample; not AI-search population'),
        ('Observed answers',"=COUNTA('Evidence Ledger'!C2:C100001)"),
        ('Verified answers',"=COUNTIF('Evidence Ledger'!L2:L100001,\"Yes\")"),
        ('Brand mentioned (Yes)',"=COUNTIF('Evidence Ledger'!G2:G100001,\"Yes\")"),
        ('Brand mention measured',"=COUNTIF('Evidence Ledger'!G2:G100001,\"Yes\")+COUNTIF('Evidence Ledger'!G2:G100001,\"No\")"),
        ('Brand mention rate','=IFERROR(B7/B8,0)'),
        ('Brand cited (Yes)',"=COUNTIF('Evidence Ledger'!P2:P100001,\"Yes\")"),
        ('Citations measured',"=COUNTIF('Evidence Ledger'!P2:P100001,\"Yes\")+COUNTIF('Evidence Ledger'!P2:P100001,\"No\")"),
        ('Domain citation rate','=IFERROR(B10/B11,0)'),
        ('Brand recommended (Yes)',"=COUNTIF('Evidence Ledger'!H2:H100001,\"Yes\")"),
        ('Recommendation measured',"=COUNTIF('Evidence Ledger'!H2:H100001,\"Yes\")+COUNTIF('Evidence Ledger'!H2:H100001,\"No\")"),
        ('Recommendation rate','=IFERROR(B13/B14,0)')]
    for key,value in values:
        if isinstance(value,str) and '100001' in value:value=value.replace('100001',str(end_row))
        summary.append([key,value])
    # Rows 2-16; ratio row indexes 10,13,16 reference numerator and denominator above.
    for row in (9,12,15):summary[f'B{row}'].number_format='0.0%'
    for row in summary.iter_rows(min_row=2,max_col=2):
        row[0].font=Font(color=NAVY,bold=True)
        row[0].fill=PatternFill('solid',fgColor=PALE)
        row[0].alignment=Alignment(wrap_text=True)
    summary.column_dimensions['A'].width=33
    summary.column_dimensions['B'].width=65
    summary.sheet_view.showGridLines=False
    summary.freeze_panes='A2'
    add_frame(wb,'Engine Breakdown',engine_stats)
    add_frame(wb,'Prompt Opportunities',gaps)
    add_frame(wb,'Competitor Mentions',comp)
    add_frame(wb,'Prompt Plan',prompt_plan)
    add_frame(wb,'Evidence Ledger',ledger)
    add_frame(wb,'Data Quality',quality)
    if gsc_pages is not None and not gsc_pages.empty:
        add_frame(wb,'GSC AI Search Pages',gsc_pages)
    m=wb.create_sheet('Methodology')
    m.append(list(METHODS[0]))
    for row in METHODS[1:]:m.append(list(row))
    decorate(m)
    m.column_dimensions['A'].width=30
    m.column_dimensions['B'].width=105
    buf=BytesIO();wb.save(buf)
    return buf.getvalue()
