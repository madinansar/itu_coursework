#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "fs.h"
#include "utilities.h"

void mkfs(const char *diskfile) {
    disk = fopen(diskfile, "w+b");
    if (!disk) {
        perror("fopen");
        exit(1);
    }

    char zero[BLOCK_SIZE] = {0};
    for (int i = 0; i < 1024; ++i) fwrite(zero, BLOCK_SIZE, 1, disk);

    sb.magic_number = 0x4D495346;
    sb.num_blocks = 1024;
    sb.num_inodes = 128;
    sb.bitmap_start = 1;
    sb.inode_start = 2;
    sb.data_start = 11;

    memset(bitmap, 0, BLOCK_SIZE);
    memset(inodes, 0, sizeof(inodes));

    inodes[0].is_valid = 1;
    inodes[0].is_directory = 1;
    inodes[0].owner_id = 150220939;
    inodes[0].size = 0;

    save_fs();
    fclose(disk);
    printf("Created filesystem in %s\n", diskfile);
}

int mkdir_fs(const char *path) {
    disk = fopen("disk.img", "r+b");
    if (!disk) return -1;

    load_fs();

    int parent_ino;
    char name[28];

    if (traverse_path(path, &parent_ino, name) == -1) {
        fclose(disk);
        return -1;
    }

    if (find_in_dir(parent_ino, name) != -1) {
        fclose(disk);
        return -1;
    }

    int new_ino = alloc_inode();
    if (new_ino == -1) {
        fclose(disk);
        return -1;
    }

    inodes[new_ino].is_valid = 1;  
    inodes[new_ino].is_directory = 1; // a dir
    inodes[new_ino].size = 0;
    inodes[new_ino].owner_id = 150220939;

    int blk = alloc_block();
    if (blk == -1) {
        inodes[new_ino].is_valid = 0; 
        fclose(disk);
        return -1;
    }

    inodes[new_ino].direct_blocks[0] = blk;

    if (add_to_dir(parent_ino, name, new_ino) == -1) {
        inodes[new_ino].is_valid = 0;
        fclose(disk);
        return -1;
    }

    save_fs();
    fclose(disk);
    return 0;
}

int create_fs(const char *path) {
    disk = fopen("disk.img", "r+b");
    if (!disk) return -1;

    load_fs();

    int parent_ino;
    char name[28];

    if (traverse_path(path, &parent_ino, name) == -1) {
        fclose(disk);
        return -1;
    }

    if (find_in_dir(parent_ino, name) != -1) {
        fclose(disk);
        return -1;
    }

    int new_ino = alloc_inode();
    if (new_ino == -1) {
        fclose(disk);
        return -1;
    }

    inodes[new_ino].is_valid = 1;
    inodes[new_ino].is_directory = 0;  // a file
    inodes[new_ino].size = 0;
    inodes[new_ino].owner_id = 150220939;

    if (add_to_dir(parent_ino, name, new_ino) == -1) {
        inodes[new_ino].is_valid = 0; 
        fclose(disk);
        return -1;
    }

    save_fs();
    fclose(disk);
    return 0;
}


int write_fs(const char *path, const char *data) {
    disk = fopen("disk.img", "r+b");
    if (!disk) return -1;
    load_fs();

    int parent_ino;
    char name[28];
    if (traverse_path(path, &parent_ino, name) == -1) return -1;
    int file_ino = find_in_dir(parent_ino, name);

    if (file_ino == -1 || inodes[file_ino].is_directory) return -1;

    int len = strlen(data);
    int needed_blocks = (len + BLOCK_SIZE - 1) / BLOCK_SIZE;
    if (needed_blocks > 4) return -1;

    for (int i = 0; i < 4; ++i) {
        if (inodes[file_ino].direct_blocks[i]) {
            free_block(inodes[file_ino].direct_blocks[i]);
            inodes[file_ino].direct_blocks[i] = 0;
        }
    }

    const char *p = data;
    for (int i = 0; i < needed_blocks; ++i) {
        int blk = alloc_block();
        if (blk == -1) return -1;
        inodes[file_ino].direct_blocks[i] = blk;
        char buf[BLOCK_SIZE] = {0};
        int copy = (len > BLOCK_SIZE) ? BLOCK_SIZE : len;
        memcpy(buf, p, copy);
        write_block(blk, buf);
        p += copy;
        len -= copy;
    }
    inodes[file_ino].size = strlen(data);
    save_fs();
    fclose(disk);
    return 0;
}

int read_fs(const char *path, char *buf, int bufsize) {
    disk = fopen("disk.img", "rb");
    if (!disk) return -1;
    load_fs();

    int parent_ino;
    char name[28];
    if (traverse_path(path, &parent_ino, name) == -1) {
        fclose(disk);
        return -1;
    }

    int file_ino = find_in_dir(parent_ino, name);
    if (file_ino == -1 || inodes[file_ino].is_directory) {
        fclose(disk);
        return -1;
    }

    int size = inodes[file_ino].size;
    if (bufsize < size) {
        fclose(disk);
        return -1;
    }

    int copied = 0;
    for (int i = 0; i < 4 && copied < size; ++i) {
        int blk = inodes[file_ino].direct_blocks[i];
        if (!blk) continue;
        char temp[BLOCK_SIZE];
        read_block(blk, temp);
        int to_copy = (size - copied > BLOCK_SIZE) ? BLOCK_SIZE : size - copied;
        memcpy(buf + copied, temp, to_copy);
        copied += to_copy;
    }

    fclose(disk);
    return copied;
}


int delete_fs(const char *path) {
    disk = fopen("disk.img", "r+b");
    if (!disk) return -1;
    load_fs();

    int parent_ino;
    char name[28];
    if (traverse_path(path, &parent_ino, name) == -1) return -1;

    int target_ino = find_in_dir(parent_ino, name);
    if (target_ino == -1 || inodes[target_ino].is_directory) return -1;

    for (int i = 0; i < 4; ++i) {
        if (inodes[target_ino].direct_blocks[i]) {
            free_block(inodes[target_ino].direct_blocks[i]);
        }
    }
    free_inode(target_ino);
    remove_from_dir(parent_ino, name);
    save_fs();
    fclose(disk);
    return 0;
}

int rmdir_fs(const char *path) {
    disk = fopen("disk.img", "r+b");
    if (!disk) return -1;
    load_fs();

    int parent_ino;
    char name[28];
    if (traverse_path(path, &parent_ino, name) == -1) return -1;

    int target_ino = find_in_dir(parent_ino, name);
    if (target_ino == -1 || !inodes[target_ino].is_directory)
        return -1;

    if (!is_dir_empty(target_ino)) {
        // dir not empty, can't remove
        fclose(disk);
        return -1;
    }

    free_inode(target_ino);
    remove_from_dir(parent_ino, name);
    save_fs();
    fclose(disk);
    return 0;
}

int ls_fs(const char *path, DirectoryEntry *entries, int max_entries) {
    disk = fopen("disk.img", "rb");
    if (!disk) return -1;
    load_fs();

    int parent_ino;
    char name[28];

    if (traverse_path(path, &parent_ino, name) == -1) {
        fclose(disk);
        return -1;
    }

    int dir_ino;
    if (strlen(name) == 0) {
        dir_ino = parent_ino;
    } else {
        dir_ino = find_in_dir(parent_ino, name);
        if (dir_ino == -1 || !inodes[dir_ino].is_directory) {
            fclose(disk);
            return -1;
        }
    }

    int count = 0;
    for (int i = 0; i < 4 && count < max_entries; ++i) {
        if (!inodes[dir_ino].direct_blocks[i]) continue;
        DirectoryEntry temp[32];
        read_block(inodes[dir_ino].direct_blocks[i], temp);
        for (int j = 0; j < 32 && count < max_entries; ++j) {
            if (temp[j].inode_number != 0) {
                entries[count++] = temp[j];
            }
        }
    }

    fclose(disk);
    return count;
}

