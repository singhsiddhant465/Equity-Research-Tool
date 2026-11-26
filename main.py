import os
import streamlit as st
import time

from langchain_openai import ChatOpenAI
from langchain_classic.chains import RetrievalQAWithSourcesChain
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from dotenv import load_dotenv
load_dotenv()

# ======================
# CHECK API KEY
# ======================
if not os.getenv("OPENAI_API_KEY"):
    st.error("OPENAI_API_KEY not found in .env file")
    st.stop()

# ======================
# UI
# ======================
st.title("Equity Research Tool 📈")
st.sidebar.title("News Article URLs")

urls = [st.sidebar.text_input(f"URL {i+1}") for i in range(3)]
process_url_clicked = st.sidebar.button("Process URLs")

faiss_store_path = "faiss_store_openai"
main_placeholder = st.empty()

# ======================
# MODELS
# ======================
# gpt-3.5-turbo-instruct was retired by OpenAI, so use a chat model.
# Override with OPENAI_MODEL in .env / Streamlit secrets without touching code.
LLM_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

# temperature=0 keeps answers grounded in the retrieved articles
llm = ChatOpenAI(model=LLM_MODEL, temperature=0, max_tokens=500)

# ======================
# PROCESS URLS
# ======================

if process_url_clicked:

    urls = [u.strip() for u in urls if u.strip()]
    if not urls:
        st.error("Please enter at least one valid URL")
        st.stop()

    main_placeholder.text("Data Loading...Started...")

    try:
        loader = WebBaseLoader(
            web_paths=urls,
            header_template={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/124.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            },
            raise_for_status=True,   # a 403/404 page now raises instead of being indexed as "content"
        )
        data = loader.load()
    except Exception as e:
        st.error(f"Error loading URLs (site may block cloud servers): {str(e)}")
        st.stop()

    # Show what was actually scraped, and flag pages that are blocks, not articles
    BLOCK_MARKERS = ["access denied", "captcha", "enable javascript", "are you a robot", "forbidden"]
    with st.expander("Loaded content preview (debug)"):
        for d in data:
            text = " ".join(d.page_content.split())
            st.write(f"**{d.metadata.get('source')}** \u2014 {len(text):,} characters")
            st.caption(text[:400] + ("..." if len(text) > 400 else ""))
            if len(text) < 1000 or any(m in text.lower() for m in BLOCK_MARKERS):
                st.warning("This page looks blocked or empty, not a full article.")

    if not data:
        st.error("No content could be loaded.")
        st.stop()

    main_placeholder.text("Data Loading...Completed!")


    # ======================
    # VALIDATION
    # ======================
    if not data:
        st.error("No data loaded. URLs might be blocked on Streamlit.")
        st.stop()

    # ======================
    # SPLITTING
    # ======================
    main_placeholder.text("Text Splitter...Started...")

    text_splitter = RecursiveCharacterTextSplitter(
        separators=['\n\n', '\n', '.', ','],
        chunk_size=1000,
        chunk_overlap=200
    )

    docs = text_splitter.split_documents(data)

    # remove empty docs
    docs = [doc for doc in docs if doc.page_content and doc.page_content.strip()]

    if len(docs) == 0:
        st.error("No valid content after splitting.")
        st.stop()

    st.write(f"Documents created: {len(docs)}")

    # ======================
    # EMBEDDINGS + FAISS
    # ======================
    main_placeholder.text("Embedding Vector Building...")

    try:
        embeddings = OpenAIEmbeddings(model=EMBED_MODEL)
        vectorstore_openai = FAISS.from_documents(docs, embeddings)
    except Exception as e:
        st.error(f"Embedding/FAISS error: {str(e)}")
        st.stop()

    vectorstore_openai.save_local(faiss_store_path)

    time.sleep(1)
    st.success("Processing complete!")

# ======================
# QUERY
# ======================
query = st.text_input("Question:")

if query:

    if not os.path.exists(faiss_store_path):
        st.error("Please process URLs first")
        st.stop()

    try:
        embeddings = OpenAIEmbeddings(model=EMBED_MODEL)
        vectorstore = FAISS.load_local(
            faiss_store_path,
            embeddings,
            allow_dangerous_deserialization=True
        )
    except Exception as e:
        st.error(f"Error loading FAISS index: {str(e)}")
        st.stop()

    # Show which chunks retrieval picked (lower score = closer match for FAISS L2)
    with st.expander("Retrieved chunks (debug)"):
        for doc, score in vectorstore.similarity_search_with_score(query, k=4):
            st.write(f"**{doc.metadata.get('source')}** \u2014 distance {score:.3f}")
            st.caption(" ".join(doc.page_content.split())[:400])

    chain = RetrievalQAWithSourcesChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever()
    )

    with st.spinner("Generating answer..."):
        try:
            result = chain.invoke({"question": query})
        except Exception as e:
            st.error(f"Model error: {str(e)}")
            st.stop()

    st.header("Answer")
    st.write(result.get("answer", "No answer found"))

    sources = result.get("sources", "")
    if sources:
        st.subheader("Sources:")
        for source in sources.split("\n"):
            st.write(source)
