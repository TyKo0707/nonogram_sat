# Documentation

## Disclaimer
*Copied from example homework solution*

The SAT solver used is [Glucose](https://www.labri.fr/perso/lsimon/research/glucose/), more specifically [Glucose 4.2.1](https://github.com/audemard/glucose). The source code is compiled using

```
git clone https://github.com/audemard/glucose.git
cd glucose/simp
make clean
make
mv glucose ../../glucose_solver
```

This example contains a compiled MacOS binary of the Glucose solver. 
For optimal experience, I encourage you to compile the SAT solver yourself. 
Note that the solver, as well as the Python script, are assumed to work on UNIX-based systems. 
In case you prefer using Windows, we recommend to use WSL.

## Problem Description

The **Nonograms** are picture logic puzzles in which cells in a grid must be colored or left blank according to numbers at the edges of the grid to reveal a hidden picture. In this puzzle, the numbers are a form of discrete tomography that measures how many unbroken lines of filled-in squares there are in any given row or column.

An example of a valid input format is:

```json
{
  "cols": [[3], [1, 1], [2], [1, 1], [3]],
  "rows": [[3], [1, 1], [2], [1, 1], [3]]
}

```

Where:

- `cols` specifies column constraints from top to bottom
- `rows` specifies row constraints from left to right

The solution is a grid where 1 represents a filled cell (`#`) and 0 a blank cell (` `).

## Encoding

The Nonogram is encoded into CNF **manually**, without other libraries. All constraints are expanded directly into clauses.

### 1. Grid Variables

Each cell uses one Boolean variable:
- `x_r_c = True` -> cell (r,c) is `filled`
- `x_r_c = False` -> cell (r,c) is `empty`

Variables are numbered sequentially using `VarManager`:
- `get(name)` -> assigns integer IDs
- `count()` -> returns number of variables

---

### 2. Pattern Generation
For every row or column, all of the valid block placements are generated recursively.  
Each placement become a 0/1 pattern, then converted into a list of literals.

---

### 3. Selector-Based Encoding
Each placement gets a **selector variable**.  
We do:
- **At least one** placement:  
  `sel_1 v sel_2 v ... v sel_n`
- **At most one**:  
  pairwise (`-` is negation) `-sel_i v -sel_j`
- **Matching the pattern**:  
  for each literal `lit`: `-selector v lit`

Selectors here are auxiliary variables generated after all grid variables

---

### 4. Full CNF Generation
- Encode each row - its placements  
- Encode each column similarly as rows
- Both use the same `x_r_c` variables -> grid consistency is automatic

---

### 5. DIMACS and SAT Solver
The CNF is written to DIMACS format.  
An external SAT solver Glucose (version 4.2.1) is called.  
Positive `x_r_c` literals in the model reconstruct the final grid.

---

### 6. Input Validation
Invalid instances are rejected before CNF generation

---

## Example Instances

### Example 1: Simple 5x5 Nonogram

Input:

```json
{
  "cols": [[5], [1, 1], [1, 1], [1, 1], [5]],
  "rows": [[5], [1, 1], [1, 1], [1, 1], [5]]
}
```

Solution:

```
#####
#   #
#   #
#   #
##### 
```

### Example 2: Unsolvable nonogram

Input:

```json
{
  "cols": [[6], [1, 1], [1, 1], [1, 1], [6]],
  "rows": [[6], [1, 1], [1, 1], [1, 1], [6]]
}
```

Solution:

```
No solution 
```

---

## User Documentation

Basic usage:
```
python3 solver.py [-i INPUT] [-o OUTPUT] [-s SOLVER] [-v {0,1}]

# Example:
# python3 solver.py -i tests/5by5.json -o formula.cnf -s ./glucose_solver -v 0
```
Command-line options:

- `-i INPUT`, `--input INPUT`: Path to the JSON file describing the Nonogram (`rows` / `cols`).  
  Default: `"tests/5by5.json"`
- `-o OUTPUT`, `--output OUTPUT`: Output file for the DIMACS CNF formula.  
  Default: `"formula.cnf"`
- `-s SOLVER`, `--solver SOLVER`: External SAT solver executable (e.g., `./glucose_solver`)
- `-v {0,1}`, `--verb {0,1}`: Verbosity level of the SAT solver

The program:
1. Parses and validates the instance
2. Generates CNF encoding (row + column placements, selector variables)
3. Writes DIMACS output to output file
4. Calls the solver
5. Prints the reconstructed grid if SAT

---

## Experiments

All examples for testing are located in the `/tests` directory. These examples include both solvable and unsolvable puzzles of different complexity (i.e. size).

Here is the table of results from running the solver on various Nonogram puzzles:

| *Grid Size* | *Constraints Complexity* | *Encode Time (s)* | *Solve Time (s)* | *Solvable* |
|------------:|:-------------------------|:-----------------:|:----------------:|-----------:|
|        3x3  | Easy                     |      < 0.001      |      0.042       |        Yes |
|        3x3  | Easy                     |      < 0.001      |        -         |         No |
|        5x5  | Easy                     |      < 0.001      |      0.003       |        Yes |
|      15x15  | Medium                   |       0.039       |      0.205       |        Yes |
|      34x27  | Medium                   |       0.469       |      3.163       |        Yes |
|      38x39  | Hard                     |       62.12       |      30.563      |        Yes |
