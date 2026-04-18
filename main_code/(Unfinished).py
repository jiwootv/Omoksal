import Gomoku_Board
import json

FILE_NAME = "Result1.json"

SIZE = 15


board_data = [[0 for _ in range(SIZE)] for __ in range(SIZE)]
print(board_data)
w1 = Gomoku_Board.GomokuBoard(board_data)
b1 = Gomoku_Board.GomokuBoard(board_data)
print(w1.where_should_i_place())

def w1_place():
	w1.edit_board(w1.where_should_i_place()['x'], w1.where_should_i_place()['y'], 2)
	b1.edit_board(w1.where_should_i_place()['x'], w1.where_should_i_place()['y'], 2)
	board_data[w1.where_should_i_place()['x']][w1.where_should_i_place()['y']] = 2
	return check_win(w1.where_should_i_place()['x'], w1.where_should_i_place()['y'], 2)
def b1_place():
	w1.edit_board(b1.where_should_i_place()['x'], b1.where_should_i_place()['y'], 1)
	b1.edit_board(b1.where_should_i_place()['x'], b1.where_should_i_place()['y'], 1)
	board_data[b1.where_should_i_place()['x']][b1.where_should_i_place()['y']] = 1
	return check_win(b1.where_should_i_place()['x'], b1.where_should_i_place()['y'], 1)

def count_dir(x, y, dx, dy, stone):
	count = 0
	nx = x + dx
	ny = y + dy

	while 0 <= nx < SIZE and 0 <= ny < SIZE and board_data[ny][nx] == stone:
		count += 1
		nx += dx
		ny += dy

	return count

def check_win(x, y, stone):
	directions = [
		(1, 0),   # 가로
		(0, 1),   # 세로
		(1, 1),   # 대각 \
		(1, -1)   # 대각 /
	]

	for dx, dy in directions:
		count = 1
		count += count_dir(x, y, dx, dy, stone)
		count += count_dir(x, y, -dx, -dy, stone)

		if count >= 5:
			print(f"WIN of {["_NULL_", "black", "white"][stone]}: {count}")
			print(f"direction: {dx}, {dy} / count: {count}")
			print(f"pos: [{x}, {y}]")
			return True

	return False

it_will_break = False
while True:
	it_will_break = w1_place()
	if not it_will_break: it_will_break = b1_place()
	if it_will_break: break


def save_as():
	with open(f"Return/{FILE_NAME}", "w", encoding="utf-8") as f:
		data = {
			"size": SIZE,
			"data": {
				f"{x};{y}": board_data[y][x]
				for x in range(SIZE)
				for y in range(SIZE)
			}
		}
		json.dump(data, f, indent=4, sort_keys=True)

	print(data)

for b in board_data:
	print(b)

save_as()