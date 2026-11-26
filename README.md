# AI Equity Research Assistant

# EquityBot :- News Research Tool

EquityBot is a news research tool for fast, grounded information retrieval. Users paste financial-news article URLs and ask questions; the app answers only from those articles and cites the source URLs.

**Live app:** https://equity-research-tool-465.streamlit.app

## Features

- Load up to 3 news-article URLs and scrape them with LangChain's `WebBaseLoader` (browser-like headers, fails loudly on HTTP errors).
- Flags pages that look blocked or empty instead of silently indexing an error page.
- Split text with `RecursiveCharacterTextSplitter` (chunk size 1000, overlap 200).
- Embed chunks with OpenAI embeddings (`text-embedding-3-small`) and index them in FAISS for fast similarity search.
- Answer questions with an OpenAI chat model (`gpt-4o-mini` by default, temperature 0) through a retrieval QA chain that returns source URLs, and says "I don't know" when the articles don't contain the answer.
- Optional "Show debug info" view: scraped-text preview and the retrieved chunks with their similarity distances.

## Installation

1. Clone this repository:

```bash
git clone https://github.com/singhsiddhant465/Equity-Research-Tool.git
cd Equity-Research-Tool
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux
```

3. Install the dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with your OpenAI API key:

```bash
OPENAI_API_KEY=your_api_key_here
# optional overrides
# OPENAI_MODEL=gpt-4o-mini
# OPENAI_EMBED_MODEL=text-embedding-3-small
```

## Usage

1. Run the Streamlit app:

```bash
streamlit run main.py
```

2. The app opens at http://localhost:8501.

- Paste up to 3 article URLs in the sidebar and click **Process URLs**.
- The app scrapes the pages, splits the text into chunks, embeds them and saves a FAISS index locally.
- Ask a question. The answer is generated only from the retrieved chunks, with source URLs.

### Example URLs

- https://rbi.org.in/scriptS/BS_PressReleaseDisplay.aspx?prid=63742
- https://scroll.in/latest/1092967/rupee-slumps-to-all-time-low-of-96-8-against-us-dollar
- https://www.deccanherald.com/business/rupee-falls-to-record-low-of-9647-against-us-dollar-in-intraday-trade-4008359

### Example questions

- What did the RBI do to the repo rate in October 2026?
- Why did the rupee fall to a record low?
- What Balance of Payments deficit do HSBC economists expect for FY27?

Note: some news sites block requests from cloud servers. The app shows a warning when a page looks blocked.

## Project Structure

- `main.py`: the Streamlit application.
- `requirements.txt`: Python dependencies.
- `faiss_store_openai/`: the saved FAISS index (`index.faiss` + `index.pkl`), created when you process URLs.
- `.env`: your OpenAI API key (not committed).
- `text_loaders_splitters.ipynb`: notebook exploring loaders and text splitters.

## Author

Siddhant Singh
