from PyQt6 import uic
import sys
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtCore import QUrl
import json
import Gomoku_Board
import MAINSETTINGS

SIZE = 15
EMPTY = 0
BLACK = 1
WHITE = 2

STEP = 27
STONE_SIZE = 21
SNAP_TOL = 10

# 중앙 교차점 기준
CENTER_X = 380
CENTER_Y = 280
CENTER_CELL_X = 7
CENTER_CELL_Y = 7

# 전체 평행이동 보정
OFFSET_X = 10
OFFSET_Y = 8


class MainWindow(QtWidgets.QMainWindow):
	def __init__(self):
		super().__init__()
		uic.loadUi("ui files/main_playing_game.ui", self)

		self.board_data = [[EMPTY for _ in range(SIZE)] for __ in range(SIZE)]
		self.placed_stones = {}

		self.player_color = BLACK
		self.ai_color = WHITE
		self.game_over = False
		self.waiting_ai = False

		self.pix_black = QtGui.QPixmap("img/BlackStone.png")
		self.pix_white = QtGui.QPixmap("img/WhiteStone.png")

		# UI에 있던 샘플 돌 숨기기
		self.Black.hide()
		self.Black_2.hide()

		# board 클릭 감지
		self.board.installEventFilter(self)

		# 메뉴 액션 연결
		# objectName이 정확히 action돌_말살 이 아닐 수도 있으니까
		# 안 맞으면 print로 확인해서 이름만 바꿔주면 됨
		if hasattr(self, "action돌_말살"):
			self.action돌_말살.triggered.connect(self.reset_game)
		elif hasattr(self, "actionReset"):
			self.actionReset.triggered.connect(self.reset_game)

		print("board pos:", self.board.x(), self.board.y())
		print("center:", CENTER_X, CENTER_Y)

		self.place_sound = QSoundEffect()
		self.place_sound.setSource(QUrl.fromLocalFile("sound/Slap.wav"))
		self.place_sound.setVolume(0.5)  # 0.0 ~ 1.0

		# 디버그용
		# self.place_stone(7, 7, BLACK)
		# self.place_stone(6, 7, WHITE)
		# self.place_stone(8, 7, WHITE)
		# self.place_stone(7, 6, WHITE)
		# self.place_stone(7, 8, WHITE)

	def eventFilter(self, obj, event):
		if obj is self.board:
			if event.type() == QtCore.QEvent.Type.MouseButtonPress:
				if event.button() == QtCore.Qt.MouseButton.LeftButton:
					if self.game_over or self.waiting_ai:
						return True

					pos = event.position()
					px, py = int(pos.x()), int(pos.y())

					cell = self.pixel_to_cell(px, py)
					print("clicked:", px, py, "->", cell)

					if cell is None:
						return True

					x, y = cell
					self.player_move(x, y)
					return True

		return super().eventFilter(obj, event)

	def pixel_to_cell(self, px, py):
		# board 내부 좌표 -> 메인 윈도우 좌표
		abs_x = px + self.board.x()
		abs_y = py + self.board.y()

		base_x = CENTER_X + OFFSET_X
		base_y = CENTER_Y + OFFSET_Y

		ox = round((abs_x - base_x) / STEP)
		oy = round((abs_y - base_y) / STEP)

		target_x = base_x + ox * STEP
		target_y = base_y + oy * STEP

		if abs(abs_x - target_x) > SNAP_TOL:
			return None
		if abs(abs_y - target_y) > SNAP_TOL:
			return None

		x = CENTER_CELL_X + ox
		y = CENTER_CELL_Y + oy

		if not (0 <= x < SIZE and 0 <= y < SIZE):
			return None

		return (x, y)

	def cell_to_pixel(self, x, y):
		px = CENTER_X + OFFSET_X + (x - CENTER_CELL_X) * STEP
		py = CENTER_Y + OFFSET_Y + (y - CENTER_CELL_Y) * STEP
		return px, py

	def place_stone(self, x, y, stone_type):
		self.place_sound.play()
		if (x, y) in self.placed_stones:

			self.placed_stones[(x, y)].deleteLater()
			del self.placed_stones[(x, y)]



		label = QtWidgets.QLabel(self.centralwidget)
		label.resize(STONE_SIZE, STONE_SIZE)
		label.setScaledContents(True)

		px, py = self.cell_to_pixel(x, y)

		# CENTER_X, CENTER_Y를 교차점 중심으로 보고 돌 중심 정렬
		label.move(px - STONE_SIZE // 2, py - STONE_SIZE // 2)

		if stone_type == BLACK:
			label.setPixmap(self.pix_black)
		else:
			label.setPixmap(self.pix_white)

		label.show()

		self.placed_stones[(x, y)] = label

	def player_move(self, x, y):
		if self.board_data[y][x] != EMPTY:
			return

		self.board_data[y][x] = BLACK
		self.place_stone(x, y, BLACK)

		if self.check_win(x, y, BLACK):
			self.finish_game("흑돌 승리!")
			return

		if self.is_board_full():
			self.finish_game("무승부!")
			return

		self.waiting_ai = True
		# QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
		QtCore.QTimer.singleShot(500, self.ai_move)

	def ai_move(self):
		if self.game_over:
			self.waiting_ai = False
			QtWidgets.QApplication.restoreOverrideCursor()
			return

		gomoku = Gomoku_Board.GomokuBoard(self.board_data)
		move = gomoku.where_should_i_place()

		if move is None:
			self.waiting_ai = False
			QtWidgets.QApplication.restoreOverrideCursor()
			self.finish_game("무승부!")
			return

		x = move["x"]
		y = move["y"]

		if self.board_data[y][x] != EMPTY:
			# 혹시 AI가 이상한 자리 고르면 안전장치
			found = False
			for yy in range(SIZE):
				for xx in range(SIZE):
					if self.board_data[yy][xx] == EMPTY:
						x, y = xx, yy
						found = True
						break
				if found:
					break

			if not found:
				self.waiting_ai = False
				QtWidgets.QApplication.restoreOverrideCursor()
				self.finish_game("무승부!")
				return

		self.board_data[y][x] = WHITE
		self.place_stone(x, y, WHITE)

		self.waiting_ai = False
		QtWidgets.QApplication.restoreOverrideCursor()

		if self.check_win(x, y, WHITE):
			self.finish_game("백돌 승리!")
			return

		if self.is_board_full():
			self.finish_game("무승부!")
			return

	def count_dir(self, x, y, dx, dy, stone):
		count = 0
		nx = x + dx
		ny = y + dy

		while 0 <= nx < SIZE and 0 <= ny < SIZE and self.board_data[ny][nx] == stone:
			count += 1
			nx += dx
			ny += dy

		return count

	def check_win(self, x, y, stone):
		directions = [
			(1, 0),   # 가로
			(0, 1),   # 세로
			(1, 1),   # 대각 \
			(1, -1)   # 대각 /
		]

		for dx, dy in directions:
			count = 1
			count += self.count_dir(x, y, dx, dy, stone)
			count += self.count_dir(x, y, -dx, -dy, stone)

			if count >= 5:
				return True

		return False

	def is_board_full(self):
		for row in self.board_data:
			for cell in row:
				if cell == EMPTY:
					return False
		return True

	def clear_stones_only(self):
		for _, label in list(self.placed_stones.items()):
			label.deleteLater()
		self.placed_stones.clear()

	def reset_game(self):
		self.waiting_ai = False
		self.game_over = False
		QtWidgets.QApplication.restoreOverrideCursor()

		self.clear_stones_only()
		self.board_data = [[EMPTY for _ in range(SIZE)] for __ in range(SIZE)]

	def finish_game(self, message):
		self.game_over = True
		self.waiting_ai = False
		QtWidgets.QApplication.restoreOverrideCursor()

		QtWidgets.QMessageBox.information(self, "게임 종료", message)
		self.reset_game()



app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())