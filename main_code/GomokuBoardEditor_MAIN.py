# == 기본 임포트 ==
import sys
from PyQt6 import QtCore, QtGui, QtWidgets
from main_code.GomokuEditor_base import Ui_MainWindow
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtCore import QUrl
import json
import Gomoku_Board
import MAINSETTINGS

# === 환경변수 ===
FUNNYMODE = MAINSETTINGS.FUNNYMODE
DEBUG_MODE = MAINSETTINGS.DEBUG_MODE

SIZE = 15
EMPTY = 0
BLACK = 1
WHITE = 2

# ====== 좌표 변환 설정 ======
GAP = 28

# (511,259)가 기준 교차점 "중심" (윈도우 좌표라고 가정)
REF_WIN_X = 494
REF_WIN_Y = 270

# 기준점이 의미하는 칸 좌표(일단 중앙)
REF_CELL_X = 6
REF_CELL_Y = 7


def indexes(list: list, value):
	k = []
	a = 0
	for i in list:
		if i == value: k.append(a)
		a += 1
	return k

def remove_duplicates(lst):
	result = []
	for item in lst:
		if item not in result:
			result.append(item)
	return result


if DEBUG_MODE: print("Main File Loaded")

class MainWindow(QtWidgets.QMainWindow):
	def __init__(self):
		super().__init__()
		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)

		# ----- 보드 데이터 -----
		self.board = [[EMPTY for _ in range(SIZE)] for __ in range(SIZE)]

		# ----- 돌 이미지 -----
		self.pix_black = QtGui.QPixmap("img/BlackStone.png")
		self.pix_white = QtGui.QPixmap("img/WhiteStone.png")
		self.pix_marker = QtGui.QPixmap("img/marker.png")

		# UI에 샘플로 있던 라벨은 숨김(원하면 지워도 됨)
		self.ui.BlackStone.hide()
		self.ui.WhiteStone.hide()

		# 돌 라벨 저장 (x,y) -> QLabel
		self.placed_stones = {}

		# Board 라벨 클릭 받기
		self.ui.Board.installEventFilter(self)

		# 기준점(윈도우 좌표)을 Board 라벨 내부 좌표로 변환해서 저장
		p = self.ui.Board.mapFrom(self, QtCore.QPoint(REF_WIN_X, REF_WIN_Y))
		self.ref_px = p.x()
		self.ref_py = p.y()

		# 클릭 스냅 허용 오차(교차점에서 너무 멀면 무시)
		self.snap_tol = 12  # 10~14 사이 취향대로

		# 하이퍼커넥트 www
		self.ui.actionSave_As.triggered.connect(self.save_as)
		self.ui.actionLoad.triggered.connect(self.load_board)
		self.ui.actionReset.triggered.connect(self.reset)
		self.ui.actionMarker.triggered.connect(self.set_marker)
		self.ui.actionGetRow.triggered.connect(self.get_rows)
		self.ui.actionAutoplace.triggered.connect(self.auto_place)

		# 소@리들
		self.place_sound = QSoundEffect()
		self.place_sound.setSource(QUrl.fromLocalFile("sound/Slap.wav"))
		self.place_sound.setVolume(0.5)  # 0.0 ~ 1.0

		self.delete_sound = QSoundEffect()
		self.delete_sound.setSource(QUrl.fromLocalFile("sound/ang!.wav"))
		self.delete_sound.setVolume(0.5)  # 0.0 ~ 1.0

		self.load_sound = QSoundEffect()
		self.load_sound.setSource(QUrl.fromLocalFile("sound/Fart.wav"))
		self.load_sound.setVolume(0.5)  # 0.0 ~ 1.0

		self.save_sound = QSoundEffect()
		self.save_sound.setSource(QUrl.fromLocalFile("sound/Suction.wav"))
		self.save_sound.setVolume(0.1)  # 0.0 ~ 1.0

		self.reset_sound = QSoundEffect()
		self.reset_sound.setSource(QUrl.fromLocalFile("sound/Boom.wav"))
		self.save_sound.setVolume(0.1)

		self.dragging = False
		self.drag_stone = EMPTY
		self.last_cell = None

		self.ui.Board.setMouseTracking(True)
		self.setMouseTracking(True)

		# 키 입력 받기 (스페이스)
		self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
		self.ui.Board.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)

		# 현재 커서가 가리키는 칸
		self.hover_cell = None
		self.allow_overwrite = False

		# class 인스턴스 지정.
		self.GomokuBoard = Gomoku_Board.GomokuBoard(self.board)

		if DEBUG_MODE: print("Mainwindow: __init__ loaded")

	def eventFilter(self, obj, event):
		if obj is self.ui.Board:
			etype = event.type()

			# ====== 마우스 클릭 시작 ======
			if etype == QtCore.QEvent.Type.MouseButtonPress:
				pos = event.position()
				px, py = int(pos.x()), int(pos.y())

				cell = self.pixel_to_cell(px, py)
				self.hover_cell = cell
				self.setFocus()

				if event.button() == QtCore.Qt.MouseButton.LeftButton:
					self.dragging = True
					self.drag_stone = BLACK
				elif event.button() == QtCore.Qt.MouseButton.RightButton:
					self.dragging = True
					self.drag_stone = WHITE
				elif event.button() == QtCore.Qt.MouseButton.MiddleButton:
					self.dragging = True
					self.drag_stone = EMPTY
				else:
					return True

				self.last_cell = None

				# 클릭 1회 즉시 처리
				if cell is not None:
					x, y = cell
					if self.drag_stone == EMPTY:
						self.remove_stone(x, y)
					else:
						if self.allow_overwrite or self.board[y][x] == EMPTY:
							self.board[y][x] = self.drag_stone
							self.place_stone(x, y, self.drag_stone)

				return True

			# ====== 마우스 이동: hover 갱신 + (드래그 중이면 연속 설치) ======
			if etype == QtCore.QEvent.Type.MouseMove:
				pos = event.position()
				px, py = int(pos.x()), int(pos.y())

				cell = self.pixel_to_cell(px, py)
				self.hover_cell = cell
				self.setFocus()

				if not self.dragging:
					return True

				if cell is None or cell == self.last_cell:
					return True

				self.last_cell = cell
				x, y = cell

				if self.drag_stone == EMPTY:
					self.remove_stone(x, y)
				else:
					if self.allow_overwrite or self.board[y][x] == EMPTY:
						self.board[y][x] = self.drag_stone
						self.place_stone(x, y, self.drag_stone)

				return True

			# ====== 마우스 클릭 끝 ======
			if etype == QtCore.QEvent.Type.MouseButtonRelease:
				self.dragging = False
				self.drag_stone = EMPTY
				self.last_cell = None
				return True

		return super().eventFilter(obj, event)

	def keyPressEvent(self, event):
		if event.key() == QtCore.Qt.Key.Key_Space:
			if self.hover_cell is None:
				return

			x, y = self.hover_cell

			# 토글: 이미 MARK면 삭제, 아니면 설치
			if self.board[y][x] == 3:
				self.remove_stone(x, y)
				return

			# 덮어쓰기 OFF면 빈칸에만 설치, ON이면 어디든 설치(원하면 MARK만 예외 처리 가능)
			if (not self.allow_overwrite) and self.board[y][x] != EMPTY:
				return

			self.board[y][x] = 3
			self.place_stone(x, y, 3)
			return

		super().keyPressEvent(event)

	def handle_click(self, px, py, stone_type):
		cell = self.pixel_to_cell(px, py)
		if cell is None:
			return

		x, y = cell

		if stone_type == EMPTY:
			self.remove_stone(x, y)
			return

		# 이미 돌 있으면 덮어쓰기 막기(원하면 덮어쓰게 바꿔도 됨)
		# if self.board[y][x] != EMPTY:
		# 	return

		self.board[y][x] = stone_type
		self.place_stone(x, y, stone_type)

	def board_instance_update(self):
		self.GomokuBoard = Gomoku_Board.GomokuBoard(self.board)

	def pixel_to_cell(self, px, py):
		# Board 라벨 내부 픽셀 -> (x,y)

		dx = px - self.ref_px
		dy = py - self.ref_py

		ox = int(round(dx / GAP))
		oy = int(round(dy / GAP))

		# 교차점에서 너무 멀면 무시
		if abs(dx - ox * GAP) > self.snap_tol:
			return None
		if abs(dy - oy * GAP) > self.snap_tol:
			return None

		x = REF_CELL_X + ox
		y = REF_CELL_Y + oy

		if not (0 <= x < SIZE and 0 <= y < SIZE):
			return None

		return (x, y)

	def cell_to_pixel(self, x, y):
		# (x,y) -> Board 라벨 내부 픽셀 (교차점 중심)
		cx = self.ref_px + (x - REF_CELL_X) * GAP
		cy = self.ref_py + (y - REF_CELL_Y) * GAP
		return (cx, cy)

	def place_stone(self, x, y, stone_type, sound=True):
		if sound:
			self.place_sound.play()
		# 기존 라벨 있으면 제거
		if (x, y) in self.placed_stones:
			# self.delete_sound.play()
			self.placed_stones[(x, y)].deleteLater()
			del self.placed_stones[(x, y)]

		if stone_type == BLACK:
			pix = self.pix_black
		elif stone_type == WHITE:
			pix = self.pix_white
		else:
			pix = self.pix_marker

		stone = QtWidgets.QLabel(parent=self.ui.Board)
		stone.setScaledContents(True)

		# 돌 크기(픽셀) - 교차점 간격 28이면 22~26 사이가 보통 예쁨
		stone_size = 22
		stone.resize(stone_size, stone_size)

		cx, cy = self.cell_to_pixel(x, y)

		# 중심 맞추기
		stone.move(cx - stone_size // 2, cy - stone_size // 2)

		stone.setPixmap(pix)
		stone.show()

		self.placed_stones[(x, y)] = stone

	def remove_stone(self, x, y):
		if self.board[y][x] == EMPTY:
			return

		self.board[y][x] = EMPTY

		if (x, y) in self.placed_stones:
			self.placed_stones[(x, y)].deleteLater()
			if FUNNYMODE:
				self.delete_sound.play()
			del self.placed_stones[(x, y)]

	def clear_board(self):
		for _, label in list(self.placed_stones.items()):
			label.deleteLater()
		self.placed_stones.clear()

		self.board = [[EMPTY for _ in range(SIZE)] for __ in range(SIZE)]

	def save_as(self):
		path, _ = QtWidgets.QFileDialog.getSaveFileName(
			self,
			"판 저장하기",
			"gomoku_board.json",
			"JSON Files (*.json);;All Files (*.*)"
		)
		if not path:
			return

		data = {
			"size": SIZE,
			"data": {
				f"{x};{y}": self.board[y][x]
				for x in range(SIZE)
				for y in range(SIZE)
			}
		}

		with open(path, "w", encoding="utf-8") as f:
			json.dump(data, f, indent=2, ensure_ascii=False)

		# 일단: JSON 문자열을 클립보드에 복사 + 간단 알림

		text = json.dumps(self.board, ensure_ascii=False)

		QtWidgets.QApplication.clipboard().setText(text)
		if FUNNYMODE:
			self.save_sound.play()
			QtWidgets.QMessageBox.information(
				self,
				"알@림",
				"성공적으로 저장되었습니다.\nReturn 폴더를 확인하시오 브로."
			)
		else:
			QtWidgets.QMessageBox.information(
				self,
				"알림",
				"성공적으로 저장되었습니다.\nReturn 폴더를 확인하세요."
			)

		self.statusBar().showMessage(f"Saved: {path}", 3000)

	def load_board(self):

		path, _ = QtWidgets.QFileDialog.getOpenFileName(
			self,
			"Load Board..",
			"",
			"JSON Files (*.json);;All Files (*.*)"
		)
		if not path:
			return

		try:
			with open(path, "r", encoding="utf-8") as f:
				data = json.load(f)
		except Exception as e:
			QtWidgets.QMessageBox.critical(self, "Load Failed", str(e))
			return

		# ---- 기본 검증 ----
		if data.get("size") != SIZE:
			QtWidgets.QMessageBox.warning(self, "Load Failed", "Board size mismatch")
			return

		raw_data = data.get("data")
		if not isinstance(raw_data, dict):
			QtWidgets.QMessageBox.warning(self, "Load Failed", "Invalid data format")
			return

		# ---- 초기화 ----
		self.clear_board()

		# ---- 복원 ----
		for key, value in raw_data.items():
			try:
				x_str, y_str = key.split(";")
				x = int(x_str)
				y = int(y_str)
				v = int(value)
			except:
				continue

			if 0 <= x < SIZE and 0 <= y < SIZE and v in (EMPTY, BLACK, WHITE):
				self.board[y][x] = v
				if v != EMPTY:
					self.place_stone(x, y, v, sound=False)
		if FUNNYMODE:
			self.load_sound.play()
			QtWidgets.QMessageBox.information(
				self,
				"알@림",
				"파일을 성공적으로 로드하였습니다.\n성공적이지 못했으면 아쉬운거지 뭐"
			)
			self.statusBar().showMessage(f"파일 불@러옴: {path}", 3000)
		else:
			QtWidgets.QMessageBox.information(
				self,
				"알림",
				"파일을 성공적으로 로드하였습니다."
			)
			self.statusBar().showMessage(f"파일 불러옴: {path}", 3000)

	def set_marker(self):
		# print(self.where_should_i_place())
		k = self.get_marker()
		for s in k:
			self.place_stone(s["x"], s["y"], 3, sound=False)



		if FUNNYMODE:
			self.save_sound.play()
			QtWidgets.QMessageBox.information(
				self,
				"알@림",
				"돌들을 성공적으로 포@박했습니다."
			)
			self.statusBar().showMessage(f"마커로 구속 완료", 3000)
		else:
			QtWidgets.QMessageBox.information(
				self,
				"알림",
				"바둑돌 주위에 마커 설치를 완료하였습니다."
			)
			self.statusBar().showMessage(f"마커 설치 완료", 3000)

	def get_marker(self):
		self.board_instance_update()
		k = self.GomokuBoard.setMarker()
		s = self.GomokuBoard.evaluate_score()

		return k

	def where_should_i_place(self):
		# whssk 뇌빼고 써서 뭐가 뭐였는지 하나도 기억이 안납니다;;
		# 변수명은 신경쓰지 마세요
		self.board_instance_update()
		s = self.GomokuBoard.evaluate_score()
		suction = []
		for i in s:
			suction.append(i["score"])

		bung_tak = indexes(suction, max(suction))

		real_final_list = []
		for sibal in bung_tak:
			p = s[sibal]
			real_final_list.append(p)

		real_final_list = remove_duplicates(real_final_list)

		dist_list = []
		for stone in real_final_list:
			d = (stone['x'] - 7) ** 2 + (stone['y'] - 7) ** 2
			dist_list.append(d)

		min_dist = min(dist_list)

		final_candidates = []
		for i in range(len(real_final_list)):
			if dist_list[i] == min_dist:
				final_candidates.append(real_final_list[i])

		print(final_candidates)
		return final_candidates[0]

	def auto_place(self):
		self.board_instance_update()
		k = self.GomokuBoard.where_should_i_place()
		self.place_stone(k['x'], k['y'], 2)
		self.board[k['y']][k['x']] = 2

	def get_rows(self):
		import traceback
		try:
			# UI 위젯 이름 확인 (여기서 틀리면 바로 잡힘)
			if not hasattr(self.ui, "xRowValue"):
				raise AttributeError("UI에 xrowValue 없음 (Designer objectName 확인)")
			if not hasattr(self.ui, "yRowValue"):
				raise AttributeError("UI에 yRowValue 없음 (Designer objectName 확인)")

			# UI(1~15) -> 내부(0~14)
			x = int(self.ui.xRowValue.value()) - 1
			y = int(self.ui.yRowValue.value()) - 1

			if not (0 <= x < SIZE and 0 <= y < SIZE):
				raise ValueError(f"좌표 범위 밖: ({x},{y})")

			v = self.board[y][x]
			if DEBUG_MODE: print(f"[GetRow] internal=({x},{y}) value={v}")

			# 돌이 아닌 칸이면 라인 계산 안 함
			if v not in (BLACK, WHITE):
				QtWidgets.QMessageBox.information(self, "GetRow", f"({x + 1},{y + 1})에는 흑/백 돌이 없음. value={v}")
				return None

			# GomokuBoard 최신화
			self.board_instance_update()

			# get_lines 함수 존재 여부 체크
			if not hasattr(self.GomokuBoard, "get_lines"):
				raise AttributeError("GomokuBoard에 get_lines 함수가 없음 (Gomoku_Board.py에 구현했는지 확인)")

			k = self.GomokuBoard.get_lines(x, y)
			if DEBUG_MODE: print("[GetRow result]", k)

			QtWidgets.QMessageBox.information(self, "GetRow", str(k))
			return k

		except Exception:
			err = traceback.format_exc()
			QtWidgets.QMessageBox.critical(self, "GetRow Crash", err)
			print(err)  # 터미널 실행 시 같이 보이게
			return None

	def reset(self):
		self.clear_board()
		if FUNNYMODE:
			self.reset_sound.play()
			QtWidgets.QMessageBox.information(
				self,
				"알@림",
				"당신의 바둑돌은 모두 펑 터졌어요!"
			)
			self.statusBar().showMessage(f"현재 바둑판의 돌들 시체로 결정", 3000)
		else:
			QtWidgets.QMessageBox.information(
				self,
				"알림",
				"판의 돌들을 성공적으로 제거하였습니다."
			)
			self.statusBar().showMessage(f"돌 리셋 완료", 3000)



if __name__ == "__main__":
	app = QtWidgets.QApplication(sys.argv)
	w = MainWindow()
	w.show()
	sys.exit(app.exec())
