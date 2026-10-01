#ifndef FS1_DISK_H
#define FS1_DISK_H

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

#define DISK_TRACKS      35
#define DISK_SECTORS     16
#define DISK_SECTOR_SIZE 256
#define DISK_IMAGE_SIZE  (DISK_TRACKS * DISK_SECTORS * DISK_SECTOR_SIZE)

/* 140K Apple II 5.25" image in DOS 3.3 logical sector order (.dsk / .do). */
typedef struct Disk {
    uint8_t data[DISK_IMAGE_SIZE];
} Disk;

bool disk_load(Disk *disk, const char *path);
const uint8_t *disk_sector(const Disk *disk, int track, int sector);

#endif
