# 📄 AI Resume Assistant — Complete User Story Diagram

> **Version:** Sprint 11 — Domain-aware RAG, deterministic scoring, ATS keyword gap analysis
> **Date:** June 2026

---

```mermaid
flowchart TB
    %% =============================================
    %% 1. APP LAUNCH
    %% =============================================
    START(["User runs: streamlit run app.py"]) 
    START --> BROWSER_OPENS["Browser opens http://localhost:8501"]
    BROWSER_OPENS --> PAGE_CONFIG["st.set_page_config: page title AI Resume Assistant, icon document, layout wide"]
    PAGE_CONFIG --> INJECT_CSS["inject_css: apply custom dark blue gradient header, score-card, feedback-card styles, button styles"]
    INJECT_CSS --> RENDER_HEADER
    
    RENDER_HEADER["st.markdown: render gradient header with title and tagline"]
    RENDER_HEADER --> INIT_RAG

    %% =============================================
    %% 2. RAG ENGINE INITIALIZATION (module level, runs once)
    %% =============================================
    subgraph RAG_INIT["Module-Level: init_rag() with @st.cache_resource runs once"]
        INIT_RAG["get_engine() creates singleton RagEngine"]
        INIT_RAG --> LOAD_MODEL["Load BAAI/bge-small-en-v1.5 embedding model (~80MB)"]
        LOAD_MODEL --> CHROMADB_CONNECT["Connect to ChromaDB (local persistent storage)"]
        CHROMADB_CONNECT --> BUILD_INDEX["build_index() - index all 18 knowledge files"]
        BUILD_INDEX --> CHUNK_TEXT["heading-aware chunker: split at ## boundaries"]
        CHUNK_TEXT --> ENCODE_CHUNKS["Encode 289 chunks into 384-dim vectors"]
        ENCODE_CHUNKS --> STORE_VECTORS["Store vectors + text + domain metadata in ChromaDB"]
    end

    INIT_RAG --> RAG_READY

    %% =============================================
    %% 3. INITIAL UI RENDERING
    %% =============================================
    RAG_READY --> INIT_UI_RENDER

    subgraph INIT_UI_RENDER["Rendering the Input Screen"]
        HEADER["Gradient header appears: dark blue, rounded, shadow"]
        HEADER --> MODE_COL["st.columns 1,3: left column = mode selector"]
        
        MODE_COL --> MODE_RADIO["st.radio: Choose mode"]
        MODE_RADIO --> OPTION_RA["Option: Resume Analysis"]
        MODE_RADIO --> OPTION_ATS["Option: ATS Job Match"]
        OPTION_RA --> INPUT_COL
        OPTION_ATS --> INPUT_COL
        
        INPUT_COL["Right column = input area"]
        INPUT_COL --> FILE_UPLOADER["st.file_uploader: Upload Resume PDF"]
        INPUT_COL --> TEXT_AREA["st.text_area: Or paste your resume, height=180"]
        
        INPUT_COL --> CONDITIONAL_JD{"If mode is ATS Job Match"}
        CONDITIONAL_JD -->|"Yes"| JD_TEXTAREA["Additional st.text_area: Job description, height=150"]
        CONDITIONAL_JD -->|"No"| NO_JD["No job description field"]
        
        FILE_UPLOADER --> RUN_BTN["st.button: rocket Analyze Resume, use_container_width=True"]
        TEXT_AREA --> RUN_BTN
        JD_TEXTAREA --> RUN_BTN
        NO_JD --> RUN_BTN
    end

    INIT_UI_RENDER --> USER_WAITS["User sees full input form"]

    %% =============================================
    %% 4. USER INPUT GATHERING
    %% =============================================
    USER_WAITS --> USER_ACTION{"User action"}

    USER_ACTION -->|"Changes mode radio"| MODE_CHANGE{"Which mode selected?"}
    MODE_CHANGE -->|"Resume Analysis"| HIDE_JD["Job description text area disappears"]
    MODE_CHANGE -->|"ATS Job Match"| SHOW_JD["Job description text area appears"]
    HIDE_JD --> USER_WAITS
    SHOW_JD --> USER_WAITS

    USER_ACTION -->|"Uploads a PDF"| PDF_UPLOADED["File selected in file_uploader"]
    USER_ACTION -->|"Types/pastes in text area"| TEXT_TYPED["Text entered in paste area"]
    USER_ACTION -->|"Clicks Analyze Resume"| CLICK_RUN

    %% =============================================
    %% 5. RESUME INPUT PRIORITY
    %% =============================================
    subgraph RESUME_SOURCE["Resume Source Decision - runs before API call"]
        CHECK_UPLOAD{"uploaded_file is not None?"}
        CHECK_UPLOAD -->|"Yes, PDF uploaded"| EXTRACT_PDF["with st.spinner: Extracting text from PDF"]
        EXTRACT_PDF --> EXTRACT_FUNC["extract_text: PdfReader reads PDF"]
        EXTRACT_FUNC --> ITER_PAGES["Iterate through all pages"]
        ITER_PAGES --> EXTRACT_EACH["page.extract_text or empty string"]
        EXTRACT_EACH --> JOIN_PAGES["join with newline"]
        JOIN_PAGES --> RESUME_VAR["resume = extracted PDF text"]
        
        CHECK_UPLOAD -->|"No PDF, check text area"| CHECK_TEXT{"text_resume.strip is truthy?"}
        CHECK_TEXT -->|"Yes"| RESUME_FROM_TEXT["resume = text_resume pasted content"]
        CHECK_TEXT -->|"No"| RESUME_EMPTY["resume = empty string"]
        RESUME_FROM_TEXT --> RESUME_VAR
        RESUME_EMPTY --> RESUME_VAR
    end

    %% =============================================
    %% 6. VALIDATION ON CLICK
    %% =============================================
    CLICK_RUN --> COLLECT_INPUT

    subgraph COLLECT_INPUT["Collecting and validating input"]
        RESUME_SOURCE
        
        VALIDATE_RESUME{"resume.strip is falsy?"}
        RESUME_VAR --> VALIDATE_RESUME
        VALIDATE_RESUME -->|"Empty"| WARN_RESUME["st.warning: Please provide a resume"]
        WARN_RESUME --> STOP_EXEC["st.stop - halts all further execution"]
        
        VALIDATE_RESUME -->|"Has content"| CHECK_MODE_ATS{"mode == ATS Job Match?"}
        CHECK_MODE_ATS -->|"Yes"| VALIDATE_JD{"job_description.strip is falsy?"}
        CHECK_MODE_ATS -->|"No"| PROCEED["Proceed to analysis"]
        
        VALIDATE_JD -->|"Empty"| WARN_JD["st.warning: Please provide job description"]
        WARN_JD --> STOP_EXEC
        
        VALIDATE_JD -->|"Has content"| PROCEED
    end

    PROCEED --> PROMPT_BUILDING

    %% =============================================
    %% 7. PROMPT CONSTRUCTION
    %% =============================================
    subgraph PROMPT_BUILDING["Prompt Construction - build_prompt"]
        SCHEMA_DEF["Define JSON schema"]
        RULES_DEF["Define rules block"]
        
        SCHEMA_DEF --> BASE_JSON["json.dumps schema with indent 2"]
        RULES_DEF --> BRANCH_PROMPT{"Which mode?"}
        
        BRANCH_PROMPT -->|"Resume Analysis"| BUILD_RA["Build: rules + schema + knowledge + resume"]
        
        BRANCH_PROMPT -->|"ATS Job Match"| BUILD_ATS["Build: rules + schema + resume + job description"]
        
        BUILD_RA --> RETRIEVE_KB["rag_engine.retrieve(resume, top_k=3)"]
        RETRIEVE_KB --> CLASSIFY_DOMAIN["classify_domain: embedding similarity vs 16 domain descriptions"]
        CLASSIFY_DOMAIN --> MARGIN_CHECK{"margin < 0.03?"}
        MARGIN_CHECK -->|"Yes"| SEARCH_TWO["Search top 2 domains in ChromaDB"]
        MARGIN_CHECK -->|"No"| SEARCH_ONE["Search single domain in ChromaDB"]
        SEARCH_TWO & SEARCH_ONE --> TOP_CHUNKS["Retrieve top 3 relevant chunks"]
        TOP_CHUNKS --> INJECT_KB["Inject domain-specific knowledge into prompt"]
        
        INJECT_KB --> BUILD_RA["Build: rules + schema + knowledge + resume"]
        BUILD_ATS --> INJECT_KB

        BUILD_RA --> PROMPT_READY["Final prompt string ready"]
        BUILD_ATS --> PROMPT_READY
    end

    PROMPT_READY --> LOGGING

    %% =============================================
    %% 8. LOGGING + API CALL
    %% =============================================
    subgraph LOGGING["Logging to console + resume_app.log"]
        LOG_SECTION_START["log_section: RESUME ANALYSIS STARTED"]
        LOG_MODE["log: Mode = Resume Analysis or ATS Job Match"]
        LOG_LEN["log: Resume Length = N characters"]
        LOG_JD_LEN["log: Job Description Length = N characters if ATS mode"]
        LOG_PROMPT_START["log_section: PROMPT START"]
        LOG_PROMPT_CONTENT["print + logging.info the full prompt text"]
        LOG_PROMPT_END["log_section: PROMPT END"]
    end

    LOGGING --> SPINNER_API

    SPINNER_API["with st.spinner: robot AI is analyzing your resume..."]
    SPINNER_API --> API_CALL

    API_CALL["client.chat.completions.create: model=openrouter/free"]
    API_CALL -->|"Response received"| LOG_RESPONSE

    subgraph LOG_RESPONSE["Logging the API response"]
        LOG_API_RECEIVED["log: API response received"]
        TRY_DUMP{"Try response.model_dump_json"}
        TRY_DUMP -->|"Success"| LOG_FULL_OBJ["log_section: FULL API RESPONSE OBJECT + print JSON"]
        TRY_DUMP -->|"Exception"| LOG_DUMP_FAIL["log: Could not dump full response"]
    end

    LOG_RESPONSE --> EXTRACT_OUTPUT

    %% =============================================
    %% 9. EXTRACT + CLEAN + PARSE
    %% =============================================
    EXTRACT_OUTPUT["raw_output = response.choices.0.message.content"]
    EXTRACT_OUTPUT --> LOG_RAW_START["log_section: RAW OUTPUT START"]
    LOG_RAW_START --> PRINT_RAW["print raw_output"]
    PRINT_RAW --> LOG_RAW_END["log_section: RAW OUTPUT END"]
    LOG_RAW_END --> NULL_CHECK

    NULL_CHECK{"raw_output is None?"}
    NULL_CHECK -->|"Yes, model returned image"| NULL_ERROR_BRANCH
    NULL_CHECK -->|"No, has content"| CLEAN_OUTPUT

    subgraph NULL_ERROR_BRANCH["Null Response Error Handler"]
        LOG_NULL["log_section: NULL RESPONSE ERROR"]
        LOG_NULL_MSG["logging.error: Model returned null content"]
        ST_NULL_ERROR["st.error: The model returned an image instead of text"]
        ST_NULL_STOP["st.stop - halt execution"]
    end

    subgraph CLEAN_OUTPUT["Cleaning + Parsing"]
        CLEAN_STEP["cleaned = re.sub backtick json or backtick with empty string, then strip"]
        CLEAN_STEP --> LOG_CLEAN_START["log_section: CLEANED OUTPUT START"]
        LOG_CLEAN_START --> PRINT_CLEAN["print cleaned"]
        PRINT_CLEAN --> LOG_CLEAN_END["log_section: CLEANED OUTPUT END"]
        LOG_CLEAN_END --> TRY_PARSE["try: safe_parse_json cleaned"]
    end

    TRY_PARSE --> PARSE_RESULT{"valid parsed result?"}

    PARSE_RESULT -->|"No / None"| PARSE_ERROR_BRANCH
    PARSE_RESULT -->|"Yes, valid dict"| NORMALIZE_STEP

    subgraph PARSE_ERROR_BRANCH["JSON Parse Error Handler"]
        LOG_JSON_FAIL["log_section: JSON PARSE ERROR"]
        LOG_JSON_PRINT["print + logging.error the raw cleaned text"]
        ST_JSON_ERROR["st.error: Model returned invalid JSON"]
        ST_JSON_RAW["st.text: show cleaned raw output for debugging"]
        ST_JSON_STOP["st.stop"]
    end

    %% =============================================
    %% 10. NORMALIZE SCORE + DETERMINISTIC RUBRIC
    %% =============================================
    subgraph NORMALIZE_STEP["Score Processing"]
        GET_BREAKDOWN["b = result.get breakdown, empty dict"]
        EXTRACT_VALUES["Extract int values from breakdown dict"]
        CALC_AVG["breakdown_avg = sum / count * 10"]
        GET_MODEL_SCORE["model_score = result.get score, 0"]
        AVERAGE["result.score = int model_score + breakdown_avg / 2"]
        GET_BREAKDOWN --> EXTRACT_VALUES --> CALC_AVG --> GET_MODEL_SCORE --> AVERAGE

        AVERAGE --> RUBRIC["score_resume(resume) — deterministic weighted rubric"]
        RUBRIC --> RUBRIC_SCORE["rubric_score = 0-100 based on 5 categories"]
        RUBRIC_SCORE --> BLEND["Final score = rubric_score x 70% + llm_score x 30%"]
    end

    NORMALIZE_STEP --> SUCCESS_MSG["st.success: checkmark Resume analysis complete"]

    %% =============================================
    %% 11. RENDER RESULTS
    %% =============================================
    SUCCESS_MSG --> RENDER_RESULTS

    subgraph RENDER_RESULTS["Rendering the Results Dashboard"]
        direction TB
        
        subgraph METRIC_CARDS["4 Metric Cards - st.columns 4"]
            COL1["Column 1: Overall Score"]
            COL1 --> CARD1["score_color determines border + text color"]
            CARD1 --> C1_RENDER["st.markdown with score-card CSS class, shows /100"]
            
            COL2["Column 2: ATS Match"]
            COL2 --> ATS_VAL["ats_match times 10 = 0-100"]
            ATS_VAL --> C2_RENDER["st.markdown score-card"]
            
            COL3["Column 3: Clarity"]
            COL3 --> CLARITY_VAL["clarity times 10 = 0-100"]
            CLARITY_VAL --> C3_RENDER["st.markdown score-card"]
            
            COL4["Column 4: Skills"]
            COL4 --> SKILLS_VAL["skills times 10 = 0-100"]
            SKILLS_VAL --> C4_RENDER["st.markdown score-card"]
        end

        MET

    %% =============================================
    %% 12. PDF DOWNLOAD
    %% =============================================
    subgraph PDF_SECTION["PDF Report Generation + Download"]
        PDF_DIVIDER["st.divider"]
        PDF_DIVIDER --> PDF_BTN
        
        PDF_BTN["st.download_button: inbox Download PDF Report"]
        PDF_BTN --> PDF_CLICK{"User clicks download button"}
        
        PDF_CLICK -->|"Yes"| PDF_GENERATE
        
        subgraph PDF_GENERATE["generate_pdf_report function"]
            PDF_MEM["BytesIO buffer"]
            PDF_MEM --> PDF_DOC["SimpleDocTemplate with A4 page size"]
            PDF_DOC --> PDF_TITLE["Paragraph: Resume Analysis Report or ATS Match Report"]
            PDF_TITLE --> PDF_SCORE["Paragraph: bold Score: score/100"]
            PDF_SCORE --> PDF_SUMMARY["Paragraph: result.summary"]
            PDF_SUMMARY --> PDF_ADD_LISTS
            
            subgraph PDF_ADD_LISTS["Add list sections"]
                LIST_STRENGTHS["add_list: Strengths"]
                LIST_STRENGTHS --> CHECK_MODE_PDF{"Mode?"}
                CHECK_MODE_PDF -->|"Resume Analysis"| LIST_WEAK["add_list: Weaknesses"]
                LIST_WEAK --> LIST_IMPROVE["add_list: Improvements"]
                CHECK_MODE_PDF -->|"ATS Job Match"| LIST_MISSING["add_list: Missing Skills"]
                LIST_MISSING --> LIST_RECOMMEND["add_list: Recommendations"]
                LIST_IMPROVE --> PDF_BUILD
                LIST_RECOMMEND --> PDF_BUILD
            end
            
            PDF_BUILD["doc.build elements"]
            PDF_BUILD --> PDF_SEEK["buffer.seek 0"]
            PDF_SEEK --> PDF_RETURN["return buffer bytes"]
        end
        
        PDF_GENERATE --> PDF_DOWNLOAD["Browser triggers file download: filename = resume_mode_report.pdf, mime = application/pdf"]
        
        PDF_CLICK -->|"No"| PDF_SKIP["Button visible, no action"]
    end

    PDF_SECTION --> PIPELINE_LOG

    %% =============================================
    %% 13. PIPELINE COMPLETE
    %% =============================================
    PIPELINE_LOG["log_section: PIPELINE COMPLETE"]
    PIPELINE_LOG --> LOG_DONE["log: All processing finished successfully"]
    LOG_DONE --> END(["End - User sees full results on screen"])

    %% =============================================
    %% 14. EXCEPTION HANDLER (outer try/except)
    %% =============================================
    TRY_PARSE -.->|"Exception thrown"| UNEXPECTED_ERROR
    
    subgraph UNEXPECTED_ERROR["Outer Exception Handler - catches all"]
        LOG_EXCEPTION["log_section: JSON PARSE ERROR"]
        LOG_EXCEPTION_DETAIL["print + logging.error the exception string + cleaned text"]
        ST_ERROR_MSG["st.error: Model returned invalid JSON"]
        ST_ERROR_RAW["st.text: show cleaned"]
        ST_ERROR_STOP["st.stop"]
    end

    %% =============================================
    %% 15. ATS MODE PDF VARIANT
    %% =============================================
    PDF_ADD_LISTS -.->|"If ATS mode"| ATS_PDF_NOTE
    
    subgraph ATS_PDF_NOTE["ATS Match PDF variant"]
        PDF_TITLE_ATS["Instead: add_list Missing Skills + Recommendations"]
        PDF_TITLE_ATS --> PDF_FEEDBACK_NOTE["No Weaknesses or Improvements in PDF"]
    end

    %% =============================================
    %% STYLES
    %% =============================================
    style RAG_INIT fill:#f0fdf4,stroke:#22c55e,color:#166534
    
    style START fill:#1e3a5f,color:#fff,stroke:#1e3a5f
    style END fill:#1e3a5f,color:#fff,stroke:#1e3a5f
    style HEADER fill:#2d6a9f,color:#fff,stroke:#2d6a9f
    style RENDER_HEADER fill:#2d6a9f,color:#fff
    
    style WARN_RESUME fill:#fef3c7,stroke:#d97706,color:#92400e
    style WARN_JD fill:#fef3c7,stroke:#d97706,color:#92400e
    style STOP_EXEC fill:#fef2f2,stroke:#ef4444,color:#991b1b
    
    style NULL_ERROR_BRANCH fill:#fef2f2,stroke:#ef4444,color:#991b1b
    style PARSE_ERROR_BRANCH fill:#fef2f2,stroke:#ef4444,color:#991b1b
    style UNEXPECTED_ERROR fill:#fef2f2,stroke:#ef4444,color:#991b1b
    
    style KNOWLEDGE_INIT fill:#f0fdf4,stroke:#22c55e,color:#166534
    
    style METRIC_CARDS fill:#f8fafc,stroke:#64748b
    style CHARTS fill:#f8fafc,stroke:#64748b
    style EXPANDER_SECTION fill:#f8fafc,stroke:#64748b
    style SUMMARY_SECTION fill:#f8fafc,stroke:#64748b
    style FEEDBACK_SECTION fill:#f8fafc,stroke:#64748b
    style PDF_SECTION fill:#f8fafc,stroke:#64748b
    
    style LOGGING fill:#e0e7ff,stroke:#6366f1,color:#3730a3
    style LOG_RESPONSE fill:#e0e7ff,stroke:#6366f1,color:#3730a3

    linkStyle default stroke:#94a3b8
```

---

## Summary of All User Paths

### ✅ Path: Success — Resume Analysis, PDF upload
1. Launch app, see gradient header + input form
2. Select "Resume Analysis"
3. Click file uploader, select a PDF from file system
4. See "No file chosen" change to filename
5. Click **🚀 Analyze Resume**
6. See spinner "Extracting text from PDF..." briefly
7. See spinner "🤖 AI is analyzing your resume..." during API call
8. See success message, 4 metric cards, gauge, radar, expander, summary, 3 feedback cards, download button
9. Click **📥 Download PDF Report**, browser saves file

### ✅ Path: Success — Resume Analysis, text paste
1. Launch app, select "Resume Analysis"
2. Paste or type resume text in the text area (no file uploaded)
3. Click **🚀 Analyze Resume**
4. Same results as above, but no PDF extraction step

### ✅ Path: Success — ATS Job Match
1. Launch app, select "ATS Job Match"
2. Upload/paste resume AND type/paste job description in the new text area
3. Click **🚀 Analyze Resume**, API sees both resume + job description in prompt
4. Same result layout
5. PDF report uses Missing Skills + Recommendations instead of Weaknesses + Improvements

### ❌ Path: Validation error — No resume
1. Click **🚀 Analyze Resume** without any resume
2. See `st.warning("Please provide a resume")`
3. Execution stops, nothing happens

### ❌ Path: Validation error — ATS mode, no job description
1. Select ATS mode
2. Provide resume but leave job description empty
3. Click **🚀 Analyze Resume**
4. See `st.warning("Please provide job description")`
5. Execution stops

### ❌ Path: Error — Model returns null (image response)
1. API responds but `message.content` is `None`
2. See `st.error("The model returned an image instead of text...")`
3. Execution stops

### ❌ Path: Error — Invalid JSON from model
1. API responds with text that isn't valid JSON
2. See `st.error("Model returned invalid JSON")` + raw text dump
3. Execution stops

### ⚙️ Background: Module-level initialization (runs once)
- `load_dotenv()` — loads `.env` for `OPENROUTER_API_KEY`
- `init_rag()` — creates singleton `RagEngine` with `@st.cache_resource`:
  - Loads embedding model `BAAI/bge-small-en-v1.5`
  - Connects to ChromaDB, builds heading-aware index (289 chunks)
  - Computes domain embeddings for 16 career domains
- `client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=...)` — creates API client
- `inject_css()` — registers all custom CSS styles for the Streamlit page
- `scoring.py` loaded — deterministic rubric scoring + ATS gap analysis

---

## File: `USER_STORY.md`
This file provides a complete reference for understanding every user interaction, UI component, and system process in the app without having to read the source code.