import json
import MAINSETTINGS

DEBUG_MODE = MAINSETTINGS.DEBUG_MODE

SIZE = 15


def indexes(list_: list, value):
	k = []
	a = 0
	for i in list_:
		if i == value:
			k.append(a)
		a += 1
	return k


def remove_duplicates(lst):
	result = []
	for item in lst:
		if item not in result:
			result.append(item)
	return result


class GomokuBoard:
	def __init__(self, board_list):
		# 보드 리스트는 2차원의 15*15 리스트이다.
		# 예: [[0, 1, 0, 0, 0...], ...]
		# 흑은 1이고, 백은 2이다.
		self.board = board_list

	def edit_board(self, x, y, type):
		self.board[y][x] = type

	def get_nowboard(self):
		return self.board

	def get_now_lines(self):
		for y in self.board:
			for x in y:
				print(x, end=" ")
			print()
		return self.board

	def save_as(self, file_name):
		path = "Return"
		suction = {}
		for x in range(SIZE):
			for y in range(SIZE):
				suction[f"{x};{y}"] = self.board[y][x]

		data = {
			"size": SIZE,
			"data": suction
		}
		with open(path + "/" + file_name + ".json", "w", encoding="utf-8") as f:
			json.dump(data, f, ensure_ascii=False, indent=2)

	def get_lines(self, x, y, board="myself"):
		"""
		입력 좌표 (x,y)의 돌(1/2)을 기준으로
		4개 축(가로/세로/대각/역대각)에서 이어진 연속 돌 길이와
		양 끝이 얼마나 열려 있는지(open_ends)를 계산한다.

		open_ends:
			2 -> 양쪽 열림
			1 -> 한쪽 열림
			0 -> 양쪽 막힘

		반환 예:
		{
			"type": 1,
			"axes": {
				"h": {"length": 3, "open_ends": 2},
				"v": {"length": 1, "open_ends": 0},
				"d": {"length": 4, "open_ends": 1},
				"ad": {"length": 2, "open_ends": 2}
			},
			"counts": {
				3: 1,
				4: 1,
				5: 0,
				"open3": 1,
				"semiopen3": 0,
				"open4": 0,
				"semiopen4": 1
			}
		}
		"""
		if board == "myself":
			board_1 = self.board
		else:
			board_1 = board

		if not (0 <= x < SIZE and 0 <= y < SIZE):
			return None

		stone = board_1[y][x]
		if stone not in (1, 2):
			return None

		def count_dir(dx, dy):
			c = 0
			cx = x + dx
			cy = y + dy

			while 0 <= cx < SIZE and 0 <= cy < SIZE and board_1[cy][cx] == stone:
				c += 1
				cx += dx
				cy += dy

			# while 종료 직후 좌표 = 끊긴 첫 칸
			return c, cx, cy

		axes_def = {
			"h": ((1, 0), (-1, 0)),
			"v": ((0, 1), (0, -1)),
			"d": ((1, 1), (-1, -1)),
			"ad": ((1, -1), (-1, 1))
		}

		axes = {}
		counts = {
			3: 0,
			4: 0,
			5: 0,
			"open3": 0,
			"semiopen3": 0,
			"open4": 0,
			"semiopen4": 0
		}

		for name, (p, n) in axes_def.items():
			pos, px, py = count_dir(p[0], p[1])
			neg, nx, ny = count_dir(n[0], n[1])

			length = 1 + pos + neg
			open_ends = 0

			if 0 <= px < SIZE and 0 <= py < SIZE and board_1[py][px] == 0:
				open_ends += 1

			if 0 <= nx < SIZE and 0 <= ny < SIZE and board_1[ny][nx] == 0:
				open_ends += 1

			axes[name] = {
				"length": length,
				"open_ends": open_ends
			}

			if length >= 5:
				counts[5] += 1
			elif length == 4:
				counts[4] += 1
				if open_ends == 2:
					counts["open4"] += 1
				elif open_ends == 1:
					counts["semiopen4"] += 1
			elif length == 3:
				counts[3] += 1
				if open_ends == 2:
					counts["open3"] += 1
				elif open_ends == 1:
					counts["semiopen3"] += 1

		if DEBUG_MODE:
			print(f"Stone type: {stone} at ({x},{y})")
			print("Axes:", axes)
			print("Counts:", counts)

		return {
			"type": stone,
			"axes": axes,
			"counts": counts
		}

	def setMarker(self):
		markers = []
		for x in range(SIZE):
			for y in range(SIZE):
				if self.board[y][x] == 1 or self.board[y][x] == 2:
					if DEBUG_MODE:
						print("______")
						print(f"TYPE: {self.board[y][x]} / Position: ({x + 1},{y + 1})")

					direction = [[-1, 1], [0, 1], [1, 1], [1, 0], [1, -1], [0, -1], [-1, -1], [-1, 0]]
					for dr in direction:
						x1 = x + dr[0]
						y1 = y + dr[1]

						if DEBUG_MODE:
							print(x1 + 1, y1 + 1)

						if x1 < 0:
							x1 = 0
						if x1 >= SIZE:
							x1 = SIZE - 1
						if y1 < 0:
							y1 = 0
						if y1 >= SIZE:
							y1 = SIZE - 1

						if DEBUG_MODE:
							print(x1 + 1, y1 + 1)

						if self.board[y1][x1] != 1 and self.board[y1][x1] != 2:
							try:
								if DEBUG_MODE:
									print(f"Pos: ({x1 + 1},{y1 + 1}) / {self.board[y1][x1]}")
								markers.append({"x": x1, "y": y1})
							except:
								if DEBUG_MODE:
									print("ERROR")

		if DEBUG_MODE:
			for _ in markers:
				print(_)

		return remove_duplicates(markers)

	def getScore(self, x, y, board="myself"):
		# 공격 점수: (x,y)에 이미 놓인 돌의 강함을 평가
		if board == "myself":
			board_ang = self.board
		else:
			board_ang = board

		linedict = self.get_lines(x, y, board_ang)
		if linedict is None:
			return 0

		score = 0
		axes = linedict["axes"]
		counts = linedict["counts"]

		c3 = counts[3]
		c4 = counts[4]
		c5 = counts[5]

		open3 = counts["open3"]
		semiopen3 = counts["semiopen3"]
		open4 = counts["open4"]
		semiopen4 = counts["semiopen4"]

		# 1) 오목 완성
		if c5 > 0:
			return 10000000

		# 2) 축별 기본 점수
		for name in ("h", "v", "d", "ad"):
			length = axes[name]["length"]
			open_ends = axes[name]["open_ends"]

			if length >= 5:
				score += 10000000
			elif length == 4:
				if open_ends == 2:
					score += 300000
				elif open_ends == 1:
					score += 120000
				else:
					score += 20000
			elif length == 3:
				if open_ends == 2:
					score += 30000
				elif open_ends == 1:
					score += 8000
				else:
					score += 1000
			elif length == 2:
				if open_ends == 2:
					score += 1500
				elif open_ends == 1:
					score += 300
				else:
					score += 50
			elif length == 1:
				if open_ends == 2:
					score += 10

		# 3) 복합 패턴 보너스
		if open4 >= 2:
			score += 2000000
		elif open4 >= 1 and semiopen4 >= 1:
			score += 1200000
		elif open4 >= 1:
			score += 900000
		elif semiopen4 >= 2:
			score += 500000

		if open3 >= 2:
			score += 200000
		elif open3 >= 1 and semiopen3 >= 1:
			score += 70000

		if open4 >= 1 and open3 >= 1:
			score += 1500000
		elif semiopen4 >= 1 and open3 >= 1:
			score += 400000

		if c4 >= 2:
			score += 400000
		elif c4 >= 1 and c3 >= 1:
			score += 100000
		elif c3 >= 2:
			score += 20000

		return score

	def get_block_score(self, x, y, my_stone, board="myself"):
		"""
		(x,y)에 내가 두면 상대가 이 자리에 두는 것을 막는 효과를 점수화
		방법:
		그 자리에 상대 돌을 가상으로 놓았을 때의 공격 점수를 그대로 차단 가치로 사용
		"""
		if board == "myself":
			board_ang = self.board
		else:
			board_ang = board

		if not (0 <= x < SIZE and 0 <= y < SIZE):
			return 0

		if board_ang[y][x] != 0:
			return 0

		enemy_stone = 1 if my_stone == 2 else 2

		tempboard = [row[:] for row in board_ang]
		tempboard[y][x] = enemy_stone

		return self.getScore(x, y, tempboard)

	def evaluate_score(self, my_stone=2):
		"""
		각 후보 자리에 대해
		1. 내가 여기 둘 때 공격 점수
		2. 상대가 여기 두는 것을 막는 점수
		를 합산해서 최종 점수 계산
		"""
		markers = self.setMarker()
		scores = []

		for i in markers:
			x = i["x"]
			y = i["y"]

			if self.board[y][x] != 0:
				continue

			tempboard = [row[:] for row in self.board]
			tempboard[y][x] = my_stone

			attack_score = self.getScore(x, y, tempboard)
			block_score = self.get_block_score(x, y, my_stone)

			final_score = attack_score + block_score

			scores.append({
				"x": x,
				"y": y,
				"attack_score": attack_score,
				"block_score": block_score,
				"score": final_score
			})

			if DEBUG_MODE:
				print(f"({x},{y}) attack={attack_score}, block={block_score}, final={final_score}")

		return scores

	def where_should_i_place(self, my_stone=2):
		s = self.evaluate_score(my_stone)

		if len(s) == 0:
			return {"x": 7, "y": 7, "score": 0}

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
			d = (stone["x"] - 7) ** 2 + (stone["y"] - 7) ** 2
			dist_list.append(d)

		min_dist = min(dist_list)

		final_candidates = []
		for i in range(len(real_final_list)):
			if dist_list[i] == min_dist:
				final_candidates.append(real_final_list[i])

		if DEBUG_MODE:
			print("FINAL CANDIDATES:", final_candidates)

		return final_candidates[0]