# AI Audioguide Generator — Multi-Agent Pipeline

AIdioguide is a multi-agent pipeline designed to generate immersive historical audio guides that sound flawless. It combines contextual research, scriptwriting (tailored for spoken delivery), and precision phonetic processing to ensure that finicky TTS engines (such as Azure) pronounce foreign names, exonyms and historical anomalies correctly.

Tech Stack: Python 3.10+, Anthropic (Claude Sonnet 4.6 / Gemini Flase 3.0), Exa, Azure TTS (Neural Multilingual), SSML.

**[Listen to an example here: Florence Grand Format (8 min)](#)**

---

## Why not summarize Wikipedia?

A good audioguide doesn't recite facts. It starts from something you can see right now, explains why it matters, and uses it as a doorway into a larger story. Standing in front of the Conciergerie, you don't need dates — you need to understand why Philippe IV destroyed the Knights Templar from the very building in front of you.

The problem: ask an LLM directly for precise architectural details and anecdotes and it hallucinates. Confidently. Early tests showed ~80% hallucination rate on specific claims — the gargoyle that "represents medieval medicine", the inscription that "dates from the original construction". The narration sounded great. Google Maps showed a 
1960s apartment building.

Grounding the narration in verifiable facts without losing the narrative thread requires a pipeline that separates concern: 
**research and fact-checking first, storytelling second.**
That's what this system is.

## Quickstart & CLI

The orchestrator is designed to be driven via a Command Line Interface (CLI) for easy batch processing.

```bash
# Clone the repository
git clone [https://github.com/your-username/audioguide-ai.git](https://github.com/your-username/audioguide-ai.git)
cd audioguide-ai

# Install dependencies (Python 3.10+)
pip install -r requirements.txt

# Environment variables setup (.env)
# Required keys: ANTHROPIC_API_KEY, GEMINI_API_KEY, EXA_API_KEY, AZURE_TTS_KEY

# Run a full generation pipeline
python main.py generate --city "Paris" --lang "en" --comment "Very good knowledge of the city. Focus on medieval Paris, ignore anything later than the XVIe century".
```

## Architecture & Workflow

```
mermaid
flowchart LR
    classDef io fill:#f3e8ff,stroke:#9333ea,stroke-width:2px
    classDef agent fill:#d1e7dd,stroke:#0f5132,stroke-width:2px
    classDef tech fill:#e0f2fe,stroke:#0284c7,stroke-width:2px

    Input([Input\nCity + listener profile]):::io

    subgraph CorePipeline [AI orchestrator pipeline]
        S["**Strategist**\nSonnet"]:::agent
        R["**Research + fact-check**\nSonnet · Exa · Gemini Flash"]:::agent
        P["**Planner**\nSonnet"]:::agent
        N["**Narrator**\nSonnet"]:::agent
    end

    subgraph TechnicalGeneration [Post-processing & TTS]
    Ph["**Phoneme detection**\nGemini Flash"]:::tech
    SSML["**SSML injection**\nPython · regex"]:::tech
    A["**Audio generation**\nAzure TTS"]:::tech
    end

    Output([Output\nFinal audioguide]):::io

    Input --> S
    S -->|01_strategy.dsv| R
    R -->|02_verified_research.dsv| P
    P -->|03_plan.json| N
    N -->|04_scripts/*.txt| Ph
    Ph -->|05_phonemes.json| SSML
    SSML -->|06_scripts_with_ssml/*.txt| A
    A -->|07_audio/*.mp3| Output
```

## Technical Decisions

### Reliability over completeness — the fact-checking layer

The core design decision of this pipeline: **it is acceptable to lose facts. It is not acceptable to invent them.**

A tourist standing in front of a monument will never know that the audioguide omitted an anecdote. They will remember if it told them something wrong.

#### The verification workflow

The research pipeline separates claim generation from claim validation across two distinct models.

```mermaid
flowchart LR
    classDef agent fill:#d1e7dd,stroke:#0f5132,stroke-width:2px
    classDef tech fill:#e0f2fe,stroke:#0284c7,stroke-width:2px
    classDef output fill:#f3e8ff,stroke:#9333ea,stroke-width:2px
    classDef rejected fill:#fee2e2,stroke:#dc2626,stroke-width:1px

    S["Sonnet\nClaim generation"]:::agent
    E["Exa\nWeb search"]:::tech
    F["Gemini Flash\nFact-check"]:::agent
    V["Verified claims"]:::output
    R["Rejected"]:::rejected

    S -->|Claims + search queries| E
    E -->|Raw extracts| F
    S -->|Claims| F
    F -->|Confirmed or corrected| V
    F -->|Doubt = discard| R
```

**Sonnet** generates two things simultaneously: the claims themselves, and the Exa search queries designed to verify them. This forces the model to anticipate what evidence would confirm or contradict each claim.

**Exa** runs the queries and returns raw source extracts — up to 5 sources per query, 1000 characters each.

**Gemini Flash** receives both the claims and the raw extracts. Its only job: does the evidence support this claim? If it has any doubt, it discards. It cannot introduce new facts, correct based on its own training knowledge, or hedge. The extracts are the only admissible evidence.

This separation is intentional. Sonnet is better at generating rich, narratively interesting claims. Gemini Flash is faster and cheaper on structured verification tasks. 
Using the same model for both generation and verification would create a closed loop with no external grounding.

The verification workflow can be used at two distincts moments: after the strategy phase and after the planification phase if futher elements are needed.

#### What this costs

On a complex city like Beirut — fragmented sources across French, English and Arabic — the pipeline produces ~130 verified, usable facts. The audioguide uses fewer than half of them.

~40% of claims are rejected outright. An additional ~20% are corrected before passing.

That's the acceptable loss. The 60 facts that make it through are factually auditable end-to-end.

#### What this prevents

Early versions without this layer produced confident, well-narrated 
hallucinations at ~80% rate on specific architectural details and 
anecdotes. The narration sounded great. The facts were invented.

The pipeline trades completeness for auditability. Every claim in the 
final audio can be traced back to a verified source.

#### Three research modes

The pipeline distinguishes three types of research topics, each handled by a dedicated prompt:

- **Lieu** — forensic research on a specific monument or physical location. Looks for architectural anomalies, physical traces, scars. The claim must point to something the listener can see right now.

- **Thème** — broader thematic research on the city. Power structures, epidemics, social dynamics. Looks for traces in the urban fabric rather than a single building.

- **Deep Dive** — targeted research commissioned by the Planner during Phase 2. Macro context, economic mechanisms, political decisions. No physical proof required — these feed the narrative openings.

These are not parametric variants of the same prompt. The output schema, the confidence scoring, and the verification criteria differ fundamentally between modes — a forensic claim requires a physical proof field, a Deep Dive claim does not.

### DSV over JSON — token economics

The research phase is the most expensive part of the pipeline — 20 LLM calls for a city like medieval Paris, each carrying significant context.

JSON structure is expensive. Quotes, brackets, colons, key names repeated on every row — all tokens that carry zero semantic value for the model. Switching to pipe-separated values eliminates that overhead entirely.

To futher reduce the tokens usage, LLM are instructed to use a telegraphic style, suppressing articles, pronouns, conjugated verbs. Symbols replace prose: `->` for consequence, `@` for location, `~` for approximation. Every tokens represents an idea. 

```
P|Bouchers vs Cabochiens 1413|Bouchers Paris -> acteurs majeurs révolte cabochienne [1413]. Simon Caboche = écorcheur Grande Boucherie -> alliance armée avec faction bourguignonne contre Couronne [3].|Aucun vestige physique direct. Trace @ Archives nationales (registres du Parlement de Paris).|H|révolte cabochienne 1413 bouchers Paris Simon Caboche;;cabochiens ordonnance cabochienne 1413 sources primaires

F|Cimetière Innocents Contiguïté|Grande Boucherie -> déchets organiques / sang -> déversement direct vers Saints-Innocents [2]. Contamination hydrique documentée. Stratigraphie archéologique = couches graisseuses identifiées [4].|Fouilles archéologiques @ Square des Innocents. Ossuaire transféré Catacombes [1786].|H|cimetière Saints-Innocents Paris archéologie médiévale contamination;;fouilles INRAP Saints-Innocents stratigraphie
```


Combined, both decisions deliver a ~3x token reduction on research outputs versus natural language JSON.

**In practice — medieval Paris (20 calls)**

| Step | Model | Input | Output |
|------|-------|-------|--------|
| Claim generation ×20 | Sonnet | ~4 000 tokens | ~1 500 tokens |
| Fact-check ×20 | Gemini Flash | ~30–40 000 tokens | ~3 000 tokens |

The fact-check input is large by design — raw Exa extracts are verbose. Thought tokens on Flash were reduced from ~25 000 to ~2 500 by relaxing formatting constraints — the model spends its reasoning budget on verification, not on layout.

### Translating user intent — the Strategist layer

The Strategist converts the user profile into a strict `ANGLE_RECHERCHE` directive that constrains every downstream agent.

For the same Istanbul city, "I know nothing, I'm with my kids" and "Byzantine expert, no Ottoman mosques, only pre-1453" don't just produce different content — they require fundamentally different research pipelines. Locking the angle upstream prevents each agent from reinterpreting the profile independently.

The directive is strict by design. If a research agent finds a compelling fact that falls outside the angle, it is discarded — not because it isn't interesting, but because coherence across 15 stops matters more than any single fact.

### The Planner — geographic logic and the guillotine rule

The Planner is the most editorially powerful agent in the pipeline. 
It receives the Strategist's initial stop list and the full validated 
fact corpus — and rewrites both.

**Geographic reordering.** Stops are reorganized by adjacent zones — 
the itinerary must make sense on foot. A thematically coherent but 
geographically absurd sequence is restructured before narration begins. 
Every stop gets a precise street address to prevent the listener from 
ending up at the wrong building.

**Hard suppression of ungrounded stops.** Any stop with no validated 
facts is deleted without mercy. No facts = no stop, regardless of how 
interesting the location seemed during planning.

**Editorial freedom.** The Planner can add stops the Strategist never 
planned — "breathing stops" in front of disappeared or anonymous 
elements, used to deliver broader historical context between two major 
sites. It can also designate one stop as Grand Format (~8 minutes), 
requiring the listener to sit down and listen.

**Narrative thread declaration.** Before narration begins, the Planner 
explicitly maps recurring figures and themes across the itinerary — 
where each thread is introduced, developed, and closed:
```json
{
  "theme": "Le Pouvoir Contre la Ville : De Marcel à Charles V",
  "introduit_au": 6,
  "developpe_aux": [8, 9],
  "clos_au": 16,
  "resume": "La Grève comme base du contre-pouvoir marchand..."
}
```

Without this, the same historical figure surfaces independently at 
multiple stops with no coherence between them. On an early version of 
the medieval Paris audioguide, Étienne Marcel appeared three times — 
each stop treating him as if the listener had never heard of him.

The Narrator receives these threads as part of its context at every stop. 
It knows that Marcel is introduced at stop 6, developed at 8 and 9, and 
closed at 16 — and writes accordingly. 

### Sequential narration in a parallel pipeline

Every other step in the pipeline runs in parallel. Narration is deliberately sequential.

The reason is empirical. Early tests ran narration in parallel — significantly faster, noticeably worse. Nearly every stop opened with a variation of "Look at this..." The model, lacking context about what had already been said, defaulted to the same rhetorical patterns independently at each stop.

Passing the full conversation history of previous stops to each narration call solves the problem. The model can see what openings, sentence structures and transitions have already been used and avoids repeating them. The result is narration that feels like a single voice across 15 stops, not 15 independent texts that happen to be about the same city.

The tradeoff is speed. Sequential narration is the only non-parallelizable step in the pipeline — and intentionally so.

### Phoneme handling and SSML injection

A travel audioguide is multilingual by nature. A stop about medieval Paris will mention "Philippe Auguste", "Gemmayzeh" in Beirut, or Ottoman street names in Istanbul — each requiring a different pronunciation strategy.

Gemini Flash detects three categories of terms and generates the appropriate handling for each:

- **SSML-supported languages** — a `<lang>` tag switches the TTS engine to the correct phonetic model for that language.
- **Unsupported languages** — IPA phonemes are injected directly, bypassing the TTS engine's language model entirely.
- **Native anomalies** — proper nouns and historical names that a TTS engine reliably mispronounces in their own language(Roman numerals, archaic spellings) also get IPA phonemes.

The injection itself is deterministic Python — regex replacements applied to the narration script before it reaches Azure TTS. A structured text transformation doesn't need a model.

If Azure returns error 1007 (invalid phoneme), the pipeline automatically retries without phonemes, falling back to `<lang>` tags only. The listener gets slightly degraded pronunciation rather than no audio.

## Stack

Python · asyncio · Pydantic · Loguru · Claude Sonnet 4.6 · Gemini Flash 2.0 · Exa · Azure Speech Studio

## Known Limitations

## Exploring the outputs