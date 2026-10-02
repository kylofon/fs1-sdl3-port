#ifndef FS1_NATIVE_H
#define FS1_NATIVE_H

#include <stdbool.h>
#include <stdint.h>

#include "pc.h"

/* Native replacements of original routines (phase 3).
 *
 * Each entry binds a C function to a code address (normally 0050:xxxx). When the CPU is
 * about to execute an instruction at an enabled entry's address, the C function runs
 * instead. It sees the full CPU state and must leave it exactly as the original routine
 * would on return, including popping the return address (native_ret / native_retf).
 * A native call costs the entry's `cycles` (NATIVE_CALL_CYCLES if 0) emulated cycles.
 * Charging what the original takes keeps the emulated timeline, and so the screen,
 * identical; --verify reports the original's measured cycle range for that purpose.
 */

#define GAME_CS 0x0050
#define GAME_DS 0x0618
#define NATIVE_CALL_CYCLES 100

typedef void (*NativeFn)(Pc *pc);

/* Linear address range [lo, hi) excluded from the --verify memory comparison. */
typedef struct NativeRange {
    uint32_t lo, hi;
} NativeRange;

typedef struct NativeEntry {
    const char *name;
    uint16_t seg, off;
    NativeFn fn;
    bool enabled;
    bool far;                  /* returns with RETF instead of RET */
    uint16_t flag_mask;        /* flags the native guarantees to match (F_*); default none */
    const NativeRange *ignore; /* optional write-only scratch areas, ignore_count entries */
    int ignore_count;
    uint32_t cycles; /* emulated cycles charged per native call; 0 = NATIVE_CALL_CYCLES */

    /* run-time state and statistics */
    bool verify;
    uint64_t calls, mismatches, cap_hits;
    uint64_t orig_cycles_min, orig_cycles_max; /* measured by --verify */
} NativeEntry;

/* Installs the dispatch hook on pc->cpu. Call after pc_init. */
void native_init(Pc *pc);
/* NAME or "all". Return false if no entry has that name. */
bool native_set_enabled(const char *name, bool enabled);
bool native_set_verify(const char *name);
void native_list(void);
/* Prints calls and mismatches of every entry being verified. */
void native_verify_summary(void);
void native_shutdown(void);

/* ---- helpers for native routines -------------------------------------------- */

static inline uint16_t mem_read16(Pc *pc, uint16_t seg, uint16_t off)
{
    return cpu_read16(&pc->cpu, cpu_linear(seg, off));
}
static inline void mem_write16(Pc *pc, uint16_t seg, uint16_t off, uint16_t v)
{
    cpu_write16(&pc->cpu, cpu_linear(seg, off), v);
}
static inline uint8_t ds_read8(Pc *pc, uint16_t off) { return cpu_read8(&pc->cpu, cpu_linear(GAME_DS, off)); }
static inline uint16_t ds_read16(Pc *pc, uint16_t off) { return mem_read16(pc, GAME_DS, off); }
static inline void ds_write8(Pc *pc, uint16_t off, uint8_t v) { cpu_write8(&pc->cpu, cpu_linear(GAME_DS, off), v); }
static inline void ds_write16(Pc *pc, uint16_t off, uint16_t v) { mem_write16(pc, GAME_DS, off, v); }

/* Near RET: pops IP. */
static inline void native_ret(Pc *pc) { pc->cpu.ip = cpu_pop(&pc->cpu); }
/* Far RET: pops IP and CS. */
static inline void native_retf(Pc *pc)
{
    pc->cpu.ip = cpu_pop(&pc->cpu);
    pc->cpu.sregs[S_CS] = cpu_pop(&pc->cpu);
}

#endif
