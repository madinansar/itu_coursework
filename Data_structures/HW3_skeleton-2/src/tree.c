#include "tree.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
//
TreeNode *init_node(GameState *gs){
    TreeNode *newNode = (TreeNode*)malloc(sizeof(TreeNode));
    if(newNode==NULL) return NULL;

    newNode->game_state = gs;
    newNode->num_children = -1; //unknown yet
    newNode->children = NULL;

    return newNode;
}
void construct_subtree(TreeNode *node, int depth) {
    if(depth <= 0 || node == NULL) return;

    GameStatus status = get_game_status(node->game_state);
    if(status != IN_PROGRESS){
        node->num_children = -1;                        
        node->children = NULL;                          
        return;
    }

    int width = node->game_state->width;
    bool *moves = (bool*)malloc(width*sizeof(bool));
    if(moves == NULL){
        node->num_children = 0;
        return; //malloc fails
    }

    int num_moves = available_moves(node->game_state, moves);
    if(num_moves<=0){
        node->num_children = 0;
        free(moves);
        return;
    }
    node->children = (TreeNode **)malloc(num_moves * sizeof(TreeNode *));
    if (node->children == NULL) {
        free(moves);
        node->num_children = 0;
        return; // malloc failed
    }
    node->num_children = num_moves; //this current node will have num_moves children
    

    //create child nodes

    int child_index = 0; //valid children
    for (int i = 0; i < width; i++) {
        if (moves[i]) {
            GameState *new_state = make_move(node->game_state, i);
            if (new_state != NULL) {
                TreeNode *child = init_node(new_state);
                if (child != NULL) {
                    node->children[child_index] = child;
                    child_index++;
                    construct_subtree(child, depth - 1); 
                } else {
                    free(new_state);
                }
            }
        }
}

    node->num_children = child_index;


    if (child_index == 0) {
        free(node->children);
        node->children = NULL;
    }

    free(moves);
}

TreeNode *init_tree(GameState *gs, int depth) {
    if (depth < 2 || gs == NULL) return NULL; 

    TreeNode *root = init_node(gs);
    if (root == NULL) return NULL;
    depth--;

    construct_subtree(root, depth); //if(depth>0) do i need this? or depth>2 is guaranteed

    return root;
}

void free_tree(TreeNode *root) {    //post-order
    if (root == NULL) {
        return; 
    }

    if (root->children != NULL) {
        for (int i = 0; i < root->num_children; i++) {
            free_tree(root->children[i]);
        }
        free(root->children);
    }

    if (root->game_state != NULL) {  
        free_game_state(root->game_state);
    }
    free(root);
}

void expand_tree(TreeNode *root){
    if(root == NULL) return;

    GameStatus status = get_game_status(root->game_state);
    if(status != IN_PROGRESS){
        root->num_children = -1;                        //test: if this is =0, then 11/17
        root->children = NULL;                          //test: delete this line
        return;
    }

//node already has children:
    if(root->num_children>0 && root->children != NULL){
        for(int i=0; i<root->num_children; i++){
            expand_tree(root->children[i]);     //recursively expand each child
        }
        return;
    }
//node is leaf:
    bool *moves = (bool*)malloc(root->game_state->width*sizeof(bool));  //array of bools for each column
    int num_moves = available_moves(root->game_state, moves);

    if(num_moves>0){
        root->children = (TreeNode**)malloc(num_moves*sizeof(TreeNode*));
        root->num_children = num_moves;

        int child_index = 0;
        for(int move =0; move < root->game_state->width; move++){
            if(moves[move]){
                GameState *child_state = make_move(root->game_state, move);
                if (child_state != NULL) {
                    root->children[child_index] = init_node(child_state);
                    child_index++;
                } else{
                    free(child_state);
                }
            }
        }
    } else {

        root->num_children = 0;
        root->children = NULL;
    }
    free(moves);

}

int node_count(TreeNode *root){
    if(root==NULL){
        return 0;
    }
    int count = 1;
    for(int i=0; i<root->num_children; i++){
        count += node_count(root->children[i]);
    }
    return count;
}

void print_tree(TreeNode *root, int level) {
    if (root == NULL) {
        return; 
    }

    for (int i = 0; i < level; i++) {
        printf("  "); 
    }

    printf("Node at level %d:\n", level);
    printf("  GameState: %s\n", root->game_state->board); 
    printf("  Number of children: %d\n", root->num_children);

    for (int i = 0; i < root->num_children; i++) {
        print_tree(root->children[i], level + 1); 
    }
}
