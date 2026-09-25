# 0xp2p Protocol

0xp2p is a decentralized peer-to-peer (P2P) communication service designed for low-latency traffic, data anonymity, and secure memory handling. Built using a hybrid runtime (Python, Rust, and C), the system routes data directly through low-level compiled memory spaces to bypass Python's Global Interpreter Lock (GIL) and enforce zero-copy processing.

---

## Architecture Overview

The system architecture decouples network routing, cryptography, and secure memory allocation into dedicated layers to enforce absolute thread isolation:

```text
├── app.py                  # CLI entryway, asyncio event loop driver
├── service.py              # Python FFI mapping layer (ctypes bindings)
├── build.py                # Single-step compilation and artifact routing script
├── manifest.json           # Runtime parameters and page configuration
├── LICENSE                 # MIT License
│
├── 📁 net-stream/          # P2P engine, async libp2p swarm with QUIC and DCUTR (Rust)
├── 📁 data-parser/         # Symmetric encryption engine and raw FFI entry points (Rust)
├── 📁 sys-alloc/           # Kernel-level page allocation and secure memory wiping (C)
├── 📁 sync-service/        # Non-blocking covert traffic shaper using Asyncio streams (Python)
└── 📁 ui-render/           # Async-compatible interface frame buffer rendering (Python/Tkinter)
```

---

## Low-Level Implementation Details

*   **Page-Aligned Security Locks:** The C allocator invokes platform syscalls (`mlock` on POSIX/Linux, `VirtualLock` on Windows Win32 API) to explicitly lock allocated heaps inside physical RAM, prohibiting the OS from flushing private encryption contexts to virtual swap memory on disk.
*   **Dynamic Access Restriction:** Employs dynamic page protections via the kernel interface (`mprotect` / `VirtualProtect`). Heaps are restricted to `PROT_NONE` (or `PAGE_NOACCESS`) during idle states and opened to read/write states only during packet ingestion to mitigate memory injection vulnerabilities.
*   **Zero-Copy Cryptography:** The Rust parser consumes raw pointers (`*mut u8`) from the allocator using `std::slice::from_raw_parts_mut`. Packet encryption and decryption are processed entirely In-Place, completely bypassing unnecessary allocations on the Rust heap.
*   **Anti-Optimization Memory Wiping:** To prevent modern compilers from optimization-stripping standard `memset` routines (Dead Store Elimination), memory zeroization is driven via `volatile` hardware pointers inside a deterministic loop before pointers are released to the OS.
*   **Traffic Obfuscation (Async Streams):** The Python traffic shaper runs non-blocking async sockets. When the P2P transport queue is idle, the service injects high-entropy random byte blocks (`secrets.token_bytes`) matching the size configured in `manifest.json`. This flattens network throughput into a fixed time-interval footprint to disrupt DPI traffic classification.

---

## Setup & Deployment

### Prerequisites
*   **Rust Toolchain:** Stable release supporting the 2021 edition (`cargo` / `rustc`).
*   **Python Engine:** Python 3.12+ (Asyncio streams core compatibility).
*   **C Compiler Toolchain:** Native installation of `gcc` or `clang`.

### Compilation

Run the single-step automated build script from the root directory to generate libraries and route raw binary artifacts to their exact deployment folders:
```bash
python build.py
```

*Note: The script automatically handles target directory organization and artifact renaming to maintain proper cross-platform linking.*

### Running the Node

Ensure all compiled libraries (`.so` / `.dll`) are successfully dropped inside `sys-alloc/build/`. Start the main execution gateway via the CLI by passing the operational mode:

```bash
# To spin up a transmitter instance
python app.py SENDER

# To spin up a receiver instance
python app.py RECEIVER
```

---

## Production Trade-offs & Limitations

*   **OS Page Sizes:** The platform allocator aligns blocks dynamically to matching kernel page bounds (typically 4096 bytes). Requesting small chunk thresholds down to individual packets causes fragmentation up to the nearest page multiplier.
*   **Unwind Boundary Restrictions:** Rust FFI bindings are fully wrapped with `catch_unwind`. Any internal runtime crashes or parser failures will return structural exit integers to Python rather than throwing native panics, ensuring Python's lifecycle wrapper stays alive to wipe low-level C memory blocks under error states.


> **CRITICAL LEGAL NOTICE & DISCLAIMER:** This software suite is provided "as is" exclusively for academic research, advanced defensive cryptographic engineering, and private network telemetry analysis. The developers, contributors, and copyright holders maintain absolute immunity from legal, civil, or criminal liabilities regarding structural software failures or any malicious deployment of this protocol in breach of domestic or international jurisdictions.
