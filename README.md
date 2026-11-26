# Ilm Academy — AI Tutor & Adaptive Learning Platform (Day 1)

Day 1 builds the foundational content pipeline, knowledge map (concept graph), tagged question bank, learner simulation data, and Analytics EDA for **Ilm Academy** (8,000 online students experiencing a ~45% pre-Week-4 dropout rate on a one-size-fits-all path).

## Deliverables & Structure

- **Content Ingestion Pipeline** ([`src/ingestion/pipeline.py`](src/ingestion/pipeline.py))
  - Transcribes lesson videos (`.mp4`) with OpenAI Whisper (`tiny`) including segment timestamps (`start_sec`, `end_sec`).
  - Extracts text from PowerPoint slides (`.pptx` via `python-pptx`) and PDF lecture notes (`.pdf` via `pymupdf`).
  - Indexes all 87 chunks into a persistent **ChromaDB** vector store (`data/chroma_db/`) using `all-MiniLM-L6-v2` embeddings.
- **Python Concept Graph (DAG)** ([`src/graph/concept_graph.py`](src/graph/concept_graph.py))
  - 45 Python concepts across Weeks 1–6 with 74 prerequisite edges.
  - Verified cycle-free (`nx.is_directed_acyclic_graph(G) == True`).
  - Maps every lesson (`L01`–`L08`) and all 225 questions to concepts.
  - Exports [`data/concept_graph.json`](data/concept_graph.json) and [`outputs/concept_graph.png`](outputs/concept_graph.png).
- **Question Bank** ([`src/questions/generate_bank.py`](src/questions/generate_bank.py))
  - 225 questions (`90` MCQ, `90` short answer, `45` coding) in [`data/question_bank.json`](data/question_bank.json).
  - Each tagged with `concept_id`, `lesson_id`, `week`, `type`, `difficulty` / `irt_b`, and `bloom_level`.
- **Learner Data & 1,000-Student Simulator** ([`src/simulation/learner_sim.py`](src/simulation/learner_sim.py))
  - Unified loader for **ASSISTments / EdNet** interaction logs.
  - 1,000-student IRT-inspired simulator modeling `ability`, `speed`, `slip`, `guess`, prerequisite gaps, learning gain, and calibrated pre-Week-4 dropout.
  - Outputs [`data/student_profiles.csv`](data/student_profiles.csv) and [`data/learner_interactions.csv`](data/learner_interactions.csv).
- **Analytics EDA Notebook** ([`notebooks/eda_analytics.ipynb`](notebooks/eda_analytics.ipynb))
  - Analyzes accuracy per concept, learning curves, dropout points, and hardest concepts—each with a visual plot and a one-line insight.

## Quickstart

```bash
pip install -r requirements.txt
python scripts/generate_sample_content.py
python -m src.ingestion.pipeline
python -m src.questions.generate_bank
python -m src.graph.concept_graph
python -m src.simulation.learner_sim
jupyter nbconvert --to notebook --execute --inplace notebooks/eda_analytics.ipynb
```
