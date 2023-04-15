from dataclasses import dataclass, field
from uuid import uuid4
from random import shuffle
import copy

import sys
from PyQt5 import uic
from termcolor import colored
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QGridLayout, QLineEdit, QWidget, QAction
import logging

"""
Goals:
1# generates sudoku puzzle that has only one way to complete it.

SUDOKU rules:
Rule 1 - Each row must contain the numbers from 1 to 9, without repetitions.
Rule 2 - Each column must contain the numbers from 1 to 9, without repetitions.
Rule 3 - The digits can only occur once per block (nonet).
Rule 4 - The sum of every single row, column and nonet must equal 45.

# A regular 9 x 9 grid is divided into 9 smaller blocks of 3 x 3, also known as nonets. The numbers from 1 to 9 can only occur once per nonet.

# coordinates for puzzle. Cell in the puzzle are kept as str.

      0   1   2   3   4   5   6   7   8
    ╔═══╤═══╤═══╦═══╤═══╤═══╦═══╤═══╤═══╗
 0  ║   │   │   ║   │   │   ║   │   │   ║
    ╟───┼───┼───╫───┼───┼───╫───┼───┼───╢
 1  ║   │   │   ║   │   │   ║   │   │   ║
    ╟───┼───┼───╫───┼───┼───╫───┼───┼───╢
 2  ║   │   │   ║   │   │   ║   │   │   ║
    ╠═══╪═══╪═══╬═══╪═══╪═══╬═══╪═══╪═══╣
 3  ║   │   │   ║   │   │   ║   │   │   ║
    ╟───┼───┼───╫───┼───┼───╫───┼───┼───╢
 4  ║   │   │   ║   │   │   ║   │   │   ║
    ╟───┼───┼───╫───┼───┼───╫───┼───┼───╢
 5  ║   │   │   ║   │   │   ║   │   │   ║
    ╠═══╪═══╪═══╬═══╪═══╪═══╬═══╪═══╪═══╣
 6  ║   │   │   ║   │   │   ║   │   │   ║
    ╟───┼───┼───╫───┼───┼───╫───┼───┼───╢
 7  ║   │   │   ║   │   │   ║   │   │   ║
    ╟───┼───┼───╫───┼───┼───╫───┼───┼───╢
 8  ║   │   │   ║   │   │   ║   │   │   ║
    ╚═══╧═══╧═══╩═══╧═══╧═══╩═══╧═══╧═══╝

"""


@dataclass
class SUDOKU:
    ID: int = uuid4().int  # generates random ID
    Puzzle: list = field(init=False)  # contains current state of the puzzle
    orig_puzzle: list = field(init=False)  # contains original start of the puzzle
    locked_coordinates: list = field(init=False)  # contains locked coordinates of the puzzle where number cannot be placed
    search_path = []
    solution = []  # contains solution for the sudoku
    debug = False
    counter = 0  # solutions counter

    def __post_init__(self):
        self.generate()

    def generate(self):
        """generates new puzzle"""
        new_puzzle = self._generate_puzzle()
        self.Puzzle = new_puzzle  # user adds his numbers to this variable
        self.orig_puzzle = new_puzzle.copy()  # this will house original starting point

        self._find_locket_coordinates()

    # ---------------------------
    # Debug
    # ---------------------------

    def debugger(self, msg, grid, show_grid=True):
        """gives debug message if enabled"""
        if self.debug:
            print(msg)

            if show_grid:
                for row in grid:
                    print(row)

                print('---------------------------------------------')

    # ---------------------------
    # Puzzle
    # ---------------------------

    def _generate_puzzle(self) -> list[list]:
        """generates 9 x 9 grid sudoku puzzle"""

        # generate simple grip
        grid = [[0 for i in range(9)] for j in range(9)]

        # generate solution for sudoku
        self._generate_solution(grid)

        # translate solution to nested list
        ready_puzzle = self.form_sudoku()
        self.solution = copy.deepcopy(ready_puzzle)

        # reduce numbers from ready sudoku to finalize puzzle
        puzzle = self._remove_numbers_from_grid(ready_puzzle)

        return puzzle

    def _generate_solution(self, grid):
        """generates a full solution with backtracking"""

        number_list = [1, 2, 3, 4, 5, 6, 7, 8, 9]

        # go through all rows
        for i in range(0, 81):
            # make coordinates
            row = i // 9
            col = i % 9

            # find next empty cell
            if grid[row][col] == 0:
                shuffle(number_list)  # shuffle numbers list, if not shuffled same solution would be generated always

                # try fit numbers recursively
                for number in number_list:

                    self.debugger(f'Validating location... {row=}, {col=}', grid)

                    # if valid location in the grid for the number
                    if self.valid_location(grid, row, col, number):

                        self.search_path.append((number, row, col))
                        grid[row][col] = number

                        if not self.find_empty_square(grid):
                            return True
                        else:
                            if self._generate_solution(grid):
                                # if the grid is full
                                return True
                break
        grid[row][col] = 0
        return False

    def _remove_numbers_from_grid(self, grid):
        """remove numbers from the grid to create the puzzle"""

        # get all non-empty squares from the grid
        non_empty_squares = [(row_num, col_num) for row_num, row_data in enumerate(grid) for col_num, num in enumerate(row_data) if num != 0]
        shuffle(non_empty_squares)

        non_empty_squares_count = len(non_empty_squares)
        rounds = 3

        while rounds > 0 and non_empty_squares_count >= 17:

            # there should be at least 17 clues
            row, col = non_empty_squares.pop()
            non_empty_squares_count -= 1

            # might need to put the square value back if there is more than one solution
            removed_square = grid[row][col]
            grid[row][col] = 0

            # make a copy of the grid to solve
            grid_copy = copy.deepcopy(grid)

            # return number of solution for sudoku puzzle
            self.counter = 0
            self.solve_puzzle(grid_copy)

            # if there is more than one solution, put the last removed cell back into the grid
            if self.counter != 1:
                grid[row][col] = removed_square
                non_empty_squares_count += 1
                rounds -= 1

        return grid

    def solve_puzzle(self, grid) -> int:
        """solves puzzle and returns number of possible solutions"""
        for i in range(0, 81):
            row = i // 9
            col = i % 9

            # find next empty cell
            if grid[row][col] == 0:
                for number in range(1, 10):

                    # check that the number hasn't been used in the row/col/subgrid
                    if self.valid_location(grid, row, col, number):
                        grid[row][col] = number

                        if not self.find_empty_square(grid):
                            self.counter += 1
                            break
                        else:
                            if self.solve_puzzle(grid):
                                return True
                break
        grid[row][col] = 0
        return False

    @staticmethod
    def find_empty_square(grid: list[list]):
        """if there is empty cell in grid"""

        for row in grid:
            if 0 in row:
                return True

        return False

    def valid_location(self, grid: list[list], row: int, col: int, number: int) -> bool:
        """verify if number can be put to grid in row, col location"""
        tests = [self._verify_row, self._verify_column, self._verify_nonet]

        for test in tests:
            status = test(grid, row, col, number)

            if status != 0:
                status_code: dict = {
                    -1: 'Does not equal to 45',
                    -2: 'Duplicate values',
                }

                self.debugger(f'Not valid location, test = {test}, status = {status_code[status]}', grid)
                return False  # if even one fails return False

        self.debugger(f'Valid location', grid)
        return True  # if all tests are passed return True

    def _find_locket_coordinates(self):
        """finds locked coordinates from the puzzle"""
        locked_coordinates = []

        # go through all rows
        for i in range(0, 81):
            # make coordinates
            row = i // 9
            col = i % 9

            number = self.orig_puzzle[row][col]

            if number != 0:
                locked_coordinates.append((row, col))

        self.locked_coordinates = locked_coordinates

    def form_sudoku(self) -> list[list]:
        """makes 9x9 sudoku from self.search_path"""
        n = 9
        m = 9

        sudoku = [[0 for i in range(n)] for j in range(m)]
        for coord in self.search_path:
            num, row, col = coord
            sudoku[row][col] = num

        return sudoku

    def validate_sudoku(self, grid: list[list]) -> bool:
        """validates full sudoku puzzle"""

        # go through all rows
        for i in range(0, 81):
            # make coordinates
            row = i // 9
            col = i % 9

            number = grid[row][col]

            if not self.valid_location(grid, row, col, number):
                return False

        return True

    # ---------------------------
    # Verify
    # ---------------------------

    @staticmethod
    def _verify_nonet(grid: list[list], x: int, y: int, num: int) -> int:
        """checks that nonet doesn't have repeating numbers and if full sums exactly to 45"""

        # add number to be tested to grid
        grid[x][y] = num

        x_nonets = [(0, 1, 2), (3, 4, 5), (6, 7, 8)]
        y_nonets = [(0, 1, 2), (3, 4, 5), (6, 7, 8)]

        # check what x nonet is used
        x_verify: tuple = ()
        for x_nonet in x_nonets:
            if x in x_nonet:
                x_verify = x_nonet
                break

        # check what y nonet is used
        y_verify: tuple = ()
        for y_nonet in y_nonets:
            if y in y_nonet:
                y_verify = y_nonet
                break

        # find values in given nonet
        nonet_values: list = []
        for x_ in x_verify:
            for y_ in y_verify:
                nonet_values.append(grid[x_][y_])

        # check that list doesn't have repeating values. Ignore 0 values
        found: list = []
        for value in nonet_values:
            if 0 == value:
                continue

            # check for duplicates, if duplicate return False
            if value not in found:
                found.append(value)
            else:
                return -2

        return 0

    @staticmethod
    def _verify_column(grid: list[list], x: int, y: int, num: int) -> int:
        """checks that column doesn't have repeating numbers and if full sums exactly to 45"""

        # add number to be tested to grid
        grid[x][y] = num

        # gets number from row if it's in the same column as the inputted positional arguments.
        column = [nums for row in grid for i, nums in enumerate(row) if i == y]

        # check that list doesn't have repeating values. Ignore 0 values
        found: list = []
        for value in column:
            if 0 == value:
                continue

            # check for duplicates, if duplicate return False
            if value not in found:
                found.append(value)
            else:
                return -2

        return 0

    @staticmethod
    def _verify_row(grid: list[list], x: int, y: int, num: int) -> int:
        """checks that row doesn't have repeating numbers and if full sums exactly to 45"""

        # add number to be tested to grid
        grid[x][y] = num

        # gets number from row if it's in the same row as the inputted positional arguments.
        row = grid[x]

        # check that list doesn't have repeating values. Ignore 0 values
        found: list = []
        for value in row:
            if 0 == value:
                continue

            # check for duplicates, if duplicate return False
            if value not in found:
                found.append(value)
            else:
                return -2

        return 0

    # ---------------------------
    # Place
    # ---------------------------

    def place_number(self, y: int, x: int, num: int) -> bool:
        """
        add number to grid if it fits
        """

        # return if number is not in limits
        if not 0 <= num <= 9:
            print(f'> Number {num} was not in allowed limits')
            return False

        # return if coordinates not in limits
        for coord in [y, x]:
            if not 0 <= coord <= 8:
                print(f'> Coordinate Number {coord} was not in allowed limits')
                return False

        # check if coordinates are not locked
        if (y, x) in self.locked_coordinates:
            print('> Cannot place number to locked coordinates!')
            return False

        self.Puzzle[y][x] = num
        return True

    # ---------------------------
    # present
    # ---------------------------

    def present(self, grid: list):
        """present sudoku in grid"""

        str_grid = "\t  0   1   2   3   4   5   6   7   8\n\t╔═══╤═══╤═══╦═══╤═══╤═══╦═══╤═══╤═══╗\n"

        separator = '\t╟───┼───┼───╫───┼───┼───╫───┼───┼───╢\n'

        for i, y in enumerate(grid):

            str_grid += f'{i}   ║'  # starting separator

            for ii, x in enumerate(y):
                number = x

                # add large or small separator for numbers
                if ii in [3, 6]:
                    str_grid += '║'
                elif ii == 0:
                    pass
                else:
                    str_grid += '│'

                if number != 0:
                    if (i, ii) in self.locked_coordinates:
                        str_grid += colored(f' {number} ', 'red')  # add number
                    else:
                        str_grid += f' {number} '  # add number
                else:
                    str_grid += f'   '  # add empty space

            str_grid += '║\n'  # closing separator

            if i != 8:
                str_grid += separator

        str_grid += '\t╚═══╧═══╧═══╩═══╧═══╧═══╩═══╧═══╧═══╝\n'  # bottom of the grid

        print(str_grid)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('Sudoku_main.ui', self)  # Load the .ui file
        self.cells = []
        self.find_widget_cells()  # collects all QLineEdit cells to self.cells variable
        self.sudoku = SUDOKU()
        self.populate_cells()

        # hide this info label by default
        self.label_info: QLabel
        self.label_info.hide()

        # auto solve puzzle
        self.actionAuto_solve: QAction
        self.actionAuto_solve.triggered.connect(self.auto_solve)

        # new game
        self.actionNew_game: QAction
        self.actionNew_game.triggered.connect(self.new_game)

        # validate puzzle
        self.pushButton_validate: QPushButton
        self.pushButton_validate.clicked.connect(self.update_validate_puzzle)

        self.show()

    @staticmethod
    def layout_widgets(layout) -> list[QWidget] or None:
        """returns all widget in layout"""
        return (layout.itemAt(i).widget() for i in range(layout.count()))

    def find_widget_cells(self):
        """finds all widget cells"""
        self.gridLayout_cells: QGridLayout
        layout = self.gridLayout_cells
        widgets = self.layout_widgets(layout)

        cells = []
        # find all cells
        if widgets is not None:
            for w in widgets:
                if isinstance(w, QLineEdit):
                    cells.append(w)
        else:
            logging.error('None of the cells found!')

        self.cells = cells

    def populate_cells(self):
        """populates all cells at the start of the game"""
        puzzle = self.sudoku.Puzzle
        cells = self.cells

        # reset cells
        for widget in cells:
            widget.setReadOnly(False)
            widget.setStyleSheet("color: black; font-weight: light;")
            widget.setText('')

        # populate cells with starting numbers
        for i, row in enumerate(puzzle):
            # print(row)  # debug - print out all rows
            for ii, cell in enumerate(row):
                # if cell is zero don't add number
                if cell != 0:
                    # find correct cell widget
                    for widget in cells:
                        # if object name matches the index of the cell add number to it
                        if widget.objectName() == f'lineEdit_{i}_{ii}':
                            widget.setStyleSheet("color: black; font-weight: bold;")
                            widget.setText(str(cell))
                            widget.setReadOnly(True)  # set to read only since user cannot edit it

    def update_validate_puzzle(self):
        """adds number to sudoku.Puzzle and validates it"""
        cells = self.cells
        grid = self.sudoku.Puzzle
        self.label_info: QLabel

        for widget in cells:
            widget: QLineEdit

            number = widget.text()  # get widget number

            # skip empty widget cells
            if number == '':
                continue

            # get coordinates from widget object name
            coord = widget.objectName().split('_')
            row = int(coord[-2])
            col = int(coord[-1])

            # add number to grid
            number = int(number)
            grid[row][col] = number

        # check if sudoku is valid
        if self.sudoku.validate_sudoku(grid):
            msg = 'Sudoku is valid'
        else:
            msg = 'Sudoku is not valid'

        self.info_text(msg, 3000)

    def info_text(self, msg: str, timer: int):
        """shows info text for msec of the timer value"""
        self.label_info.show()
        self.label_info.setText(msg)
        QTimer.singleShot(timer, self.label_info.hide)

    def auto_solve(self):
        """auto solves the grid"""
        self.sudoku.Puzzle = self.sudoku.solution
        grid = self.sudoku.Puzzle
        cells = self.cells

        # populate cells with starting numbers
        for i, row in enumerate(grid):
            # print(row)  # debug - print out all rows
            for ii, cell in enumerate(row):
                # find correct cell widget
                for widget in cells:
                    widget: QLineEdit

                    # skip locked coordinates
                    if (i, ii) in self.sudoku.locked_coordinates:
                        continue

                    # if object name matches the index of the cell add number to it
                    if widget.objectName() == f'lineEdit_{i}_{ii}':

                        # if cell contains number already, and it's correct bold it mark is as green
                        if widget.text() != '' and cell == int(widget.text()):
                            widget.setStyleSheet("color: green; font-weight: bold;")
                        else:
                            widget.setStyleSheet("color: red; font-weight: bold;")
                            widget.setText(str(cell))

                        widget.setReadOnly(True)  # set cell to non-editable after auto solve has been used

    def new_game(self):
        """starts new game"""
        self.sudoku.generate()
        self.populate_cells()
        self.info_text('New game started!', 3000)


if __name__ == '__main__':

    # depending on the application preference the app is launched as terminal or PyQt5 applications
    application_preference = True

    if application_preference:
        # PyQt5 applications
        app = QApplication(sys.argv)
        window = MainWindow()
        app.exec_()
    else:
        # terminal applications
        print('---------------------------------------------')
        print('<<<                SUDOKU                 >>>')
        print('---------------------------------------------')

        new = True
        sudoku = SUDOKU()

        while True:

            # create new puzzle
            if new:
                sudoku.generate()
                new = False

            sudoku.present(sudoku.Puzzle)

            print('> To add number use "row, col, number"')
            print('> To validate the sudoku type: "validate"')
            print('> To generate new sudoku type: "new"')
            numbers: str = input('< ').strip()

            # stop the game
            if numbers.lower() in ['exit', 'close']:
                break

            # make new game
            if numbers.lower() == 'new':
                new = True
                continue

            # validates current sudoku
            if numbers.lower() == 'validate':
                if sudoku.validate_sudoku(sudoku.Puzzle):
                    print('> Sudoku is valid')
                else:
                    print('> Sudoku is not valid')
                continue

            # auto solves puzzle
            if numbers.lower() == 'solve':
                sudoku.Puzzle = sudoku.solution
                continue

            numbers: list = numbers.split(',')

            # if correct amount of numbers
            if len(numbers) == 3:
                nums = []
                for num_ in numbers:
                    num_: str

                    try:
                        nums.append(int(num_.strip()))
                    except ValueError:
                        print('> Only use numbers, space and comma separator!!')
                        break

                if len(nums) == 3:
                    sudoku.place_number(y=nums[0], x=nums[1], num=nums[2])
