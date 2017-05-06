assignments = []

# Sudoku constants
letters = 'ABCDEFGHI'
digits = '123456789'
rows = letters
cols = digits


def cross(A, B):
    """
    Cross product of elements in A and elements in B
    :param A: Iterable with overloaded +
    :param B: Iterable with overloaded +
    :return: Cross product iterable
    """
    return [a + b for a in A for b in B]


# Sudoku representation
boxes = cross(rows, cols)
row_units = [cross(r, cols) for r in rows]
col_units = [cross(rows, c) for c in cols]
square_units = [cross(row, col) for row in ('ABC', 'DEF', 'GHI') for col in ('123', '456', '789')]
diag_units = [[''.join(b) for b in zip(rows, cols)], [''.join(b) for b in zip(reversed(rows), cols)]]
diag_boxes = set(sum(diag_units, []))
unitlist = row_units + col_units + square_units + diag_units
units = dict((box, [unit for unit in unitlist if box in unit]) for box in boxes)
peers = dict((box, set(sum(units[box], []))-{box}) for box in boxes)


def sanity_check():
    """
    A collection of tests of the sudoku representation
    :return: None
    """
    assert(len(rows) == 9)
    assert(len(cols) == 9)
    assert(len(boxes) == 81)
    assert(len(row_units) == 9)
    assert(len(col_units) == 9)
    assert(len(square_units) == 9)

    # Diagonal sudoku
    assert(len(diag_units) == 2)
    assert(len(unitlist) == 29)
    assert(len(units['E5']) == 5)  # Center box has 5 units
    assert(all(len(units[box]) == 4 for box in boxes if box in diag_boxes - {'E5'}))
    assert(all(len(units[box]) == 3 for box in boxes if box not in diag_boxes))
    assert(len(peers['E5']) == 32)  # Center box has 26 peers
    assert(all(len(peers[box]) == 26 for box in boxes if box in diag_boxes - {'E5'}))
    assert(all(len(peers[box]) == 20 for box in boxes if box not in diag_boxes))


def assign_value(values, box, value):
    """
    Assigns a value to a given box. If it updates the board, records the assignment.
    :param values: A sudoku in dictionary form
    :param box: A sudoku box, e.g. 'A1'
    :param value: A box's allowable values, e.g. '8' for finalized, '123456789' for empty
    :return: The resulting sudoku
    """

    # Don't waste memory appending actions that don't actually change any values
    if values[box] == value:
        return values

    values[box] = value
    if len(value) == 1:
        assignments.append(values.copy())
    return values


def grid_values(grid):
    """
    Convert grid into a dict of {square: char} with '123456789' for empties.
    :param grid: A grid in string form
    :return: A grid in dictionary form
             Keys: The boxes, e.g., 'A1'
             Values: The value in each box, e.g., '8'. If the box has no value, then the value will be '123456789'.
    """
    assert(len(grid) == 81)
    assert(all(c in digits+'.' for c in grid))
    numbers = []
    for c in grid:
        if c == '.':
            numbers.append(digits)
        else:
            numbers.append(c)
    assert(len(numbers) == 81)
    return dict(zip(boxes, numbers))


def display(values):
    """
    Display the values as a 2-D grid.
    :param values: A sudoku in dictionary form
    :return: None
    """
    width = 1 + max(len(values[b]) for b in boxes)  # space between adjacent values
    separator = '+'.join(['-'*(width*3)]*3)
    for r in rows:
        print(''.join(values[r+c].center(width) + ('|' if c in '36' else '') for c in cols))
        if r in 'CF':
            print(separator)


def eliminate(values):
    """
    If a box has only one possible value, eliminate that value from the box's peers. 
    :param values: A sudoku in dictionary form.
    :return: The resulting sudoku
    """
    for box in [box for box in values.keys() if len(values[box]) == 1]:
        digit = values[box]
        for peer in peers[box]:
            values = assign_value(values, peer, values[peer].replace(digit, ''))
    return values


def only_choice(values):
    """
    If a unit has only one possible place for a value, then put the value there.
    :param values: A sudoku in dictionary form
    :return: The resulting sudoku
    """
    for unit in unitlist:
        for digit in digits:
            placements = [box for box in unit if digit in values[box]]
            if len(placements) == 1:
                values = assign_value(values, placements[0], digit)
    return values


def naked_twins(values):
    """
    Eliminate values using the naked twins strategy: in each unit, if there are two boxes 
    with the same two values, remove the values from all the peers the two boxes share.
    :param values: A sudoku in dictionary form  
    :return: The resulting sudoku
    """
    for unit in unitlist:
        twins = [(b1, b2) for b1 in unit for b2 in unit
                 if len(values[b1]) == len(values[b2]) == 2 and
                 values[b1] == values[b2] and
                 b1 < b2]  # remove duplicates
        for twin in twins:
            box1, box2 = twin
            # Note: Because we are eliminating in place, a pair other than the
            # first may have only one value remaining by the time of its turn.
            if len(values[box1]) < 2: continue
            val1, val2 = values[box1]
            for shared_peer in peers[box1] & peers[box2] - {box1} - {box2}:  # intersection, not union, of peers
                values = assign_value(values, shared_peer, values[shared_peer].replace(val1, '').replace(val2, ''))

    return values


def reduce_puzzle(values):
    """
    Iterates constraint propagation techniques. 
    If at some point there is a box with no available values, returns False.
    If the sudoku is solved, returns the sudoku.
    If after an iteration the sudoku remains the same, returns the sudoku.
    :param values: A sudoku in dictionary form
    :return: The resulting sudoku
    """
    reduced = False
    while not reduced:
        n_solved_before = len([box for box in values.keys() if len(values[box]) == 1])
        values = eliminate(values)
        values = only_choice(values)
        values = naked_twins(values)
        n_solved_after = len([box for box in values.keys() if len(values[box]) == 1])
        reduced = n_solved_after == n_solved_before
        if len([box for box in values.keys() if len(values[box]) == 0]):
            return False
    return values

def search(values):
    """
    Creates a tree of assignments and uses DFS to look for solutions.
    :param values: A sudoku in dictionary form
    :return: The resulting sudoku or False if no solution
    """
    values = reduce_puzzle(values)
    if values is False:
        return False  # No solution
    if all(len(values[b]) == 1 for b in boxes):
        return values  # Sudoku solved
    # Create branch: choose one of the unfilled squares with the fewest possibilities
    n, box = min((len(values[b]), b) for b in boxes if len(values[b]) > 1)
    # Assign branch and recurse with DPS
    for v in values[box]:
        new_values = values.copy()
        new_values[box] = v
        solved = search(new_values)
        if solved:
            return solved


def solve(grid):
    """
    Solve a sudoku
    :param grid: Sudoku in string form
    :return: Final sudoku in dictionary form or False if no solution
    """
    values = grid_values(grid)
    solved = search(values)
    if solved:
        return solved
    return False


if __name__ == '__main__':
    diag_sudoku_grid = '2.............62....1....7...6..8...3...9...7...6..4...4....8....52.............3'
    error_sudoku_1   = '1......2.....9.5...............8...4.........9..7123...........3....4.....936.4..'
    sanity_check()
    display(solve(diag_sudoku_grid))
    print('\n')
    display(solve(error_sudoku_1))  # The sudoku that caught the bug in naked_twins()

    # This is not working for some reason
    try:
        from visualize import visualize_assignments
        visualize_assignments(assignments)

    except SystemExit:
        pass
    except:
        print('We could not visualize your board due to a pygame issue. Not a problem! It is not a requirement.')
