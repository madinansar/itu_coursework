#ifndef UTILITIES_H
#define UTILITIES_H

#include "fs.h" 

extern FILE *disk;
extern SuperBlock sb;
extern unsigned char bitmap[BLOCK_SIZE];
extern Inode inodes[128];

void read_block(int block_num, void *buf);
void write_block(int block_num, const void *buf);

void load_fs();
void save_fs();

int alloc_block();
void free_block(int block_num);
int alloc_inode();
void free_inode(int idx);

int find_in_dir(int dir_ino, const char *name);
int add_to_dir(int dir_ino, const char *name, int child_ino);
int remove_from_dir(int dir_ino, const char *name);
int is_dir_empty(int dir_ino);

int traverse_path(const char *path, int *parent_ino_out, char *name_out);

#endif
