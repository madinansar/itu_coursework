#include <stdio.h>
#include <string.h>
#include "fs.h"
#include "utilities.h"

int main(int argc, char *argv[]) {
    if (argc < 3) {
        printf("Usage: %s <command> <path> [data]\n", argv[0]);
        return 1;
    }

    const char *cmd = argv[1];
    const char *path = argv[2];

    if (strcmp(cmd, "mkfs") == 0) {
        mkfs(path);  // path is disk filename
    } else if (strcmp(cmd, "mkdir_fs") == 0) {
        if (mkdir_fs(path) == 0){
            printf("Directory created.\n");
        } else {
            printf("Directory create failed.\n");
        }

    } else if (strcmp(cmd, "create_fs") == 0) {
        if (create_fs(path) == 0) {
            printf("File created.\n");
        } else {
            printf("File create failed.\n");
        }
    } else if (strcmp(cmd, "write_fs") == 0) {
        if (argc < 4) {
            fprintf(stderr, "Usage: %s write_fs <path> <data>\n", argv[0]);
            return 1;
        }
        if (write_fs(path, argv[3]) == 0) {
            printf("Write successful.\n");
        } else {
            printf("Write failed.\n");
        }
    } else if (strcmp(cmd, "read_fs") == 0) {
        char buf[4096];
        int n = read_fs(path, buf, sizeof(buf));
        if (n >= 0) {
            buf[n] = '\0';
            printf("Read (%d bytes): %s\n", n, buf);
        } else {
            printf("Read failed.\n");
        }
    } else if (strcmp(cmd, "ls_fs") == 0) {
        DirectoryEntry entries[32];
        int n = ls_fs(path, entries, 32);
        for (int i = 0; i < n; ++i) {
            printf(" - %s (inode %d)\n", entries[i].name, entries[i].inode_number);
        }
    } else if (strcmp(cmd, "delete_fs") == 0) {
        if (delete_fs(path) == 0) {
            printf("File deleted.\n");
        } else {
            printf("File delete failed.\n");
        }
    } else if (strcmp(cmd, "rmdir_fs") == 0) {
        if (rmdir_fs(path) == 0) {
            printf("Directory deleted.\n");
        } else {
            printf("Directory delete failed.\n");
        }
    } else {
        fprintf(stderr, "Unknown command: %s\n", cmd);
        return 1;
    }

    return 0;
}
