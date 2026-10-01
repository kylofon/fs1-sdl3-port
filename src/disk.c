#include "disk.h"

#include <SDL3/SDL.h>

bool disk_load(Disk *disk, const char *path)
{
    size_t size = 0;
    void *buf = SDL_LoadFile(path, &size);
    if (!buf) {
        SDL_Log("Cannot read disk image '%s': %s", path, SDL_GetError());
        return false;
    }
    if (size != DISK_IMAGE_SIZE) {
        SDL_Log("'%s' is %u bytes, expected %d (35-track DOS-order .dsk)", path, (unsigned)size, DISK_IMAGE_SIZE);
        SDL_free(buf);
        return false;
    }
    SDL_memcpy(disk->data, buf, DISK_IMAGE_SIZE);
    SDL_free(buf);
    return true;
}

const uint8_t *disk_sector(const Disk *disk, int track, int sector)
{
    if (track < 0 || track >= DISK_TRACKS || sector < 0 || sector >= DISK_SECTORS)
        return NULL;
    return disk->data + ((size_t)track * DISK_SECTORS + sector) * DISK_SECTOR_SIZE;
}
