#include <stdio.h>
#include <stdlib.h>

#define PLAYER_X 'X'
#define PLAYER_O 'O'
#define EMPTY_CELL ' '

// Global board 
char board[10];

// Function declarations
void initializeBoard();
void displayBoard();
int checkWin();
int isMovesLeft();
int minimax(int isMaximizing);
int findBestMove();
void clearScreen();
int getPlayerMove(int player);

// Main function
int main() {
    int playAgain = 1;

    while (playAgain == 1) {
        int mode;
        printf("=== TIC-TAC-TOE ===\n");
        printf("Choose Game Mode:\n1. Player vs Player\n2. Player vs Computer\nYour choice: ");
        scanf("%d", &mode);
        if (mode != 1 && mode != 2) mode = 2; // default to PvC

        initializeBoard();
        displayBoard();

        int currentPlayer = 1; // Player 1 starts
        while (1) {
            int move;
            if (mode == 1 || (mode == 2 && currentPlayer == 1)) {

                //  player move

                move = getPlayerMove(currentPlayer);
                board[move] = (currentPlayer == 1) ? PLAYER_X : PLAYER_O;
            } else {

                // Computer move

                move = findBestMove();
                board[move] = PLAYER_O;
                printf("Computer chooses %d\n", move);
            }

            displayBoard();

            int result = checkWin();
            if (result == 1) {
                if (mode == 2 && currentPlayer == 2)
                    printf("Computer wins!\n");
                else
                    printf("Player %d wins!\n", currentPlayer);
                break;
            } else if (result == 0) {
                printf("Draw!\n");
                break;
            }

            currentPlayer = (currentPlayer == 1) ? 2 : 1;
        }

        printf("\n1. Play again?  2. Exit: ");
        scanf("%d", &playAgain);
        clearScreen();
    }

    return 0;
}

// Initialize board 

void initializeBoard() {
    for (int i = 1; i <= 9; i++)
        board[i] = '0' + i;
}

// Display current board
void displayBoard() {
    clearScreen();
    printf("\n\n=== TIC-TAC-TOE ===\n\n");
    printf("     |     |     \n");
    printf("  %c  |  %c  |  %c  \n", board[1], board[2], board[3]);
    printf("_____|_____|_____\n");
    printf("     |     |     \n");
    printf("  %c  |  %c  |  %c  \n", board[4], board[5], board[6]);
    printf("_____|_____|_____\n");
    printf("     |     |     \n");
    printf("  %c  |  %c  |  %c  \n", board[7], board[8], board[9]);
    printf("     |     |     \n\n");
}

// Check if someone won
// Returns 1 if win, 0 if draw, -1 
int checkWin() {
    int winCombos[8][3] = {
        {1,2,3}, {4,5,6}, {7,8,9},
        {1,4,7}, {2,5,8}, {3,6,9},
        {1,5,9}, {3,5,7}
    };

    for (int i = 0; i < 8; i++) {
        if (board[winCombos[i][0]] == board[winCombos[i][1]] &&
            board[winCombos[i][1]] == board[winCombos[i][2]]) {
            return 1;
        }
    }

    for (int i = 1; i <= 9; i++)
        if (board[i] != PLAYER_X && board[i] != PLAYER_O)
            return -1;

    return 0; // Draw
}

// Check if moves are left
int isMovesLeft() {
    for (int i = 1; i <= 9; i++)
        if (board[i] != PLAYER_X && board[i] != PLAYER_O)
            return 1;
    return 0;
}

// Minimax algorithm for perfect AI
int minimax(int isMaximizing) {
    int result = checkWin();
    if (result == 1) return isMaximizing ? -10 : 10;
    if (!isMovesLeft()) return 0;

    if (isMaximizing) {
        int best = -1000;
        for (int i = 1; i <= 9; i++) {
            if (board[i] != PLAYER_X && board[i] != PLAYER_O) {
                char backup = board[i];
                board[i] = PLAYER_O;
                int val = minimax(0);
                best = (val > best) ? val : best;
                board[i] = backup;
            }
        }
        return best;
    } else {
        int best = 1000;
        for (int i = 1; i <= 9; i++) {
            if (board[i] != PLAYER_X && board[i] != PLAYER_O) {
                char backup = board[i];
                board[i] = PLAYER_X;
                int val = minimax(1);
                best = (val < best) ? val : best;
                board[i] = backup;
            }
        }
        return best;
    }
}

// Find best move for AI
int findBestMove() {
    int bestVal = -1000;
    int move = 0;
    for (int i = 1; i <= 9; i++) {
        if (board[i] != PLAYER_X && board[i] != PLAYER_O) {
            char backup = board[i];
            board[i] = PLAYER_O;
            int moveVal = minimax(0);
            board[i] = backup;
            if (moveVal > bestVal) {
                bestVal = moveVal;
                move = i;
            }
        }
    }
    return move;
}

// Clear terminal screen
void clearScreen() {
    #if defined(_WIN32) || defined(_WIN64)
        system("cls");
    #else
        system("clear");
    #endif
}

// Get valid player move
int getPlayerMove(int player) {
    int input;
    while (1) {
        printf("Player %d turn (1-9): ", player);
        if (scanf("%d", &input) != 1) {
            while (getchar() != '\n'); // flush input
            continue;
        }
        if (input >= 1 && input <= 9 && board[input] != PLAYER_X && board[input] != PLAYER_O)
            return input;
    }
}
