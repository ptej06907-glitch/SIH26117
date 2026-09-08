# Local inference operation

The workspace assistant routes each submitted request to a local model. It sends only the current typed request, not uploaded files or earlier messages.

## Models
- General writing: Qwen2.5 1.5B Instruct, Q4_K_M.
- Programming: Qwen2.5 Coder 1.5B Instruct, Q4_K_M.
- Official sources: https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF and https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF.
- Runtime: https://github.com/ggml-org/llama.cpp/releases/tag/b10809 (Windows CPU).
- Asset checksums and download URLs: MODEL_ASSETS.json.

## Local execution
The Python service starts the selected runtime on demand with a local model file. It binds to 127.0.0.1, uses a process-specific API key, disables the runtime web UI and MCP proxy, and enables runtime offline mode. Python HTTP calls disable environment-proxy inheritance. There is no cloud fallback.

Both model processes may remain resident after use. One generation runs at a time through the application. On graceful application shutdown, the model processes are terminated. A forced process kill can leave child processes alive; avoid repeatedly force-restarting during generation. Model logs are in data/model-logs. Logs and generated answers should be treated as private.

## Limits
2000 characters per request; 2048-token model context; 384 output tokens. The UI indicates truncation when the generation reaches the output limit. Initial use includes loading time. The models are small prototype choices and can make mistakes. Code is not executed or verified in this milestone.

## Configuration
models/registry.json maps capabilities to model IDs, display names and local GGUF files. Keep files inside models/. Restart the app after changing the registry. Use a compatible runtime/model format; do not configure remote URLs. The first model matching a capability is used.

## Preparation versus runtime
scripts/prepare_models.py downloads assets during preparation and verifies known SHA-256 values. It is never called automatically by the application. scripts/benchmark_models.py generates two public sample responses and records actual results; it does not execute generated code. Full network-monitor proof remains a later milestone.
