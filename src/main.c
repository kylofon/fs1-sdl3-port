/*
 * Microsoft Flight Simulator 1.0x (IBM PC, 1982) - SDL3 port.
 *
 * Phase 1: the original program runs on an embedded minimal PC (pc.c) and is
 * displayed, heard and controlled through SDL3. See docs/PORT_PLAN.md.
 *
 * Keys: F10 toggles composite/RGB monitor, F11 cycles emulation speed,
 *       F12 dumps memory to extracted/mem_dump.bin.
 * Dev options:
 *   --frames N          quit after N frames (each frame is exactly 1/60 s of emulated time)
 *   --screenshot FILE   save the last frame as BMP on quit
 *   --type TEXT         type TEXT, one key per second, starting after 2 seconds
 */
#define SDL_MAIN_USE_CALLBACKS 1
#include <SDL3/SDL.h>
#include <SDL3/SDL_main.h>

#include "disk.h"
#include "pc.h"

#define WINDOW_W 960
#define WINDOW_H 720
#define AUDIO_RATE 44100
#define DEFAULT_DISK "original/Microsoft Flight Simulator v1.05 (198x)(Microsoft Corporation).ima"

typedef struct App {
    SDL_Window *window;
    SDL_Renderer *renderer;
    SDL_Texture *screen;
    SDL_AudioStream *audio;
    uint32_t pixels[CGA_W * CGA_H];
    float samples[AUDIO_RATE / 5];
    Disk disk;
    Pc *pc;

    uint64_t last_ticks;
    int speed;

    long frame;
    long max_frames;
    const char *screenshot;
    const char *type_text;
} App;

static uint8_t xt_scancode(SDL_Scancode sc)
{
    switch (sc) {
    case SDL_SCANCODE_ESCAPE: return 0x01;
    case SDL_SCANCODE_1: return 0x02;
    case SDL_SCANCODE_2: return 0x03;
    case SDL_SCANCODE_3: return 0x04;
    case SDL_SCANCODE_4: return 0x05;
    case SDL_SCANCODE_5: return 0x06;
    case SDL_SCANCODE_6: return 0x07;
    case SDL_SCANCODE_7: return 0x08;
    case SDL_SCANCODE_8: return 0x09;
    case SDL_SCANCODE_9: return 0x0A;
    case SDL_SCANCODE_0: return 0x0B;
    case SDL_SCANCODE_MINUS: return 0x0C;
    case SDL_SCANCODE_EQUALS: return 0x0D;
    case SDL_SCANCODE_BACKSPACE: return 0x0E;
    case SDL_SCANCODE_TAB: return 0x0F;
    case SDL_SCANCODE_Q: return 0x10;
    case SDL_SCANCODE_W: return 0x11;
    case SDL_SCANCODE_E: return 0x12;
    case SDL_SCANCODE_R: return 0x13;
    case SDL_SCANCODE_T: return 0x14;
    case SDL_SCANCODE_Y: return 0x15;
    case SDL_SCANCODE_U: return 0x16;
    case SDL_SCANCODE_I: return 0x17;
    case SDL_SCANCODE_O: return 0x18;
    case SDL_SCANCODE_P: return 0x19;
    case SDL_SCANCODE_LEFTBRACKET: return 0x1A;
    case SDL_SCANCODE_RIGHTBRACKET: return 0x1B;
    case SDL_SCANCODE_RETURN: return 0x1C;
    case SDL_SCANCODE_KP_ENTER: return 0x1C;
    case SDL_SCANCODE_LCTRL: case SDL_SCANCODE_RCTRL: return 0x1D;
    case SDL_SCANCODE_A: return 0x1E;
    case SDL_SCANCODE_S: return 0x1F;
    case SDL_SCANCODE_D: return 0x20;
    case SDL_SCANCODE_F: return 0x21;
    case SDL_SCANCODE_G: return 0x22;
    case SDL_SCANCODE_H: return 0x23;
    case SDL_SCANCODE_J: return 0x24;
    case SDL_SCANCODE_K: return 0x25;
    case SDL_SCANCODE_L: return 0x26;
    case SDL_SCANCODE_SEMICOLON: return 0x27;
    case SDL_SCANCODE_APOSTROPHE: return 0x28;
    case SDL_SCANCODE_GRAVE: return 0x29;
    case SDL_SCANCODE_LSHIFT: return 0x2A;
    case SDL_SCANCODE_BACKSLASH: return 0x2B;
    case SDL_SCANCODE_Z: return 0x2C;
    case SDL_SCANCODE_X: return 0x2D;
    case SDL_SCANCODE_C: return 0x2E;
    case SDL_SCANCODE_V: return 0x2F;
    case SDL_SCANCODE_B: return 0x30;
    case SDL_SCANCODE_N: return 0x31;
    case SDL_SCANCODE_M: return 0x32;
    case SDL_SCANCODE_COMMA: return 0x33;
    case SDL_SCANCODE_PERIOD: return 0x34;
    case SDL_SCANCODE_SLASH: return 0x35;
    case SDL_SCANCODE_RSHIFT: return 0x36;
    case SDL_SCANCODE_KP_MULTIPLY: return 0x37;
    case SDL_SCANCODE_LALT: case SDL_SCANCODE_RALT: return 0x38;
    case SDL_SCANCODE_SPACE: return 0x39;
    case SDL_SCANCODE_CAPSLOCK: return 0x3A;
    case SDL_SCANCODE_F1: return 0x3B;
    case SDL_SCANCODE_F2: return 0x3C;
    case SDL_SCANCODE_F3: return 0x3D;
    case SDL_SCANCODE_F4: return 0x3E;
    case SDL_SCANCODE_F5: return 0x3F;
    case SDL_SCANCODE_F6: return 0x40;
    case SDL_SCANCODE_F7: return 0x41;
    case SDL_SCANCODE_F8: return 0x42;
    case SDL_SCANCODE_F9: return 0x43;
    case SDL_SCANCODE_F10: return 0x44;
    case SDL_SCANCODE_NUMLOCKCLEAR: return 0x45;
    case SDL_SCANCODE_SCROLLLOCK: return 0x46;
    case SDL_SCANCODE_KP_7: case SDL_SCANCODE_HOME: return 0x47;
    case SDL_SCANCODE_KP_8: case SDL_SCANCODE_UP: return 0x48;
    case SDL_SCANCODE_KP_9: case SDL_SCANCODE_PAGEUP: return 0x49;
    case SDL_SCANCODE_KP_MINUS: return 0x4A;
    case SDL_SCANCODE_KP_4: case SDL_SCANCODE_LEFT: return 0x4B;
    case SDL_SCANCODE_KP_5: return 0x4C;
    case SDL_SCANCODE_KP_6: case SDL_SCANCODE_RIGHT: return 0x4D;
    case SDL_SCANCODE_KP_PLUS: return 0x4E;
    case SDL_SCANCODE_KP_1: case SDL_SCANCODE_END: return 0x4F;
    case SDL_SCANCODE_KP_2: case SDL_SCANCODE_DOWN: return 0x50;
    case SDL_SCANCODE_KP_3: case SDL_SCANCODE_PAGEDOWN: return 0x51;
    case SDL_SCANCODE_KP_0: case SDL_SCANCODE_INSERT: return 0x52;
    case SDL_SCANCODE_KP_PERIOD: case SDL_SCANCODE_DELETE: return 0x53;
    default: return 0;
    }
}

static uint8_t ascii_scancode(char ch, bool *shift)
{
    static const char lower[] = "\0\x1b" "1234567890-=\b\tqwertyuiop[]\r\0asdfghjkl;'`\0\\zxcvbnm,./\0*\0 ";
    static const char upper[] = "\0\x1b" "!@#$%^&*()_+\b\tQWERTYUIOP{}\r\0ASDFGHJKL:\"~\0|ZXCVBNM<>?\0*\0 ";
    for (int i = 1; i < (int)sizeof lower - 1; i++) {
        if (lower[i] == ch) {
            *shift = false;
            return (uint8_t)i;
        }
        if (upper[i] == ch) {
            *shift = true;
            return (uint8_t)i;
        }
    }
    return 0;
}

static void type_char(Pc *pc, char ch)
{
    bool shift;
    uint8_t sc = ascii_scancode(ch, &shift);
    if (!sc)
        return;
    if (shift)
        pc_key_event(pc, 0x2A);
    pc_key_event(pc, sc);
    pc_key_event(pc, sc | 0x80);
    if (shift)
        pc_key_event(pc, 0x2A | 0x80);
}

static void dump_memory(App *app)
{
    SDL_CreateDirectory("extracted");
    if (SDL_SaveFile("extracted/mem_dump.bin", app->pc->mem, CPU_MEM_SIZE))
        SDL_Log("Memory dumped to extracted/mem_dump.bin (CS:IP %04X:%04X)", app->pc->cpu.sregs[S_CS],
                app->pc->cpu.ip);
    else
        SDL_Log("Memory dump failed: %s", SDL_GetError());
}

static void save_screenshot(App *app, const char *path)
{
    SDL_Surface *s = SDL_CreateSurfaceFrom(CGA_W, CGA_H, SDL_PIXELFORMAT_XRGB8888, app->pixels,
                                           CGA_W * (int)sizeof(uint32_t));
    if (s && SDL_SaveBMP(s, path))
        SDL_Log("Screenshot saved to %s", path);
    else
        SDL_Log("Screenshot failed: %s", SDL_GetError());
    SDL_DestroySurface(s);
}

SDL_AppResult SDL_AppInit(void **appstate, int argc, char *argv[])
{
    SDL_SetAppMetadata("Flight Simulator 1", "0.2", "fs1-sdl3");

    App *app = SDL_calloc(1, sizeof(App));
    if (!app)
        return SDL_APP_FAILURE;
    *appstate = app;
    app->speed = 1;

    const char *disk_path = DEFAULT_DISK;
    for (int i = 1; i < argc; i++) {
        if (SDL_strcmp(argv[i], "--frames") == 0 && i + 1 < argc)
            app->max_frames = SDL_atoi(argv[++i]);
        else if (SDL_strcmp(argv[i], "--screenshot") == 0 && i + 1 < argc)
            app->screenshot = argv[++i];
        else if (SDL_strcmp(argv[i], "--type") == 0 && i + 1 < argc)
            app->type_text = argv[++i];
        else
            disk_path = argv[i];
    }

    if (!disk_load(&app->disk, disk_path))
        return SDL_APP_FAILURE;
    if (app->disk.format != DISK_PC_160K) {
        SDL_Log("'%s' is not a PC disk image; only the PC version runs", disk_path);
        return SDL_APP_FAILURE;
    }

    app->pc = SDL_malloc(sizeof(Pc));
    if (!app->pc || !pc_init(app->pc, &app->disk))
        return SDL_APP_FAILURE;
    pc_boot(app->pc);

    if (!SDL_Init(SDL_INIT_VIDEO | SDL_INIT_AUDIO | SDL_INIT_GAMEPAD)) {
        SDL_Log("SDL_Init failed: %s", SDL_GetError());
        return SDL_APP_FAILURE;
    }
    if (!SDL_CreateWindowAndRenderer("Flight Simulator 1", WINDOW_W, WINDOW_H, SDL_WINDOW_RESIZABLE,
                                     &app->window, &app->renderer)) {
        SDL_Log("Window creation failed: %s", SDL_GetError());
        return SDL_APP_FAILURE;
    }
    SDL_SetRenderVSync(app->renderer, 1);
    /* CGA's 200 lines fill a 4:3 display */
    SDL_SetRenderLogicalPresentation(app->renderer, 640, 480, SDL_LOGICAL_PRESENTATION_LETTERBOX);

    app->screen = SDL_CreateTexture(app->renderer, SDL_PIXELFORMAT_XRGB8888, SDL_TEXTUREACCESS_STREAMING,
                                    CGA_W, CGA_H);
    if (!app->screen)
        return SDL_APP_FAILURE;
    SDL_SetTextureScaleMode(app->screen, SDL_SCALEMODE_PIXELART);

    SDL_AudioSpec spec = { SDL_AUDIO_F32, 1, AUDIO_RATE };
    app->audio = SDL_OpenAudioDeviceStream(SDL_AUDIO_DEVICE_DEFAULT_PLAYBACK, &spec, NULL, NULL);
    if (app->audio)
        SDL_ResumeAudioStreamDevice(app->audio);
    else
        SDL_Log("No audio: %s", SDL_GetError());

    app->last_ticks = SDL_GetTicksNS();
    SDL_Log("Booting %s", disk_path);
    return SDL_APP_CONTINUE;
}

SDL_AppResult SDL_AppEvent(void *appstate, SDL_Event *event)
{
    App *app = appstate;
    switch (event->type) {
    case SDL_EVENT_QUIT:
        return SDL_APP_SUCCESS;
    case SDL_EVENT_KEY_DOWN:
        if (event->key.scancode == SDL_SCANCODE_F10) {
            if (!event->key.repeat) {
                app->pc->composite = !app->pc->composite;
                SDL_Log("Monitor: %s", app->pc->composite ? "composite" : "RGB");
            }
            break;
        }
        if (event->key.scancode == SDL_SCANCODE_F11) {
            if (!event->key.repeat) {
                app->speed = app->speed >= 8 ? 1 : app->speed * 2;
                SDL_Log("Emulation speed x%d", app->speed);
            }
            break;
        }
        if (event->key.scancode == SDL_SCANCODE_F12) {
            if (!event->key.repeat)
                dump_memory(app);
            break;
        }
        if (xt_scancode(event->key.scancode))
            pc_key_event(app->pc, xt_scancode(event->key.scancode)); /* repeats = typematic */
        break;
    case SDL_EVENT_KEY_UP:
        if (xt_scancode(event->key.scancode))
            pc_key_event(app->pc, xt_scancode(event->key.scancode) | 0x80);
        break;
    default:
        break;
    }
    return SDL_APP_CONTINUE;
}

SDL_AppResult SDL_AppIterate(void *appstate)
{
    App *app = appstate;
    Pc *pc = app->pc;

    uint64_t now = SDL_GetTicksNS();
    double seconds = (double)(now - app->last_ticks) / 1e9;
    app->last_ticks = now;
    if (app->max_frames || seconds > 0.1)
        seconds = 1.0 / 60.0;

    if (app->type_text && app->frame >= 120 && app->frame % 60 == 0) {
        long i = (app->frame - 120) / 60;
        if (i < (long)SDL_strlen(app->type_text))
            type_char(pc, app->type_text[i]);
    }

    pc_run(pc, pc->cpu.cycles + (uint64_t)(seconds * PC_CPU_HZ * app->speed));

    int n = pc_speaker_render(pc, app->samples, SDL_arraysize(app->samples), AUDIO_RATE);
    if (app->audio && app->speed == 1 && SDL_GetAudioStreamQueued(app->audio) < AUDIO_RATE / 5 * 4)
        SDL_PutAudioStreamData(app->audio, app->samples, n * (int)sizeof(float));

    pc_render_cga(pc, app->pixels);
    SDL_UpdateTexture(app->screen, NULL, app->pixels, CGA_W * sizeof(uint32_t));
    SDL_SetRenderDrawColor(app->renderer, 0, 0, 0, 255);
    SDL_RenderClear(app->renderer);
    SDL_RenderTexture(app->renderer, app->screen, NULL, NULL);
    SDL_RenderPresent(app->renderer);

    app->frame++;
    if (app->max_frames && app->frame >= app->max_frames)
        return SDL_APP_SUCCESS;
    return SDL_APP_CONTINUE;
}

void SDL_AppQuit(void *appstate, SDL_AppResult result)
{
    (void)result;
    App *app = appstate;
    if (!app)
        return;
    if (app->screenshot && app->pc)
        save_screenshot(app, app->screenshot);
    if (app->pc) {
        SDL_Log("Stopped at CS:IP %04X:%04X after %llu cycles, CGA mode %02X color %02X", app->pc->cpu.sregs[S_CS],
                app->pc->cpu.ip,
                (unsigned long long)app->pc->cpu.cycles, app->pc->cga_mode, app->pc->cga_color);
        pc_free(app->pc);
        SDL_free(app->pc);
    }
    SDL_DestroyAudioStream(app->audio);
    SDL_DestroyTexture(app->screen);
    SDL_DestroyRenderer(app->renderer);
    SDL_DestroyWindow(app->window);
    disk_free(&app->disk);
    SDL_free(app);
}
