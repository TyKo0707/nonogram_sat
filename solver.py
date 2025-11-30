#!/usr/bin/env python3
import subprocess
import json
import time
from argparse import ArgumentParser
import itertools


class VarManager:
    """
    Manages SAT variable numbering and naming
    """
    def __init__(self):
        self.next_var = 1
        self.map = {}

    def get(self, name):
        if name not in self.map:
            self.map[name] = self.next_var
            self.next_var += 1
        return self.map[name]

    def count(self):
        return self.next_var - 1


def generate_placements(blocks, length):
    """
    Generate all binary patterns of given length that satisfy the block pattern.
    Example: blocks=[2,1], length=7
    """
    results = []

    def rec(i, pos, arr):
        if i == len(blocks):
            results.append(arr[:])
            return

        b = blocks[i]
        for start in range(pos, length - b + 1):
            new_arr = arr[:]
            for j in range(start, start + b):
                new_arr[j] = 1
            rec(i + 1, start + b + 1, new_arr)

    rec(0, 0, [0] * length)
    return results


def new_aux_var():
    global AUX_COUNTER
    AUX_COUNTER += 1
    return AUX_COUNTER


def encode_exactly_one(placements, cnf):
    """
    placements is a list of literal-lists
    Encode exactly one single placement using selectors
    """
    selectors = [new_aux_var() for _ in placements]

    # At least one
    cnf.append(selectors[:])

    # Match pattern for each selector
    for sel, pattern in zip(selectors, placements):
        for lit in pattern:
            cnf.append([-sel, lit])

    # At most one
    for a, b in itertools.combinations(selectors, 2):
        cnf.append([-a, -b])


def encode_nonogram(rows, cols):
    """
    Given row/column constraints, build CNF and return tuple of (cnf, num_vars, var_map)
    """
    global AUX_COUNTER

    R = len(rows)
    C = len(cols)

    vm = VarManager()
    cnf = []

    # grid variables x_r_c
    def x(r, c):
        return vm.get(f"x_{r}_{c}")

    # start auxiliary vars AFTER all grid vars
    AUX_COUNTER = R * C

    # Encode rows
    for r, blocks in enumerate(rows):
        placements = generate_placements(blocks, C)

        pattern_literals = []
        for p in placements:
            lits = []
            for c, val in enumerate(p):
                v = x(r, c)
                lits.append(v if val == 1 else -v)
            pattern_literals.append(lits)

        encode_exactly_one(pattern_literals, cnf)

    # Encode cols
    for c, blocks in enumerate(cols):
        placements = generate_placements(blocks, R)

        pattern_literals = []
        for p in placements:
            lits = []
            for r, val in enumerate(p):
                v = x(r, c)
                lits.append(v if val == 1 else -v)
            pattern_literals.append(lits)

        encode_exactly_one(pattern_literals, cnf)

    return cnf, vm.count(), vm.map


def write_dimacs(cnf, nr_vars, filename):
    with open(filename, "w") as f:
        f.write(f"p cnf {nr_vars} {len(cnf)}\n")
        for clause in cnf:
            f.write(" ".join(str(l) for l in clause) + " 0\n")


def call_solver(solver, cnf_file, verb):
    return subprocess.run(
        [solver, "-model", f"-verb={verb}", cnf_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )


def decode_solution(model, var_map, R, C):
    reverse = {v: k for k, v in var_map.items()}

    grid = [[" " for _ in range(C)] for _ in range(R)]
    for lit in model:
        if lit > 0 and lit in reverse:
            name = reverse[lit]
            if name.startswith("x_"):
                _, r, c = name.split("_")
                grid[int(r)][int(c)] = "#"

    return grid


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-i", "--input", default="tests/5by5.json")
    parser.add_argument("-o", "--output", default="formula.cnf")
    parser.add_argument("-s", "--solver", default="./glucose")
    parser.add_argument("-v", "--verb", default=1, type=int)

    args = parser.parse_args()

    # Load instance
    with open(args.input) as f:
        spec = json.load(f)

    rows = spec["rows"]
    cols = spec["cols"]

    print("Encoding...")
    t0 = time.time()
    cnf, nr_vars, var_map = encode_nonogram(rows, cols)
    encode_time = time.time() - t0
    print(f"Generated CNF with {nr_vars} variables and {len(cnf)} clauses.")

    write_dimacs(cnf, nr_vars, args.output)
    print(f"CNF written to {args.output}")

    print("Solving...")
    t1 = time.time()
    result = call_solver(args.solver, args.output, args.verb)
    solve_time = time.time() - t1

    print(result.stdout)

    if "UNSAT" in result.stdout:
        print("No solution.")
        print(f"Encode time: {encode_time:.3f}s")
        exit(0)

    # parse model
    model = []
    for line in result.stdout.splitlines():
        if line.startswith("v"):
            for x in line.split()[1:]:
                if x != "0":
                    model.append(int(x))

    grid = decode_solution(model, var_map, len(rows), len(cols))
    print("Solution:")
    for row in grid:
        print("".join(row))

    print(f"Encode time: {encode_time:.3f}s")
    print(f"Solve time: {solve_time:.3f}s")
