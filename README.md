# AI Chess: Rational Agent Implementation

This repository contains the source code for the AI Chess project, developed as the final project for the Principles of AI course. The project implements a fully autonomous, rational AI agent capable of playing chess against a human opponent while maximizing its expected outcome.

## 🧠 The Three Foundational Pillars

This project is built upon three core artificial intelligence principles:

1. Logic (First-Order Logic & Inference):
   The rules of chess, including legal move generation, check, checkmate, and stalemate detection, are enforced using logical inference rules. The `logic.py` module         evaluates the state space and prevents illegal transitions, ensuring the AI operates within strict environmental constraints.

2. The Math of AI (Linear Algebra & Probability):
   The board is represented as an 8x8 matrix, allowing the AI to use Piece-Square Tables (PST) to evaluate positional advantages. The evaluation function calculates the        Expected Value of any given board state based on material advantage, center control, pawn structure, king safety, and mobility.

3. Optimization (Heuristic Search):
   The decision-making core uses the Minimax algorithm heavily optimized with Alpha-Beta Pruning to drastically reduce the search space complexity. Additional optimizations include:
   * Zobrist Hashing (Transposition Tables): Caches previously evaluated board states.
   * Move Ordering (MVV-LVA & Killer Heuristics): Prioritizes high-value captures to increase pruning efficiency.
   * Quiescence Search: Mitigates the horizon effect by continuing the search through active capture sequences.
   * Null Move Pruning & Late Move Reductions (LMR): Safely discards weak branches early.

---

## 📁 Repository Structure

The codebase is modularly separated according to the PEAS (Performance, Environment, Actuators, Sensors) architecture:

*  - Contains `Game_engine_2.py`, the main entry point handling the Pygame loop and state management.
*  - Contains `logic.py`, which validates moves, line-of-sight, and check/checkmate conditions.
*  - Contains `AI_CHESS.py` (Search & Optimizations) and `advanced_evaluation.py` (Mathematical Modeling and Heuristics).
*  - UI assets, fonts, and layout management.
*  - Contains the final PDF report, presentation slides, performance benchmark graphs, and the video demo link.

---

## 🚀 Installation & Setup

### Prerequisites
* Python 3.8 or higher.
* `pygame` library.

### 1. Install Dependencies
Open your terminal or command prompt and install the required Pygame library:
```bash
pip install pygame
