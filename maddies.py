from words import WORDS
COLOURS = ['Green', 'White', 'Yellow']
import pprint

from bauhaus import Encoding, proposition, constraint, Or, And
from bauhaus.utils import count_solutions, likelihood

# These two lines make sure a faster SAT solver is used.
from nnf import config

config.sat_backend = "kissat"

# Encoding that will store all of your constraints
E = Encoding()
ALPHABET = "abcdefghijklmnopqrstuvwxyz"
SOL = ['f','o','u','n','d']
NOTSOL = ['a','b','c','e','g','h','i','j','k','l','m','p','q','r','s','t','v','w','x','y','z']
BOARD = [
    ["White", "White", "White", "Yellow", "White"],
    ["White", "White", "White", "White", "Yellow"],
    ["Yellow", "White", "Yellow", "Green", "White"],
    ["Greenf", "Greeno", "Greenu", "Greenn", "Greend"],
]
row_solutions = [[],[],[]]
print("got here1")


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


@proposition(E)
class Tile(Hashable):
    def __init__(self, x_index, y_index, colour, letter) -> None:
        self.x_index = x_index
        self.y_index = y_index
        self.colour = colour
        self.letter = letter

    def __str__(self) -> str:
        return f"({self.colour} {self.letter} at {self.x_index}, {self.y_index})"
    
@proposition(E)
class Word(Hashable):
    def __init__(self, word) -> None:
        self.word = word

    def __str__(self) -> str:
        return f"({self.word})"


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


@proposition(E)
class Board(Hashable):
    def __init__(self, row1, row2, row3, row4) -> None:
        self.row1 = row1
        self.row2 = row2
        self.row3 = row3
        self.row4 = row4

    def __str__(self) -> str:
        return f"{self.row1} \n {self.row2} \n {self.row3} \n {self.row4}"

possible_tiles = {0: [],
                  1: [],
                  2: [],
                  3: []}

for i in range(5):
    possible_tiles[3].append(Tile(3, i, BOARD[3][i][:-1], BOARD[3][i][-1:]))
for a in ALPHABET:
    for i in range(3):
        for j in range(5):
            possible_tiles[i].append(Tile(i, j, BOARD[i][j], a))

bottom_row = Row(3, possible_tiles[3][0], possible_tiles[3][1], possible_tiles[3][2], possible_tiles[3][3], possible_tiles[3][4])

for word in WORDS:
    for row in range(2,-1,-1): 
        Row(row,word[0],word[1],word[2],word[3],word[4])

for i in range(5): 
    Tile(3,i,"Green",SOL[i])

    
def build_theory():
    print("got here2")

    # for r in range(3,-1,-1): 
    #     for col in range(5):
    #         for letter1 in NOTSOL: 
    #             for letter2 in NOTSOL:
    #                 if letter1 != letter2: 
    #                     E.add_constraint((Tile(r,col,BOARD[r][col],letter1)) | (Tile(r,col,BOARD[r][col],letter2)))

    for r in range(3,-1,-1): 
        for col in range(5):
            for letter in SOL:
                if BOARD[r][col] == "Green": 
                    E.add_constraint(Tile(r,col,"Green",SOL[col]))
                if BOARD[r][col] == "Yellow": 
                    E.add_constraint(~(Tile(r,col,"Yellow",SOL[col])))

    for r in range(3,-1,-1): 
        for col in range(5):
            for letter in SOL:
                if BOARD[r][col] == "Yellow": 
                    if letter != SOL[col]:
                        E.add_constraint(Tile(r,col,"Yellow",letter))

    for r in range(3,-1,-1): 
        for col in range(5):
            for letter in NOTSOL: 
                if BOARD[r][col] == "Green": 
                    E.add_constraint(~(Tile(r,col,"Green",letter)))
                if BOARD[r][col] == "Yellow": 
                    E.add_constraint(~(Tile(r,col,"Yellow",letter)))
                else: 
                    E.add_constraint(Tile(r,col,"White",letter))

    # for r in range(3,-1,-1): 
    #     for col in range(5):
    #         for letter1 in NOTSOL: 
    #             for letter2 in NOTSOL:
    #                 if letter1 != letter2: 
    #                     E.add_constraint((Tile(r,col,BOARD[r][col],letter1)) | (Tile(r,col,BOARD[r][col],letter2)))
 
                        
    return E

def display_board(board):
    for row in board:
        print(row)

def display_solutions(sol):
    pprint.pprint(sol)

if __name__ == "__main__":
    T = build_theory()
    print("got here3")

    # # Don't compile until you're finished adding all your constraints!
    T = T.compile()
    # After compilation (and only after), you can check some of the properties
    # of your model:
    print("got here4")
    print("\nSatisfiable: %s" % T.satisfiable())
    print("# Solutions: %d" % count_solutions(T))
    sol = T.solve()
    display_solutions(sol)

    # print("\nVariable likelihoods:")
    # for v,vn in zip([a,b,c,x,y,z], 'abcxyz'):
    #     # Ensure that you only send these functions NNF formulas
    #     # Literals are compiled to NNF here
    #     print(" %s: %.2f" % (vn, likelihood(T, v)))
    # print()
    display_board(BOARD)