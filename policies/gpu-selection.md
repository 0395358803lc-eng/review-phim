# GPU / backend and resource selection

Inventory GPU vendor/model, reported VRAM, driver, runtime and each library's installed acceleration support before selecting device.

| Hardware | Candidate backend | Proof requirement |
|---|---|---|
| NVIDIA | CUDA/CTranslate2 CUDA/NVENC | model inference smoke test; actual encoder test; driver/tool compatibility |
| AMD | ROCm (where supported), DirectML or CPU | installed backend and model-specific execution |
| Apple Silicon | Metal/MPS/CoreML where supported | local model executes, memory bounded |
| Other | CPU baseline | measured latency and RAM, report constraints |

Decision: try available specialist small model -> batch adaptive to free memory -> measure throughput, failures and peak VRAM -> compare quality on sample -> upgrade only if gains justify cost. Render encoder support separate from AI inference (NVENC may fail even when CUDA works).

When GPU unavailable: mark CPU fallback, tell user expected tradeoff without invented time estimate. Track model name/weights revision/quantization/backend/resolution, concurrency, elapsed, observed device load and output correctness. OOM -> lower batch or pick smaller model, never silently bypass verification steps.
