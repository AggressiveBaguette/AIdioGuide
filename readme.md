Mermaid
``` mermaid
flowchart TD
    %% ── PHASE 0 : EDITORIAL ──
    S0["⚙️ STRATEGIST
    ---
    Model: Sonnet · t° 0.7
    Goal: Define research scope & narrative angle
    In: City / visit theme
    Out: Subject list · languages · angles to avoid"]

    %% ── PHASE 1 : RESEARCH ──
    subgraph RESEARCH["🔎 RESEARCH — parallel per subject"]
        G["🧠 CLAIM GENERATION
        ---
        Model: Sonnet · t° 0.4
        Goal: Generate verifiable atomic claims
        In: Monument / Topic
        Out: claims, YAML"]

        R1["🔎 WEB SEARCH
        ---
        Tool: Exa
        Goal: Find supporting sources
        In: Claims + search queries
        Out: Raw extracts"]

        REJ1["🗑️ REJECTED"]

        FC["✅ FACT-CHECK
        ---
        Model: Gemini Flash, t° 0
        Goal: Defend or reject each claim
        In: Claims + Exa extracts
        Out: Validated claim or rejection"]

        REJ2["🗑️ REJECTED"]

        RESIDU["📦 VALIDATED CLAIMS
        ---
        Claim is verified"]

        G --> R1
        R1 -->|"< 2 hits or < 2 domains"| REJ1
        R1 -->|OK| FC
        FC -->|Claim not confirmed 
        by sources| REJ2
        FC -->|OK| RESIDU
    end

    %% ── PHASE 2 : PLANNING ──
    S1["📋 PLANNER
    ---
    Model: Sonnet · t° 0.5
    Goal: Structure the visit from validated material
    In: Full validated corpus
    Out: Ordered stops · pitch & opening per stop · audio duration"]

    RELOOP{"Missing info
    on specific topic?"}

    RESEARCH2["🔎 ADDITIONAL RESEARCH
Same workflow as previously"]

    %% ── PHASE 3 : NARRATION ──
    subgraph NARRATION["✍️ NARRATION — parallel per stop"]
        N["✍️ NARRATION
        ---
        Model: Sonnet · t° 0.7
        Goal: Turn claims into audio-ready script
        In: Validated claims · stop structure · duration
        Out: Pitch + Opening + Transition · ~300-400 words / 3 min
        No new facts introduced"]
    end

    %% ── PHASE 4 : AUDIO ──
    subgraph AUDIO["🎧 AUDIO"]
        PHON["🔤 PHONEME DETECTION
        ---
        Model: Gemini Flash
        Goal: Prepare foreign words for TTS
        In: Narration script
        Out: Script + phoneme hints per foreign word"]

        TTS["🔊 TTS - parallel per stop
        ---
        Tool: Azure TTS
        Goal: Generate final audio
        In: Script + phoneme hints
        Out: Audio file per stop"]

        PHON --> TTS
    end

    OUT["🎧 FINAL OUTPUT"]

    %% ── FLOW ──
    S0 --> RESEARCH
    RESEARCH --> S1
    S1 --> RELOOP
    RELOOP -->|"Yes"| RESEARCH2
    RESEARCH2 --> NARRATION
    RELOOP -->|No| NARRATION
    NARRATION --> AUDIO
    AUDIO --> OUT

    %% ── STYLES ──
    classDef editorial fill:#dbeafe,stroke:#2563eb,color:#1e3a5f
    classDef generation fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef search fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e
    classDef check fill:#fef9c3,stroke:#ca8a04,color:#713f12
    classDef rejet fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef output fill:#f0fdf4,stroke:#15803d,color:#14532d
    classDef audio fill:#f3e8ff,stroke:#9333ea,color:#3b0764
    classDef decision fill:#f9fafb,stroke:#6b7280,color:#111827

    class S0 editorial
    class G generation
    class R1,RESEARCH2 search
    class FC check
    class REJ1,REJ2 rejet
    class RESIDU,N,S1,OUT output
    class PHON,TTS audio
    class RELOOP decision
```
