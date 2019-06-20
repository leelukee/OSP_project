#!/usr/bin/python

d = {'a' : 2, 'b' : 3, 'c' : 4, 'd': 5}
d2 = {'a': 2, 'b' : 3, 'c' : 4, 'd':5, 'e':6}

d3 = {}

for word in d.keys():
	if word in d2.keys():
		x = d[word]
		d3[word] = d2[word] * x

print(d3)
