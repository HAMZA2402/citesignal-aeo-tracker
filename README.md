# CiteSignal — AI Visibility & AEO Tracker (V1)

A free, browser-based, **evidence-first** visibility measurement tool built with Python and Streamlit.

## What this version actually does

- Builds reproducible buyer-intent prompt plans for services and locations.
- Imports manual AI-answer observations in the included CSV template.
- Tracks **brand mentioned**, **exact website domain cited**, and **brand explicitly recommended** separately.
- Counts known Yes/No values, excluding Unknown from each metric's denominator.
- Compares engines, captures competitor mentions and cited domains, highlights gaps, and tracks weekly samples.
- Generates Excel and CSV reports with raw evidence, quality checks and methodology notes.
- Optionally imports a **Pages** CSV/XLSX from the dedicated Google Search Console **Generative AI performance (Search)** report; keeps AI-feature link impressions separate from prompt citations.
- Provides **fictional demo data** so anyone can explore the app without making claims about real AI search results.

## What this version does NOT do

- It does **not** automatically scrape ChatGPT, Google, Perplexity, Gemini or Bing.
- It does **not** measure platform-wide market share, actual AI referrals, or causal SEO lift.
- It does **not** store client files on a permanent database. Uploaded data may be in Streamlit session memory only.
- It does **not** equate grounded API responses with consumer product output.

## How to run

1. `pip install -r requirements.txt`
2. `streamlit run app.py`
3. Click **Load fictional demo** and explore the tabs.
4. Download `demo/observation_template.csv` and record real observations in a local file.
5. Upload your verified observation CSV, set brand and exact website domain, then download reports.
6. Optionally export **Pages** from Google Search Console → **Generative AI performance (Search)** and import it with the source confirmation checkbox. These are AI-feature link impressions, not per-prompt citations.
7. Keep the CSV for future runs. Use a consistent prompt, location, surface and date tracking plan.

## GitHub / Streamlit Community Cloud

Create a **new repository**, separate from existing SEO/LinkScope apps. Upload `app.py`, `aeo_engine.py`, `reporting.py`, `requirements.txt` and the `demo` folder to the repository **root**. Deploy with main file `app.py` on Streamlit Community Cloud. No API key is required in V1.

Do not commit real client data or private screenshots to a public repository. Do not expose private observations through an unauthenticated public deployment. Prefer demo data in a public showcase and a privately managed environment for client work.

## Analysis protocol

For each prompt, record engine, location, date, identical prompt text, cited URLs (if any), explicit brand mention status, explicit recommendation status, competitor brands, and a screenshot or evidence reference. Mark missing data as **Unknown**, not No. A citation link to `brand.example` is only counted when the URL's host equals that domain or a subdomain; a similar-looking domain does not count.

Response sampling must not be confused with user queries. Results can vary by user, model version, location, date, and personalization. Treat findings as directional until repeated on matched prompt cohorts.

## Planned V2 (optional paid integrations)

- Extend GSC AI report import to date/country/device comparisons and quality-controlled historical cohorts.
- Optional APIs: OpenAI Responses web search, Gemini Google Search grounding, Perplexity, and Google AI Overview / AI Mode SERP provider such as DataForSEO. Keys kept in Streamlit Secrets; cost limits and run budgets required.
- Durable database, accounts/permissions, scheduled prompt cohorts, evidence history, multi-client segmentation, quality gates.
- API-based results labeled **API**, not mislabeled as ChatGPT/Gemini native UI observations.

## Documentation

- Google Search Console Generative AI Performance: https://support.google.com/webmasters/answer/16984139?hl=en
- OpenAI Responses API web search: https://developers.openai.com/api/docs/guides/tools-web-search
- Gemini Search grounding: https://ai.google.dev/gemini-api/docs/google-search
- DataForSEO AI Overview: https://dataforseo.com/help-center/how-to-scrape-google-ai-overviews-with-serp-api
- Streamlit deployment: https://docs.streamlit.io/deploy/streamlit-community-cloud

This demo contains invented organizations and observations. They must not be described as real-world AI search measurements.
