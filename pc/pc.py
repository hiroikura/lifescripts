#!/usr/bin/python3 -i
#
# bc alternative, "pc" - Python Caluculator
#

from math import *

# some aliases
rad = radians
deg = degrees

qpi = pi / 4.0 # for 45deg

# Pythagoras Theorems
def pytha(x,y):
    return sqrt(x**2 + y**2)

def pythc(z,x):
    return sqrt(z**2 - x**2)

# TBD: precision caler

# Usage printer
print('''\
pc - Python Calculator
Predefined:
 Constants: pi=3.141592..., e=2.718281...  (qpi=pi/4)
 Angular conversion: rad(d), deg(r)
 Square roots: sqrt(x), pytha(x,y), pythc(z,x)
 Trigonometric: sin(x), cos(x), tan(x), asin(x), acos(x), atan(x), atan2(y,x)
 Power, exponential, logarithmic: exp(x), log(x), pow(x,y), ...
''', end='')

# print "bcl Original constants and functions::\n"
# print "Constants:\n"
# print " pi: Pi (3.141592...)\n"
# print " qpi: 1/4 Pi\n"
# print "Functions:\n"
# print " rad(d): returns radian from degree\n"
# print " deg(r): returns degree from radian\n"
# print " pytha(x,y): returns sqrt(x^2 + y^2)\n"
# print " pythc(z,x): returns sqrt(z^2 - x^2)\n"
# print "Aliases:\n"
# print " cos(r), sin(r), tan(r), atan(a), log(x)\n"
# 
# # standard precision for engineering
# scale = 6
