# Congklak Game

A Python-based implementation of the traditional **Congklak board game** for two players, including an AI player based on the **Minimax algorithm with Alpha-Beta Pruning**.

##  About the Game

Congklak is a traditional board game in which players distribute seeds across a set of holes on the board. The objective is to collect more seeds in your store than your opponent.

This project also includes an **AI opponent** that analyzes possible game moves and selects a strategic move using the Minimax algorithm.

##  How to Play

* The game is played by **two players**: a human player and an AI opponent.
* Each player has their own side of the board and a **store**.
* On each turn, a player selects one of their non-empty holes.
* The player distributes the seeds one by one according to the game rules.
* The AI analyzes possible moves and chooses a move based on the current game state.
* Players continue taking turns until the game reaches its end condition.
* The player with the most seeds in their store wins.

##  Game Rules

* Players can only select holes from their own side of the board.
* Seeds are distributed one at a time in consecutive holes.
* A player's store is included when distributing seeds.
* The opponent's store is skipped.
* The game follows specific capture and turn rules depending on where the last seed is placed.
* The game ends when the required end condition is reached.
* The winner is determined by comparing the number of seeds collected by both players.

##  AI Strategy

The AI uses the **Minimax algorithm** to evaluate possible future game states and select a move that maximizes its advantage while considering the opponent's best possible response.

**Alpha-Beta Pruning** is used to optimize Minimax by eliminating branches of the game tree that cannot influence the final decision. This significantly reduces the number of game states that need to be evaluated, allowing the AI to make decisions more efficiently while producing the same result as standard Minimax.

This approach is suitable for Congklak because the game involves **sequential decisions and competing objectives**: each move changes the board state and affects the possible moves available to both players.

##  Technologies

* **Python**
* **Minimax Algorithm**
* **Alpha-Beta Pruning**
* **Object-Oriented Programming**
* **Data Structures and Algorithms**

##  Author

**Sarra Homada**
**Salma Belaalia**
