# Runtime Requirements (Single-Agent)

This project supports Gemini via the legacy Google Generative AI SDK (`import google.generativeai as genai`).

Required packages (minimal):
- google-generativeai >= 0.8.0

Install:
```bash
pip install "google-generativeai>=0.8.0"
```

Notes:
- The single-agent dynamically selects providers. Gemini requires a valid `GEMINI_API_KEY` (aliases supported: `GOOGLE_GEMINI_API_KEY`, `GOOGLE_GEMINI_KEY`, `GENAI_API_KEY`, `GEMINI_KEY`).
- `.env` is loaded from the workspace root with priority.


