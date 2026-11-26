# `venus-protocol-rs` Implementation Plan

## Purpose & Scope

`venus-protocol-rs` (`venus-protocol` crate) is a standalone, `no_std`-friendly, `MIT OR Apache-2.0` Rust implementation of the Mesa Venus Vulkan wire protocol (`virgl/venus-protocol`).

**In scope:**
- `no_std` (+ `alloc`) wire primitives (`Decoder`, `Encoder`, `WireError`, `ObjectId`, `CommandHeader`).
- Generated Vulkan + Mesa Venus types, enums, bitflags, `pNext` chains, and command codecs.
- Both **renderer** side (decode command requests + encode replies) and **driver** side (encode command requests + decode replies).
- A `VenusHandler` dispatch trait (defaulting unhandled commands to `Unsupported`) so consumers like `goby` only implement the commands they support.
- Differential test suite against pinned upstream C `virgl/venus-protocol` headers.

**Out of scope:**
- WebGPU, Vulkan execution runtime / state tracking, `virtio-gpu` / `vtest` / WebSocket transport, shader compilation, or any `goby` dependency.

---

## Phases

### Phase 1 — Pin Upstream & Build the `no_std` Wire Core (`src/wire.rs`)
- Vendor `PIN.json` (`virgl/venus-protocol` commit `4dadbf462d1fe8b192c8648c4f1a370601adf23e`) and the three XMLs (`vk.xml`, `VK_EXT_command_serialization.xml`, `VK_MESA_venus_protocol.xml`) under `upstream/`.
- Implement `Decoder<'a>` over `&'a [u8]` and `Encoder<S: WireSink>` (`SliceSink<'a>` for `no_std`, `Vec<u8>` for `alloc`):
  - Little-endian 4-byte aligned reads/writes (`align4(n) = (n + 3) & !3`) with `Result<T, WireError>`.
  - Scalars (`u8`..`f64`, `bool32`, `size_t` as `u64`), `ObjectId(pub u64)`, `array_size` (`u64`), `simple_pointer` (`0 | 1`), padded blobs, NUL-terminated strings, and `CommandHeader` / reply headers.
- **Gate:** Unit tests for every primitive, padding edge case, and error path under `cargo test`, `cargo check --no-default-features`, `cargo check --no-default-features --features alloc`, and `cargo clippy --all-targets -- -D warnings`.

### Phase 2 — Codegen Pipeline (`codegen/`)
- Reuse `virgl/venus-protocol`'s XML parsing and wire-layout IR (`vkxml.py` + `vn_protocol.py`) to generate `src/generated/`:
  - `enums.rs` — `VkCommandTypeEXT`, `VkStructureType`, `VkResult`, `VkFormat`, bitflags, etc.
  - `types.rs` — Self-contained safe Rust structs, unions, and typed `pNext` enums.
  - `commands.rs` — Request & reply structs + `decode_request` / `encode_reply` (and `encode_request` / `decode_reply`).
  - `dispatch.rs` — `VenusHandler` trait + `dispatch_command`.
- **Gate:** Generated crate compiles cleanly with `cargo check`, `cargo clippy -- -D warnings`, and `wasm32-unknown-unknown`.

### Phase 3 — Differential Test Oracle Against Upstream C (`tests/`)
- Compile the pinned upstream C `driver` and `renderer` headers via `cc` in dev-only integration tests.
- Cross-verify every command and reply byte-for-byte (C driver → Rust renderer, Rust encoder → C decoder), covering `pNext` chains, blobs, partial out-structs, and truncated inputs.
- Replay real Mesa Venus captures (`compute-double-plus-one.venus.bin`, `vkcube`, `llamacpp_gemm`, `dEQP-VK`, `vkQuake`, `PPSSPP`).

### Phase 4 — CI & `goby` Integration
- Add GitHub Actions CI (`cargo test`, `no_std`, `wasm32-unknown-unknown`, `clippy`) and tag `v0.1.0`.
- Port `goby`'s `packages/protocol-venus` handlers to Rust depending on `venus-protocol-rs` and retire the C decoder.
