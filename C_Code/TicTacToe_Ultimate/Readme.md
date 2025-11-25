# 🎮 TicTacToe-Ultimate

![C Language](https://img.shields.io/badge/Language-C-blue?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Console-green?style=for-the-badge)
![AI](https://img.shields.io/badge/AI-Minimax-red?style=for-the-badge)

A fully-featured console-based **Tic-Tac-Toe** game implemented in **C**, supporting both **Player vs Player** and **Player vs Computer (AI)** modes. The AI uses the **Minimax algorithm**, making it unbeatable!  

---

## ✨ Features

- **Two Game Modes**:  
  - Player vs Player (PvP)  
  - Player vs Computer (PvC) with perfect AI  
- **Console-based Interface**: Clear and user-friendly display  
- **Unbeatable AI**: Computer always makes the optimal move  
- **Replay Option**: Play multiple rounds without restarting  
- **Cross-Platform**: Works on Windows and Linux  

---

## 📜 Game Rules

| Rule | Description |
|------|-------------|
| Grid | 3x3 board |
| Player 1 | `X` |
| Player 2 / Computer | `O` |
| Objective | Align 3 marks horizontally, vertically, or diagonally |
| Draw | All cells filled without a winner |

---

## 🛠️ Installation

```bash
git clone https://github.com/yourusername/TicTacToe-Ultimate.git
cd TicTacToe-Ultimate
gcc -o TicTacToe main.c
./TicTacToe