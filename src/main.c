/*
 * Microsoft Flight Simulator 1.0x (IBM PC, 1982) - SDL3 port.
 *
 * Phase 1 scaffold: opens a window sized for CGA mode 4 (320x200), loads the
 * original booter disk image and presents an empty frame.
 * See docs/PORT_PLAN.md for the roadmap.
 */
#define SDL_MAIN_USE_CALLBACKS 1
#include <SDL3/SDL.h>
#include <SDL3/SDL_main.h>

#include "disk.h"

#define SCREEN_W 320
#define SCREEN_H 200
#define WINDOW_SCALE 3
#define DEFAULT_DISK "original/Microsoft Flight Simulator v1.05 (198x)(Microsoft Corporation).ima"

typedef struct App {
    SDL_Window *window;
    SDL_Renderer *renderer;
    SDL_Texture *screen;
    uint32_t pixels[SCREEN_W * SCREEN_H];
    Disk disk;
} App;

SDL_AppResult SDL_AppInit(void **appstate, int argc, char *argv[])
{
    SDL_SetAppMetadata("Flight Simulator 1", "0.1", "fs1-sdl3");

    App *app = SDL_calloc(1, sizeof(App));
    if (!app)
        return SDL_APP_FAILURE;
    *appstate = app;

    const char *disk_path = argc > 1 ? argv[1] : DEFAULT_DISK;
    if (!disk_load(&app->disk, disk_path))
        return SDL_APP_FAILURE;

    if (!SDL_Init(SDL_INIT_VIDEO | SDL_INIT_GAMEPAD)) {
        SDL_Log("SDL_Init failed: %s", SDL_GetError());
        return SDL_APP_FAILURE;
    }
    if (!SDL_CreateWindowAndRenderer("Flight Simulator 1", SCREEN_W * WINDOW_SCALE, SCREEN_H * WINDOW_SCALE,
                                     SDL_WINDOW_RESIZABLE, &app->window, &app->renderer)) {
        SDL_Log("Window creation failed: %s", SDL_GetError());
        return SDL_APP_FAILURE;
    }
    SDL_SetRenderVSync(app->renderer, 1);
    SDL_SetRenderLogicalPresentation(app->renderer, SCREEN_W, SCREEN_H, SDL_LOGICAL_PRESENTATION_INTEGER_SCALE);

    app->screen = SDL_CreateTexture(app->renderer, SDL_PIXELFORMAT_XRGB8888, SDL_TEXTUREACCESS_STREAMING,
                                    SCREEN_W, SCREEN_H);
    if (!app->screen)
        return SDL_APP_FAILURE;
    SDL_SetTextureScaleMode(app->screen, SDL_SCALEMODE_NEAREST);

    SDL_Log("Loaded %s (%d tracks x %d sectors x %d bytes)", disk_path, app->disk.tracks,
            app->disk.sectors_per_track, app->disk.sector_size);
    return SDL_APP_CONTINUE;
}

SDL_AppResult SDL_AppEvent(void *appstate, SDL_Event *event)
{
    (void)appstate;
    if (event->type == SDL_EVENT_QUIT)
        return SDL_APP_SUCCESS;
    if (event->type == SDL_EVENT_KEY_DOWN && event->key.key == SDLK_ESCAPE)
        return SDL_APP_SUCCESS;
    return SDL_APP_CONTINUE;
}

SDL_AppResult SDL_AppIterate(void *appstate)
{
    App *app = appstate;

    SDL_UpdateTexture(app->screen, NULL, app->pixels, SCREEN_W * sizeof(uint32_t));
    SDL_SetRenderDrawColor(app->renderer, 0, 0, 0, 255);
    SDL_RenderClear(app->renderer);
    SDL_RenderTexture(app->renderer, app->screen, NULL, NULL);
    SDL_RenderPresent(app->renderer);
    return SDL_APP_CONTINUE;
}

void SDL_AppQuit(void *appstate, SDL_AppResult result)
{
    (void)result;
    App *app = appstate;
    if (!app)
        return;
    SDL_DestroyTexture(app->screen);
    SDL_DestroyRenderer(app->renderer);
    SDL_DestroyWindow(app->window);
    disk_free(&app->disk);
    SDL_free(app);
}
