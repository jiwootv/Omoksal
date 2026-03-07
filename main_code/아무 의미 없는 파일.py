print("○○○○○○○○○○○○○○○○")
print("●●●●●●●●●●●●●●●●")
print("● ●")
print('●ㅤ●')

k = [3, 1, 4, 1, 5, 9 ,2, 6974, 6974]
a = k

k[0] = 2
print(k, a)

print(max(k))
print(k.index(max(k)))

def indexes(list: list, value):
	k = []
	a = 0
	for i in list:
		if i == value: k.append(a)
		a += 1
	return k

print(indexes(k, max(k)))