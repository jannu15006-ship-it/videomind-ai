# 🎥 VideoMind-AI
### *Enterprise Multimodal Video & Podcast Intelligence Engine*

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20Storage-orange.svg)](https://www.trychroma.com/)
[![Whisper](https://img.shields.io/badge/OpenAI-Whisper-green.svg)](https://openai.com/research/whisper)
[![CLIP](https://img.shields.io/badge/OpenAI-CLIP-blueviolet.svg)](https://openai.com/research/clip)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An end-to-end multimodal intelligence engine performing **sub-second semantic search across speech and visual keyframes** in video and audio streams, with grounded timestamp citations and interactive playback synchronization.

---

## 🏛️ System Architecture

```
┌────────────────────────────────────────────────────────┐
│                   STREAMLIT WEB UI                     │
│   • Video Player with dynamic click-to-seek playback   │
│   • Visual Citation Cards & Relevance Confidence       │
└───────────────────────────┬────────────────────────────┘
                            │ REST / JSON
┌───────────────────────────▼────────────────────────────┐
│                    FASTAPI BACKEND                     │
│   • Asynchronous Job Queue for Video Processing        │
│   • Pydantic v2 Schemas & Swagger /docs                │
└───────────────────────────┬────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        ▼                                       ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│       AI / ML MODELS        │   │       VECTOR STORAGE        │
│  • Audio: OpenAI Whisper    │   │  • ChromaDB                 │
│  • Vision: CLIP ViT-B/32    │   │    - Dual Collections:      │
│  • LLM: Grounded Synthesis  │   │      1. Audio Transcripts   │
│  • Re-ranker: Cross-Encoder │   │      2. Visual Scenes       │
└─────────────────────────────┘   └─────────────────────────────┘
```

---

## 📂 Project Structure

```
videomind-ai/
├── src/
│   ├── ingestion/       # Video & audio extraction pipelines (yt-dlp, ffmpeg)
│   ├── transcription/   # Whisper speech-to-text with word-level timestamps
│   ├── vision/          # Scene detection and CLIP visual embeddings
│   ├── indexing/        # ChromaDB vector store and schema manager
│   ├── search/          # Hybrid search and Reciprocal Rank Fusion (RRF)
│   ├── synthesis/       # Grounded LLM reasoning and citation generator
│   ├── api/             # FastAPI REST endpoints and Pydantic schemas
│   └── ui/              # Interactive Streamlit dashboard with player sync
├── tests/               # Automated unit and integration test suites
├── configs/             # Application settings & environment loaders
├── data/                # Media cache & persistent vector store (git-ignored)
├── .env.example         # Environment variables template
├── .gitignore           # Git ignore rules for media and caches
└── requirements.txt     # Production dependencies
```

---

## 📅 Engineering Progress Tracker

- [x] **Day 1:** Project scaffolding, clean architecture, configuration manager & test suite.
- [ ] **Day 2:** Video stream ingestion & audio extraction module.
- [ ] **Day 3:** Whisper speech-to-text with word-level timestamps.
- [ ] **Day 4:** Visual scene detection & keyframe extraction.
- [ ] **Day 5:** Visual embeddings with OpenAI CLIP.
- [ ] **Day 6:** Temporal alignment of audio and visual frames.
- [ ] **Day 7:** Sprint 1 milestone review & unit tests.
- [ ] *(Days 8–28: Follows the [Production Engineering Roadmap](C:\Users\JANNU\.gemini\antigravity\brain\dcfecd71-b172-41ba-94ff-9e0b19960599\project_roadmap.md))*
