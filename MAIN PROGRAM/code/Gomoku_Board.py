import json
import code.MAINSETTINGS

DEBUG_MODE = code.MAINSETTINGS.DEBUG_MODE

SIZE = 15

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


class GomokuBoard:
	def __init__(self, board_list):
		# 보드 리스트는 2차원의 15*15 리스트이다.
		# 예: [ [0, 1, 0, 0, 0... ]
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
		path = "../Return"
		suction = {}
		for x in range(SIZE):
			for y in range(SIZE):
				suction[f"{x};{y}"] = self.board[y][x]

		data = {
			"size": SIZE,
			"data":
				suction

		}
		with open(path + "/" + file_name + ".json", "w", encoding="utf-8") as f:
			json.dump(data, f, ensure_ascii=False, indent=2)

	def get_lines(self, x, y, board="myself"):
		"""
		입력 좌표 (x,y)의 돌(1/2)을 기준으로
		4개 축(가로/세로/대각/역대각)에서 이어진 연속 돌 길이를 계산해서
		3줄/4줄/5줄+ 개수를 반환한다.

		반환 예:
		{
			"type": 1,
			"lengths": {"h": 3, "v": 1, "d": 4, "ad": 2},
			"counts": {3: 1, 4: 1, 5: 0}
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
			# 빈칸/마커면 라인 의미 없음
			return None

		def count_dir(dx, dy):
			"""(x,y)에서 (dx,dy) 방향으로 같은 돌이 몇 개 연속인지"""
			c = 0
			cx = x + dx
			cy = y + dy
			while 0 <= cx < SIZE and 0 <= cy < SIZE and board_1[cy][cx] == stone:
				c += 1
				cx += dx
				cy += dy
			return c

		# 4축 정의: (정방향, 역방향)
		axes = {
			"h": ((1, 0), (-1, 0)),  # 가로
			"v": ((0, 1), (0, -1)),  # 세로
			"d": ((1, 1), (-1, -1)),  # 대각 \
			"ad": ((1, -1), (-1, 1))  # 역대각 /
		}

		lengths = {}
		counts = {3: 0, 4: 0, 5: 0}  # 5는 "5 이상"으로 취급

		for name, (p, n) in axes.items():
			pos = count_dir(p[0], p[1])
			neg = count_dir(n[0], n[1])
			length = 1 + pos + neg
			lengths[name] = length

			if length >= 5:
				counts[5] += 1
			elif length == 4:
				counts[4] += 1
			elif length == 3:
				counts[3] += 1
		if DEBUG_MODE:
			print(f"Stone type: {stone} at ({x},{y})")
			print("Axis lengths:", lengths)
			print("Counts: 3-in-row =", counts[3], ", 4-in-row =", counts[4], ", 5+-in-row =", counts[5])

		return {
			"type": stone,
			"lengths": lengths,
			"counts": counts
		}

	def setMarker(self):
		markers = []
		for x in range(SIZE):
			for y in range(SIZE):
				if self.board[y][x] == 1 or self.board[y][x] == 2:  # 흑돌또는 백돌이라면
					# 이제 한칸 주위를 마커로 둘@러싸 봅시다.
					"""
					방향: 
					* * *
					* / *
					* * *
					"""
					if DEBUG_MODE:
						print("______")
						print(f"TYPE: {self.board[y][x]} / Position: ({x + 1},{y + 1})")
					direction = [[-1, 1], [0, 1], [1, 1], [1, 0], [1, -1], [0, -1], [-1, -1], [-1, 0]]
					for dr in direction:
						x1 = x + dr[0]
						y1 = y + dr[1]
						if DEBUG_MODE: print(x1 + 1, y1 + 1)
						if x1 < 0:
							x1 = 0
						if x1 >= SIZE:
							x1 = SIZE - 1
						if y1 < 0:
							y1 = 0
						if y1 + 1 >= SIZE:
							y1 = SIZE - 1
						if DEBUG_MODE: print(x1 + 1, y1 + 1)
						if self.board[y1][x1] != 1 and self.board[y1][x1] != 2:  # 흑돌 또는 백돌이 아니면:
							try:
								if DEBUG_MODE: print(f"Pos: ({x1 + 1},{y1 + 1}) / {self.board[y1][x1]}")
								markers.append({"x": x1, "y": y1})
							except:
								if DEBUG_MODE: print("ERROR")
		if DEBUG_MODE:
			for _ in markers:
				print(_)
		return markers

	def getScore(self, x, y, board="myself"):
		# 공격만: (x,y)에 이미 놓인 내 돌(1/2)의 강함을 평가
		if board == "myself":
			board_ang = self.board
		else:
			board_ang = board
		linedict = self.get_lines(x, y, board_ang)
		if linedict is None:
			return 0

		score = 0

		# counts 기반(축 중 몇 개가 3/4/5+ 인지)
		c3 = linedict["counts"][3]
		c4 = linedict["counts"][4]
		c5 = linedict["counts"][5]

		# lengths 기반(각 축 길이)
		L = linedict["lengths"]  # {"h":..,"v":..,"d":..,"ad":..}

		# ---- 1) 승리/즉승급 ----
		if c5 > 0:
			return 10_000_000  # 5목이면 최상

		# ---- 2) 4줄은 매우 큼 ----
		# (4가 여러 축이면 더 큼)
		score += c4 * 200_000

		# ---- 3) 3줄 ----
		score += c3 * 5_000

		# ---- 4) 축 길이 보너스(2,3,4에 대해 추가로 가산) ----
		# 길이 자체를 조금 더 세밀하게 반영
		for name in ("h", "v", "d", "ad"):
			length = L[name]
			if length == 4:
				score += 50_000
			elif length == 3:
				score += 2_000
			elif length == 2:
				score += 200

		# ---- 5) “더블 쓰리 / 더블 포” 같은 복합 패턴 보너스 ----
		# 공격만 기준
		if c4 >= 2:
			score += 500_000  # 4가 2개면 거의 끝
		elif c4 >= 1 and c3 >= 1:
			score += 150_000  # 4+3은 강력
		elif c3 >= 2:
			score += 30_000  # 더블 3

		return score

	def evaluate_score(self):
		# 마커리스트 지정 딸깍
		markers = self.setMarker()
		scores = []  # 각 마커간의 점수가 들어갈 곳 www
		for i in markers:
			# 이때 i의 형식: {'x':a, 'y':b}

			# 일단 임시리스트 대강 suction 하고
			tempboard = [row[:] for row in self.board]

			# 그 칸 화이트워싱
			# 뭐 늘 type은 하양일거니까 저렇게 둬도 되고 마커가 있는 칸은 당연히 type = 0인칸이라 저지랄해도 됨
			tempboard[i['y']][i['x']] = 2
			for j in tempboard:
				for k in j:
					ah_sibal_gaegatda = [" ", "●", "○"]
					# print(ah_sibal_gaegatda[k], end=" ")
				# print()
			# 대충 추가를 해줍니다
			# 점수 넣어줬음
			scores.append({'x': i['x'], 'y': i['y'],'score': self.getScore(i['x'], i['y'], tempboard)})
		# print(scores)
		return scores

	def where_should_i_place(self):
		# whssk 뇌빼고 써서 뭐가 뭐였는지 하나도 기억이 안납니다;;
		# 변수명은 신경쓰지 마세요
		s = self.evaluate_score()
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


