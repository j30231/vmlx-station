# vMLX Station

`vMLX Station` is a macOS-only local LLM control plane for Apple Silicon.

It is designed to sit on top of [`vMLX`](https://github.com/jjang-ai/vmlx) and make local models feel more like a product:

- menu bar status for the currently loaded model
- local model discovery and inventory
- one-click load and unload
- scheduled model switching by time of day
- OpenAI-compatible inference via the underlying `vmlx serve` runtime
- a small local control API for apps, scripts, and future GUI surfaces

## Why this exists

`vMLX` is a strong inference runtime, but it is still mostly a CLI-first workflow.

`vMLX Station` adds the missing operator layer:

- what models do I have?
- what is loaded right now?
- what should load at 11 PM?
- what endpoint should my local tools call?
- can I test the loaded model without installing another UI?

## Architecture

`vMLX Station` has two parts:

1. `runtime/`
   - a Python daemon that discovers models, manages a `vmlx serve` child process, and applies schedules
2. `Sources/VmlxStationMenuBar/`
   - a native macOS menu bar app built with Swift/AppKit that polls the daemon and lets you load models quickly

The daemon controls `vmlx serve`.
The model API remains the standard OpenAI-compatible `vmlx` endpoint.

## Current MVP

- scan model roots for MLX and JANG-style models
- load/unload a model through `vmlx serve`
- expose local control endpoints on `127.0.0.1:18100`
- expose a built-in admin/test UI on `http://127.0.0.1:18100/admin`
- expose inference through the managed `vmlx` server on `127.0.0.1:18083`
- menu bar item that shows current model and lists installed models
- time-of-day schedules
- editable runtime tuning for major `vmlx serve` knobs
- model cards that show discovered text and vision context windows
- runtime validation that blocks obviously incompatible setting combinations before load

## Supported model types

- standard MLX model folders with `config.json`
- JANG/vMLX model folders with `jang_config.json`

For example:

- `mlx-community/gemma-4-e4b-it-4bit`
- `dealignai/Gemma-4-31B-JANG_4M-CRACK`

## TurboQuant

`vMLX Station` does not implement TurboQuant itself.
It relies on the underlying runtime.

For JANG models, true TurboQuant support depends on the official `jang-tools` package from the [`jjang-ai/jangq`](https://github.com/jjang-ai/jangq) project being installed in the same Python environment as `vmlx`.

## Repo Layout

- `runtime/` Python daemon
- `Sources/VmlxStationMenuBar/` macOS menu bar app
- `config/` sample config
- `launchd/` template plist files
- `docs/` architecture and roadmap
- `scripts/` development helpers

## Quick Start

### 1. Create a Python venv for the daemon

```bash
./scripts/bootstrap_runtime.sh
```

### 2. Install `vmlx`

Point the config at an existing `vmlx` install, or install it in a dedicated venv.

Default expected path:

```text
/Users/<you>/.venvs/vmlx/bin/vmlx
```

### 3. Copy the sample config

```bash
mkdir -p "$HOME/Library/Application Support/vmlx-station"
cp config/example-config.yaml "$HOME/Library/Application Support/vmlx-station/config.yaml"
```

### 4. Start the daemon

```bash
./scripts/dev_daemon.sh
```

### 5. Build the menu bar app

```bash
swift build
.build/debug/VmlxStationMenuBar
```

### 6. Install the daemon as a LaunchAgent

```bash
./scripts/install_daemon.sh
./scripts/check_daemon.sh
```

`install_daemon.sh` will bootstrap `runtime/.venv` automatically if it does not exist.

To remove it later:

```bash
./scripts/uninstall_daemon.sh
```

### 7. Install the menu bar app as a LaunchAgent

```bash
./scripts/install_menu_bar.sh
./scripts/check_menu_bar.sh
```

To remove it later:

```bash
./scripts/uninstall_menu_bar.sh
```

### 8. Install the full station

```bash
./scripts/install_station.sh
./scripts/check_station.sh
```

To remove both services:

```bash
./scripts/uninstall_station.sh
```

## Control API

The daemon exposes a small local API:

- `GET /health`
- `GET /api/status`
- `GET /api/models`
- `GET /api/config`
- `POST /api/load`
- `POST /api/unload`
- `POST /api/reload`
- `POST /api/rescan`
- `POST /api/chat-test`
- `PUT /api/config`
- `GET /api/schedule`
- `PUT /api/schedule`

Example:

```bash
curl -X PUT http://127.0.0.1:18100/api/schedule \
  -H 'Content-Type: application/json' \
  -d '{
    "enabled": true,
    "rules": [
      {"name":"day","start":"06:00","end":"23:00","model_id":"gemma-4-e4b-it-4bit"},
      {"name":"night","start":"23:00","end":"06:00","model_id":"Gemma-4-31B-JANG_4M-CRACK"}
    ]
  }'
```

## OpenAI-compatible inference endpoint

When a model is loaded, `vmlx serve` is managed separately and exposed at:

```text
http://127.0.0.1:18083/v1
```

## Built-in Admin UI

Open this in a browser:

```text
http://127.0.0.1:18100/admin
```

It includes:

- current runtime/model status
- model inventory with load buttons
- unload/rescan/reload actions
- a built-in chat test panel
- editable runtime settings for common `vmlx serve` options
- editable day/night schedule

Note on context length:

- the current `vmlx serve --help` output does not expose a dedicated `--context-length` or `--max-model-len` flag
- `max_tokens` in `vmlx serve` is the default response-generation cap, not the model context window
- the practical knobs available today are `max_tokens`, cache memory, batching, paged cache, KV cache quantization, and disk-streaming settings
- `vMLX Station` now reads each model's `text_config.max_position_embeddings` where available and shows that separately in the UI
- the daemon blocks a few bad combinations up front:
  - `kv_cache_quantization` requires `continuous_batching`
  - `use_paged_cache` requires `continuous_batching`
  - `stream_from_disk` requires `max_num_seqs=1` and cannot be combined with batching/cache features

## Roadmap

See [ROADMAP.md](/Users/jaesik/Documents/New%20project/vmlx-station/docs/ROADMAP.md).

## License

Apache-2.0
