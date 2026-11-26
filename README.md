# venus-protocol-rs

Rust implementation of the Mesa Venus Vulkan wire protocol (`virgl/venus-protocol`, pinned to commit `4dadbf46`).

Licensed under `MIT OR Apache-2.0`.

## Roadmap

1. **Wire Core (`no_std`)**: Bounds-checked slice `Decoder` / `Encoder`, command header flags, 64-bit object IDs, and length-prefixed arrays/strings/blobs.
2. **XML Codegen**: Generate typed Rust structs, `pNext` chains, and `VenusHandler` dispatch traits from `vk.xml` + `VK_EXT_command_serialization.xml` + `VK_MESA_venus_protocol.xml`.
3. **Differential Tests**: Cross-verify every command and reply byte-for-byte against the upstream C headers, plus real captures (`vkcube`, `llamacpp_gemm`, `dEQP-VK`, `vkQuake`, `PPSSPP`).
4. **WASM Target**: First-class `wasm32-unknown-unknown` support for browser runtimes like `goby`.
