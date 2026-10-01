#ifndef FS1_PC_H
#define FS1_PC_H

#include <stdbool.h>
#include <stdint.h>

#include "cpu8086.h"
#include "disk.h"

/* Minimal IBM PC/XT for a self-booting game: 8088 @ 4.77 MHz, 640K RAM, CGA,
 * i8259 PIC, i8253 PIT, 8255 port 61h/keyboard, and a high-level BIOS. */

#define PC_CPU_HZ 4772727.0
#define PC_PIT_HZ 1193182.0

#define CGA_W 640 /* rendered width; 320-pixel modes are doubled horizontally */
#define CGA_H 200

typedef struct PitChannel {
    uint16_t reload;
    int32_t count;
    uint8_t mode;
    uint8_t access;
    bool write_hi_next;
    bool read_hi_next;
    bool latched;
    uint16_t latch;
    bool loaded;
} PitChannel;

typedef struct SpeakerEvent {
    uint64_t cycle;
    uint8_t port61;
    uint16_t pit2_reload;
} SpeakerEvent;

#define PC_MAX_SPEAKER_EVENTS 8192
#define PC_KBD_QUEUE 64

typedef struct Pc {
    Cpu8086 cpu;
    uint8_t *mem;
    Disk *disk;

    /* i8259 */
    uint8_t pic_irr, pic_imr, pic_isr, pic_vector;
    int pic_icw_step;
    bool pic_need_icw4;
    bool pic_read_isr;

    /* i8253 */
    PitChannel pit[3];
    uint32_t pit_cycle_frac;

    /* 8255 / keyboard */
    uint8_t port61;
    uint8_t kbd_queue[PC_KBD_QUEUE];
    int kbd_head, kbd_tail;
    uint8_t kbd_latch;
    bool kbd_full;
    uint64_t kbd_next_cycle;

    /* CGA */
    uint8_t cga_mode;   /* 3D8 */
    uint8_t cga_color;  /* 3D9 */
    uint8_t crtc_index; /* 3D4 */
    uint8_t crtc[32];
    bool composite; /* display: composite monitor (artifact colour) vs RGB */

    /* speaker log for the current audio slice */
    SpeakerEvent speaker[PC_MAX_SPEAKER_EVENTS];
    int speaker_count;
    uint8_t speaker_port61_at_start;
    uint16_t speaker_reload_at_start;
    uint64_t speaker_slice_start;
    double speaker_sample_frac, speaker_phase, speaker_x1, speaker_y1;

    uint32_t unknown_hle_mask[8];
} Pc;

bool pc_init(Pc *pc, Disk *disk);
void pc_free(Pc *pc);
/* Loads the boot sector to 0000:7C00 and jumps to it, like the BIOS would. */
void pc_boot(Pc *pc);
/* Runs until cpu.cycles reaches target. */
void pc_run(Pc *pc, uint64_t target_cycles);

/* XT set-1 scancode (make code; set bit 7 for break). */
void pc_key_event(Pc *pc, uint8_t scancode);

/* Renders the current CGA screen into CGA_W x CGA_H XRGB8888 pixels. */
void pc_render_cga(const Pc *pc, uint32_t *pixels);

/* Generates mono float samples for cycles [slice_start, cpu.cycles) and starts a new slice.
 * Returns the number of samples written (at most max_samples). */
int pc_speaker_render(Pc *pc, float *out, int max_samples, int sample_rate);

#endif
