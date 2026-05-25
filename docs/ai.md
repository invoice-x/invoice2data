# AI features

invoice2data ships an **opt-in** AI layer. It is *deterministic-first*: nothing
AI-related runs unless you configure a provider, and templates always take
precedence — the LLM is only a fallback. The default provider is `mock` (no
network), so the test suite and a fresh install never call out anywhere.

Install the extra:

```bash
pip install "invoice2data[ai]"
```

## Configure a provider

All settings come from `INVOICE2DATA_AI_*` environment variables, so credentials
are never hard-coded:

| variable | meaning | default |
|----------|---------|---------|
| `INVOICE2DATA_AI_PROVIDER` | `mock`, or a vendor: `openai`, `deepseek`, `mistral`, `gemini`, `ollama` | `mock` |
| `INVOICE2DATA_AI_MODEL` | model id passed to the provider | (empty) |
| `INVOICE2DATA_AI_API_KEY` | API key (not needed for local Ollama) | — |
| `INVOICE2DATA_AI_BASE_URL` | override the API base URL | vendor default |

The vendor providers all speak the OpenAI chat-completions API, so picking a
provider just sets the right base URL for you. Recommended picks:

- **Gemini** — cheap and capable for invoices.
- **Mistral** — EU-hosted, good for privacy-sensitive data.
- **DeepSeek** — low cost.
- **Ollama** — fully local/offline; no key, no data leaves your machine.

```bash
export INVOICE2DATA_AI_PROVIDER=gemini
export INVOICE2DATA_AI_MODEL=gemini-2.0-flash
export INVOICE2DATA_AI_API_KEY=...
```

Only the document **text** is sent to the provider (never page images), keeping
requests small and cheap.

## 1. LLM fallback extraction

When no template matches — or a matched template misses required fields — let the
provider extract the canonical fields as a last resort:

```bash
invoice2data --ai-fallback invoice.pdf
```

Templates are still tried first; the LLM only runs when they come up short. The
result follows the same {doc}`canonical schema <recommended-template-fields>`.

## 2. AI-assisted template generation

Draft a reusable template from a sample document, then refine it by hand:

```bash
invoice2data --new-template sample.pdf --ai --template-out acme.yml
```

Without `--ai`, `--new-template` still drafts a template using built-in
heuristics (candidate fields, date ordering); `--ai` asks the configured provider
to propose the regexes instead. Either way you get a YAML/JSON template you own
and can edit — not a black box.

## Library use

```python
from invoice2data.ai.fallback import ai_fallback_extract

fields = ai_fallback_extract(text)  # uses the configured provider
```

See the {doc}`reference` (AI section) for `AIConfig`, `load_config()`, the
`AIProvider` protocol and `get_provider()`.
```{note}
The AI layer is provider-pluggable by design: implement the `AIProvider`
protocol and register it to add your own backend.
```
