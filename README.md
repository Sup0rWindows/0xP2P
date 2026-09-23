# 0xp2p Protocol :)


0xp2p is a zero-footprint, serverless, decentralized peer-to-peer (P2P) communication framework engineered for tactical privacy, absolute anti-forensic durability, and global resistance against Deep Packet Inspection (DPI) , Utilizing a cross-language hybrid architecture, 0xp2p enforces strict hardware-level physical memory locking, dynamic kernel page-permission shifting , and automated symmetric hole punching. This guarantees that ephemeral payloads and session keys never touch persistent storage and are strictly non-recoverable from volatile memory (RAM).

---

## Architectural Topology

The ecosystem is decoupled into 5 dynamically obfuscated directory segments to enforce absolute separation of privileges and mask binary intention from endpoint forensic analysis:

```text
├── app.py         # Main execution gateway and lifecycle wrapper
├── service.py       # Orchestration agent managing low-level dynamic FFI bindings
├── build.py            # Automated cross-platform compiler pipeline script
├── manifest.json           # Ephemeral network parameters and security policy metadata
├── LICENSE                 # Legal MIT software license and liability waiver
│
├── 📁 net-stream/          # [Module 1] Decentralized P2P Subsystem, QUIC Layer & DCUTR Engine (Rust)
├── 📁 data-parser/         # [Module 2] Symmetric Cryptographic Engine & Ephemeral Ratchet (Rust)
├── 📁 sys-alloc/           # [Module 3] Kernel-Level Memory Guardian & Hardware Pinning (C)
├── 📁 sync-service/        # [Module 4] Covert Traffic Shaper & Continuous Decoy Proxy (Python)
└── 📁 ui-render/           # [Module 5] Ephemeral Pixel Buffer & Direct-to-GPU Canvas (Python/Tkinter)
```

---

##  Strategic Security Implementation

*   **Hardware-Level (Write XOR Read) Enforcement:** Implements dynamic page protection shifting via the `sys_restrict_memory_access` runtime layer. The operational memory window defaults strictly to a read-only state (`PAGE_READONLY` / `PROT_READ`). It is flipped momentarily to a write state (`PAGE_READWRITE`) during byte mutations and instantaneously dropped back to read-only execution memory, making side-channel memory-injection or malicious runtime pointer alterations mathematically impossible.
*   **Global NAT Traversal & QUIC Upgrade:** Deploys a hybrid multiplexed transport stack combining standard TCP with low-latency **QUIC (UDP)**. Integrates **Circuit Relay v2** clients to automatically hook into public bootstrap infrastructures, bypassing hostile Symmetric NAT boundaries without end-user manual configuration.
*   **Direct Connection Utility (DCUTR):** Leverages automated peer-coordinated hole punching (`dcutr::Behaviour`). Once an obfuscated connection is established via an autonomous relay proxy, the system instantly upgrades the pipeline into a direct, encrypted endpoint-to-endpoint tunnel, decoupling from the intermediary host to maximize performance and throughput.
*   **Hardware RAM Pinning:** Invokes platform-native low-level syscalls (`mlock` on POSIX/Linux, `VirtualLock` on Windows Win32 API) to lock allocated memory boundaries physically, prohibiting the operating system kernel from swapping tactical payloads into virtual memory swap spaces or paging files on persistent SSDs/HDDs.
*   **Cryptographic Zeroization:** Inherits structural deterministic compiler destruction via Rust's `ZeroizeOnDrop` trait and enforces standard C `volatile` memory pointers to physically overwrite volatile memory blocks with bitwise zeros immediately upon scope exit, overriding aggressive compiler dead-code optimizations.
*   **ISP Traffic Obfuscation (Blinding):** Executes a persistent covert multiplexing pump that injects fixed-size symmetric decoy padding chunks (`b'\x00'`) every 50ms. This flattens network throughput into a static, uninterrupted white-noise wave, rendering timing-based side-channel analysis and DPI traffic pattern classification useless to ISPs.
*   **Defensive MITM Interception Immunity:** Deploys an out-of-band ephemeral handshake utilizing authenticated key exchange algorithms to ensure forward secrecy, neutralizing cryptographic manipulation or certificate-spoofing injection vectors.

---

## Protocol Execution Sequence

1.  **Blind Pairing Discovery:** Nodes establish routing metadata utilizing air-gapped QR-token handshakes or cryptographically sealed asynchronous dead-drops, entirely isolating identity lookups from cleartext public network routing.
2.  **Molecular Payload Fragmentation:** Cleartext message envelopes are immediately fragmented into 512-byte molecular chunks. Each discrete chunk is encrypted via independent symmetric key materials generated sequentially by a fast-rolling double-blind ephemeral ratchet.
3.  **Volatile Interface Rendering:** Payload structures passed to the UI layer avoid native string-allocation pools. Chunks are translated directly into isolated render textures, drawn directly onto the graphical container, and flushed from operational registers instantly upon window focus shifts.

---

## Compilation & Deployment Pipeline

### Prerequisites
*   **Rust Compiler & Cargo Toolchain** 1.70+
*   **Python Runtime Environment** 3.10+
*   **CMake Build Automation Suite** 3.10+ alongside native C Compilers (**GCC**, **Clang**, or **MSVC**)

### Step-by-Step Build Order

#### 1. Execute Automated Build Script
Run the intelligent build pipeline from the root directory to automatically detect your system architecture, compile all native modules, and align binaries:
```bash
python build.py
```

#### 2. Manual Directory Compilation (Alternative)
If manual orchestration is preferred, execute the compilers sequentially:
```bash
# Compile Memory Guardian (C)
cd sys-alloc && mkdir build && cd build && cmake .. && cmake --build . --config Release && cd ../..

# Compile Cryptographic Engine (Rust)
cd data-parser && cargo build --release && cd ..

# Compile P2P Topology Subsystem (Rust)
cd net-stream && cargo build --release && cd ..
```

#### 3. Initialize Ecosystem Workspace
Once compiled shared libraries (`.so` / `.dll`) and binaries are located within their designated build locations, launch the workspace driver:
```bash
python app.py
```

---

## License & Legal Liability Waiver

This software ecosystem is open-sourced under the strict terms of the **MIT License**.

> **CRITICAL LEGAL NOTICE & DISCLAIMER:** This software suite is provided "as is" exclusively for academic research, advanced defensive cryptographic engineering, and private network telemetry analysis. The developers, contributors, and copyright holders maintain absolute immunity from legal, civil, or criminal liabilities regarding structural software failures or any malicious deployment of this protocol in breach of domestic or international jurisdictions.
