import itertools, random, time
from itertools import product
from words import WORDS

from colorama import Fore, init
init(autoreset=True)

from bauhaus import Encoding, proposition, constraint, Or, And
from bauhaus.utils import count_solutions, likelihood

# These two lines make sure a faster SAT solver is used.
from nnf import config

config.sat_backend = "kissat"

# Encoding that will store all of your constraints

#global vars 
E = Encoding()
ALPHABET = "abcdefghijklmnopqrstuvwxyz"
# Pick a random word from words.py and split it into a list of characters
SOL = list(WORDS[random.randint(0, len(WORDS)-1)])
# Generate a list of all the characters not used in the solution
NOTSOL = [letter for letter in ALPHABET if letter not in SOL]
# Give a valid colour layout to the SAT solver
BOARD = [
    ["White", "Green", "Yellow", "White", "White"],
    ["Yellow", "Green", "White", "White", "White"],
    ["White", "Green", "White", "Yellow", "White"],
    ["Green", "Green", "Green", "Green", "Green"],
]
valid_tiles = [[set(),set(),set(),set(),set()],[set(),set(),set(),set(),set()],[set(),set(),set(),set(),set()], [set(), set(), set(), set(), set()]]
valid_rows = [set(), set(), set(), set()]
valid_boards = set()


class Hashable:
    def __hash__(self):
        return hash(str(self))

    def __eq__(self, __value: object) -> bool:
        return hash(self) == hash(__value)

    def __repr__(self):
        return str(self)


# Different classes for propositions are useful because this allows for more dynamic constraint creation
# for propositions within that class. For example, you can enforce that "at least one" of the propositions
# that are instances of this class must be true by using a @constraint decorator.
# other options include: at most one, exactly one, at most k, and implies all.
# For a complete module reference, see https://bauhaus.readthedocs.io/en/latest/bauhaus.html

# Proposition for a Tile, holds row, column index, colour and letter
@proposition(E)
class Tile(Hashable):
    def __init__(self, x_index, y_index, colour, letter) -> None:
        self.x_index = x_index
        self.y_index = y_index
        self.colour = colour
        self.letter = letter

    def __str__(self) -> str:
        return f"({self.colour} {self.letter} at {self.x_index}, {self.y_index})"

# Proposition for a Row, holds row number (0-3) and the 5 tiles it contains
@proposition(E)
class Row(Hashable):
    def __init__(
        self, row_number, letterZero, letterOne, letterTwo, letterThree, letterFour
    ) -> None:
        self.row_number = row_number
        self.letterZero = letterZero
        self.letterOne = letterOne
        self.letterTwo = letterTwo
        self.letterThree = letterThree
        self.letterFour = letterFour

    def __str__(self) -> str:
        return f"Row {self.row_number} contains [{self.letterZero},{self.letterOne},{self.letterTwo},{self.letterThree},{self.letterFour}]"

# Proposition for a Board, holds the 4 rows it contains
@proposition(E)
class Board(Hashable):
    def __init__(self, row1, row2, row3, row4) -> None:
        self.row1 = row1
        self.row2 = row2
        self.row3 = row3
        self.row4 = row4

    def __str__(self) -> str:
        return f"{self.row1} \n {self.row2} \n {self.row3} \n {self.row4}"

    
def build_theory():
    
    # Iterate through every tile on the board and every letter in the final word
    for r, col in itertools.product(range(3,-1,-1), range(5)):
        for letter in SOL:
            # If the tile must be green, add a constraint that the Tile at that index must be a Green tile
            # with the letter from that column of the final word
            if BOARD[r][col] == "Green": 
                E.add_constraint(Tile(r,col,"Green",SOL[col]))
                # If the tile is not already in the valid tile array, add it
                valid_tiles[r][col].add(Tile(r,col,"Green",SOL[col]))
            # If the tile must be yellow, 
            if BOARD[r][col] == "Yellow": 
                E.add_constraint(~(Tile(r,col,"Yellow",SOL[col])))  
            if BOARD[r][col] == "Yellow" and letter != SOL[col]:
                    E.add_constraint(Tile(r,col,"Yellow",letter))
                    # If the tile is not already in the valid tile array, add it
                    valid_tiles[r][col].add(Tile(r,col,"Yellow",letter))
        for letter in NOTSOL: 
            # The letter at any index cannot be a Green or Yellow tile
            E.add_constraint(~(Tile(r,col,"Green",letter)))
            E.add_constraint(~(Tile(r,col,"Yellow",letter)))
            # If the index must be White, then any letter not in the solution 
            # is a valid tile at that index
            if BOARD[r][col] == "White":
                E.add_constraint(Tile(r,col,"White",letter))
                # If the tile is not already in the valid tiles array, add it
                valid_tiles[r][col].add(Tile(r,col,"White",letter))

    #For every valid tile that we gathered
    for row in range(4):
        for let1 in valid_tiles[row][0]:
            for let2 in valid_tiles[row][1]:
                for let3 in valid_tiles[row][2]:
                    for let4 in valid_tiles[row][3]:
                        for let5 in valid_tiles[row][4]:
                            # If the letters of all 5 tiles are in the word list
                            # Add a constraint that all the letters and the row of the letters must be true
                            # Add the row to the list of valid rows at the row index
                            pot_word = let1.letter + let2.letter + let3.letter + let4.letter + let5.letter
                            if pot_word in WORDS:
                                E.add_constraint((
                                    (let1 & let2 & let3 & let4 & let5) >> Row(row, let1, let2, let3, let4, let5)
                                ))
                                # If the row is not already in the valid rows array, add it
                                valid_rows[row].add(Row(row, let1, let2, let3, let4, let5))

    # Generate combinations of valid_rows
    for rows_combination in product(*valid_rows):
        # Unpack the combinations for each row
        row1, row2, row3, row4 = rows_combination

        # Add a constraint for the combination of rows and the board
        E.add_constraint(((row1 & row2 & row3 & row4) >> Board(row1, row2, row3, row4)))

        # Add the board to valid_boards set
        valid_boards.add(Board(row1, row2, row3, row4)) 

    return E

def display_board(BOARD):
    # For each row in the board
    row_iter = [BOARD.row1, BOARD.row2, BOARD.row3, BOARD.row4]
    for row in row_iter:
        # Print the letters of each row in the board separated by a space
        letter_iter = [row.letterZero.letter, row.letterOne.letter, row.letterTwo.letter, row.letterThree.letter, row.letterFour.letter]
        colour_iter = [row.letterZero.colour.upper(), row.letterOne.colour.upper(), row.letterTwo.colour.upper(), row.letterThree.colour.upper(), row.letterFour.colour.upper()]
        for i in range(len(letter_iter)):
            if colour_iter[i] == "GREEN":
                print(f'{Fore.GREEN}{letter_iter[i]} ', end="")
            elif colour_iter[i] == "YELLOW":
                print(f'{Fore.YELLOW}{letter_iter[i]} ', end="")
            else:
                print(f'{Fore.WHITE}{letter_iter[i]} ', end="")
        print('\n', end="")

def display_solutions(sol):
    num_sol = len(sol)
    # If there are 0 board solutions, we cannot display a board
    print("Board Solutions: %d" % num_sol)
    if num_sol == 0:
        print('No valid boards to display.')
    else: 
        # If there are board solutions, pick a random one and display it
        print('Possible solution:')
        display_board(sol[random.randint(0, len(sol)-1)])

if __name__ == "__main__":
    start = time.time()
    print(f"The final word is: {''.join(SOL)}")
    if len(SOL) > 5: 
        raise Exception("Final word is greater than 5.")
    T = build_theory()
    T = T.compile()
    print(f"Satisfiable: {T.satisfiable()}")
    sol = T.solve()
    # Only pass in unique Board solutions
    board_sol = []
    [board_sol.append(item) for item in sol if hasattr(item, "row1")]
    display_solutions(board_sol)
    end = time.time()
    elapsed = round(end-start, 2)
    print(f'Compile time of {elapsed} seconds.\n')

# Board with 1190 solutions and length 1000 word list takes ~1m30s
# Board with 480 solutions and length 1000 word list takes ~20s
# Board with 816 solutions and length 2000 word list takes ~20s
# Board with 1300 solutions and length 2000 word list takes ~50s
# Board with 336 solutions and length 3834 word list takes ~1m20s
# Board with 2392 solutions and length 2000 word list takes ~5m15s


# To make our constraints simpler, we decided that hints do not have to be reused
# e.g. a Yellow Y in the first row does not constrain that a Y must be included in the second row.
# We also decided that white letters can be reused across the board
# e.g. a White K is guessed in the first row does not constrain that it cannot be guessed in the second row

# Maximum length word list (3834) and a board with many solutions (>1000) takes too long to compute
# Limit the word list, right now it's at 2000 words and has a reasonable runtime

# One of the major hurdles we overcame was runtime. When keeping track of valid tiles, rows, and boards, lots 
# of duplicate propositions and constraints were being generated. To fix this issue, and massively 
# optimize our project, we checked if a proposition was not already in the list before adding it.
# At first, a board and word that resulted in single-digit solutions would get 'Killed' by the docker container.
# After implementing these changes, it would compile in seconds. Even a board and word that resulted in 
# over a thousand solutions took less than a minute to compile.

# We were still not satisfied with the time it took to to compile, so we changed all of the inner
# valid lists to sets, which made the contains check redundant. This removed thousands of 
# comparisons which optimized our code even further.

# Board with 8700 solutions and length 2000 word list takes ~15s
# Board with 20700 solutions and length 2000 word list takes ~25s

# After these optimizations, we decided to extend our word list to the full 3834 words. 

# Board with 6630 solutions and length 3834 word list takes ~20s
# Board with 38686 solutions and length 3834 word list takes ~50s
# Board with 83600 solutions and length 3834 word list takes ~1m30s

# Used python time library to keep track of elapsed time in seconds.
# Print elapsed time at the end to see how long it took.