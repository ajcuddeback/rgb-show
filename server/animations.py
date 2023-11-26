import board
import neopixel
import time

num_pixels = 100
pixels = neopixel.NeoPixel(board.D18, num_pixels, brightness=0.3, auto_write=False, pixel_order=neopixel.RGB)

axis = [[0, 29], [30, 49], [50, 64], [65, 74], [75, 84], [85, 94], [95, 99]]
colors = [(255,20,217), (0,255,0), (255,0,0)]

# Loop over first set, then second set, then so on...
def climb(color):
	for i in range(len(axis)):
		for j in range(axis[i][0], axis[i][1]):
			pixels[j] = color
		pixels.show()
		time.sleep(0.3)

def fillup():
	for color in colors:
		climb(color)
	time.sleep(0.3)


def shutdown():
	print("SHUTTING OFF")
	pixels.fill((0,0,0))
	pixels.show()