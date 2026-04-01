#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "fs.h"
#include "utilities.h"

// globals
FILE *disk = NULL;
SuperBlock sb;
unsigned char bitmap[BLOCK_SIZE];
Inode inodes[128]; 

// read a block from disk
void read_block(int block_num, void *buf) {
    fseek(disk, block_num * BLOCK_SIZE, SEEK_SET);
    fread(buf, BLOCK_SIZE, 1, disk);
}

// write a block to disk
void write_block(int block_num, const void *buf) {
    fseek(disk, block_num * BLOCK_SIZE, SEEK_SET);
    fwrite(buf, BLOCK_SIZE, 1, disk);
}

// load SuperBlock, bitmap, and inode table into memory
void load_fs() {
    read_block(0, &sb);
    read_block(sb.bitmap_start, bitmap);
    int inode_bytes = sb.num_inodes * sizeof(Inode);
    int blocks_needed = (inode_bytes + BLOCK_SIZE - 1) / BLOCK_SIZE;
    for (int i = 0; i < blocks_needed; ++i) {
        read_block(sb.inode_start + i, ((char*)inodes) + i * BLOCK_SIZE);
    }
}

// save SuperBlock, bitmap, and inode table to disk
void save_fs() {
    write_block(0, &sb);
    write_block(sb.bitmap_start, bitmap);
    for (size_t i = 0; i < sb.num_inodes * sizeof(Inode) / BLOCK_SIZE; ++i) {
        write_block(sb.inode_start + i, ((char*)inodes) + i * BLOCK_SIZE);
    }
}

// allocate a free data block
int alloc_block() {
    for (int i = 0; i < sb.num_blocks - sb.data_start; ++i) {
        int byte = i / 8, bit = i % 8;
        if (!(bitmap[byte] & (1 << bit))) {
            bitmap[byte] |= (1 << bit);
            return sb.data_start + i;
        }
    }
    fprintf(stderr, "Error: disk is full\n");
    return -1;
}

// free a previously allocated data block
void free_block(int block) {
    int idx = block - sb.data_start;
    int byte = idx / 8, bit = idx % 8;
    bitmap[byte] &= ~(1 << bit);
}

// allocate an unused inode
int alloc_inode() {
    for (int i = 1; i < sb.num_inodes; ++i) {
        if (!inodes[i].is_valid) {
            inodes[i].is_valid = 1;
            return i;
        }
    }
    fprintf(stderr, "Error: inode table is full\n");
    return -1;
}

// free a previously used inode
void free_inode(int idx) {
    memset(&inodes[idx], 0, sizeof(Inode));
}

// find a file/dir by name in a directory inode
int find_in_dir(int dir_ino, const char *name) {
    DirectoryEntry entries[BLOCK_SIZE / sizeof(DirectoryEntry)];
    Inode *dir = &inodes[dir_ino];
    for (int i = 0; i < 4; ++i) {
        if (!dir->direct_blocks[i]) continue;
        read_block(dir->direct_blocks[i], entries);
        for (int j = 0; j < 32; ++j) {
            if (strcmp(entries[j].name, name) == 0) {
                return entries[j].inode_number;
            }
        }
    }
    return -1;
}

// add new entry to directory inode
int add_to_dir(int dir_ino, const char *name, int child_ino) {
    DirectoryEntry entries[BLOCK_SIZE / sizeof(DirectoryEntry)] = {0};
    Inode *dir = &inodes[dir_ino];
    for (int i = 0; i < 4; ++i) {
        if (dir->direct_blocks[i] == 0) {
            int blk = alloc_block();
            if (blk == -1) return -1;
            dir->direct_blocks[i] = blk;
            memset(entries, 0, sizeof(entries));
        } else {
            read_block(dir->direct_blocks[i], entries);
        }

        for (int j = 0; j < 32; ++j) {
            if (entries[j].inode_number == 0) {
                entries[j].inode_number = child_ino;
                strncpy(entries[j].name, name, 27);
                entries[j].name[27] = '\0';
                write_block(dir->direct_blocks[i], entries);
                dir->size++;
                return 0;
            }
        }
    }
    fprintf(stderr, "Error: directory is full\n");
    return -1;
}

int remove_from_dir(int dir_ino, const char *name) {
    DirectoryEntry entries[BLOCK_SIZE / sizeof(DirectoryEntry)];
    Inode *dir = &inodes[dir_ino];

    for (int i = 0; i < 4; ++i) {
        if (!dir->direct_blocks[i]) continue;
        read_block(dir->direct_blocks[i], entries);
        for (int j = 0; j < 32; ++j) {
            if (strcmp(entries[j].name, name) == 0) {
                entries[j].inode_number = 0;
                entries[j].name[0] = '\0';
                write_block(dir->direct_blocks[i], entries);
                dir->size--;
                return 0;
            }
        }
    }
    return -1;
}
int is_dir_empty(int dir_ino) {
    for (int i = 0; i < 4; ++i) {
        if (!inodes[dir_ino].direct_blocks[i]) continue;
        DirectoryEntry entries[32];
        read_block(inodes[dir_ino].direct_blocks[i], entries);
        for (int j = 0; j < 32; ++j) {
            if (entries[j].inode_number != 0) {
                return 0; // directory is not empty
            }
        }
    }
    return 1; // directory is empty
}

int traverse_path(const char *path, int *parent_ino_out, char *name_out) {
    if (!path || path[0] != '/') return -1;

    char temp[256];
    strncpy(temp, path, sizeof(temp));
    temp[sizeof(temp)-1] = '\0';

    if (strcmp(path, "/") == 0) {
        *parent_ino_out = 0;
        name_out[0] = '\0';
        return 0;
    }


    // tokenizing
    char *tokens[32];
    int token_count = 0;
    char *token = strtok(temp, "/");
    while (token && token_count < 32) {
        tokens[token_count++] = token;
        token = strtok(NULL, "/");
    }

    int curr_ino = 0; 

    for (int i = 0; i < token_count - 1; ++i) {
        int next_ino = find_in_dir(curr_ino, tokens[i]);
        if (next_ino == -1 || !inodes[next_ino].is_directory) return -1;
        curr_ino = next_ino;
    }

    *parent_ino_out = curr_ino;
    strncpy(name_out, tokens[token_count - 1], 28);
    return 0;
}
