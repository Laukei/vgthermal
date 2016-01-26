import numpy as np
import pygame
import matplotlib.pyplot as plt

class ThermalSystem:
	def __init__(self):
		self.model = np.zeros((40,40))
		self.model[8][8] = 1 #sources of heat marked with 1
		self.model[-3][-3] = -1 #heatsinks marked with -1

		self.thermal_mass = np.ones_like(self.model,dtype=float) #coefficients for building material thermal properties
		self.thermal_mass[5:-5,5:-5] += 100
		self.thermal_mass[6:-6,6:-6] -= 100

		self.rate = 10.0
		self.base = 5.0
		self.state = np.zeros_like(self.model,dtype=float)
		self.sources = []
		self.exhausts = []

		for r, row in enumerate(self.state):
			for c, cell in enumerate(row):
				self.state[r][c] += self.base
				if self.model[r][c] == 1:
					self.sources.append([r,c])
				elif self.model[r][c] == -1:
					self.exhausts.append([r,c])
		self.genNeighbours()

	def genNeighbours(self):
		self.neighbours = []
		for r in range(self.model.shape[0]):
			self.neighbours.append([])
			for c in range(self.model.shape[1]):
				self.neighbours[-1].append([])
				if c+1 < self.model.shape[1]:
					self.neighbours[r][c].append([r,c+1])
				if c-1 >= 0:
					self.neighbours[r][c].append([r,c-1])
				if r+1 < self.model.shape[0]:
					self.neighbours[r][c].append([r+1,c])
				if r-1 >= 0:
					self.neighbours[r][c].append([r-1,c])

	def _toggleSource(self,r,c):
		if [r,c] in self.sources:
			self.sources.pop(self.sources.index([r,c]))
		else:
			self.sources.append([r,c])

	def _toggleExhaust(self,r,c):
		if [r,c] in self.exhausts:
			self.exhausts.pop(self.exhausts.index([r,c]))
		else:
			self.exhausts.append([r,c])

	def iterate(self):
		for source in self.sources:
			self.state[source[0],source[1]]+= self.rate

		for exhaust in self.exhausts:
			self.state[exhaust[0],exhaust[1]]/=2.0

		self.flowstate = np.zeros_like(self.model,dtype=float)
		for r, row in enumerate(self.neighbours):
			for c, cell in enumerate(row):
				self.flows = []
				for n, neighbour in enumerate(cell):
					if self.state[r][c] > self.state[neighbour[0]][neighbour[1]]:
						self.flows.append([neighbour,self.state[r][c]-self.state[neighbour[0]][neighbour[1]]])
				if len(self.flows)>0:
					for flow in self.flows:
						self.change = flow[1]/(float(len(self.flows)+1))
						self.flowstate[flow[0][0]][flow[0][1]]+=self.change/self.thermal_mass[flow[0][0]][flow[0][1]]
						self.flowstate[r][c]-=self.change/self.thermal_mass[r][c]

		self.state=np.add(self.state,self.flowstate)

	def getState(self):
		return self.state

	def getThermalMass(self):
		return self.thermal_mass

	def shape(self):
		return self.state.shape

	def toggleSource(self,r,c):
		if self.model[r][c] != 1:
			self.model[r][c]=1
		else:
			self.model[r][c]=0
		self._toggleSource(r,c)

	def toggleExhaust(self,r,c):
		if self.model[r][c] != -1:
			self.model[r][c]=-1
		else:
			self.model[r][c]=0
		self._toggleExhaust(r,c)



class Square(pygame.sprite.Sprite):
	def __init__(self,x,y,w,h,color):
		pygame.sprite.Sprite.__init__(self)
		self.image = pygame.Surface([w,h])
		self.image.fill(color)
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y
	def setColor(self,color):
		self.image.fill(color)

class GridSquare(Square):
	def __init__(self,x,y,w,h,color,r,c):
		Square.__init__(self,x,y,w,h,color)
		self.r = r
		self.c = c
	def getRC(self):
		return self.r, self.c

class Button(Square):
	def __init__(self,x,y,w,h,color,text):
		Square.__init__(self,x,y,w,h,color)
		self.updateText(text)
	def updateText(self,text):
		self.text = text
		offset = font.size('Tg')[1]-5
		for r, row in enumerate(self.text.split('\n')):
			self.textSurf = font.render(row,20,BLACK)
			self.image.blit(self.textSurf,(3,0+offset*r))
	def setColor(self,color):
		self.image.fill(color)
		self.updateText(self.text)



def scaled_color(value,maxima,minima):
	'''
	scale_factor = (255.0/float(maxima-minima))
	return_value = []
	for i in range(3):
		if value<=maxima and value>=minima:
			return_value.append(int(value*scale_factor))
		elif value>maxima:
			return_value.append(255)
		elif value<minima:
			return_value.append(0)
	return tuple(return_value)
	'''
	if value > maxima:
		return WHITE
	elif value < minima:
		return BLACK
	else:
		return tuple([int(255*x) for x in plt.cm.jet((value-minima)/(maxima-minima))[:-1]])

if __name__=="__main__":
	pygame.init()

	minima = 0
	maxima = 50
	border_size = 0

	ts = ThermalSystem()
	x_number, y_number = ts.shape()

	WINDOW_AREA = (900,800)
	CONTROLS = 100
	BLACK = (0,0,0)
	WHITE = (255,255,255)
	RED = (255,100,100)
	screen = pygame.display.set_mode(WINDOW_AREA)
	pygame.display.set_caption('Thermal Model')
	fontname = 'Garamond'
	font = pygame.font.SysFont(fontname,20,True,False)
	clock = pygame.time.Clock()

	all_sprites_list = pygame.sprite.LayeredUpdates()
	buttons_list = pygame.sprite.LayeredUpdates()

	model_square_map = []
	for r, row in enumerate(ts.getState()):
		model_square_map.append([])
		for c, cell in enumerate(row):
			sq = GridSquare(r*((WINDOW_AREA[0]-CONTROLS)/x_number)+border_size,c*((WINDOW_AREA[1])/y_number)+border_size,(WINDOW_AREA[0]/x_number)-2*border_size,(WINDOW_AREA[1]/y_number)-2*border_size,scaled_color(cell,maxima,minima),r,c)
			model_square_map[-1].append(sq)
			all_sprites_list.add(sq)

	material_view_button = Button((WINDOW_AREA[0]-CONTROLS)+4,1,CONTROLS-5,80-2,WHITE,'Material\nview')
	buttons_list.add(material_view_button)
	all_sprites_list.add(material_view_button)

	LmbPressed = False
	RmbPressed = False
	ModelViewOn = False

	done = False
	while done == False:
		#main loop
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				done = True
			elif event.type == pygame.MOUSEBUTTONDOWN:
				#print event.button
				if event.button == 1:
					LmbPressed = True
				elif event.button == 3:
					RmbPressed = True

		if LmbPressed or RmbPressed:
			under_mouse = [s for s in all_sprites_list.sprites() if s.rect.collidepoint(pygame.mouse.get_pos())]
			if under_mouse != []:
				for item in under_mouse:
					if isinstance(item,GridSquare):
						if LmbPressed:
							ts.toggleSource(*item.getRC())
							print ts.sources
						elif RmbPressed:
							ts.toggleExhaust(*item.getRC())
							print ts.exhausts
					if item is material_view_button:
						ModelViewOn = not ModelViewOn
						if ModelViewOn == True:
							material_view_button.setColor(RED)
						else:
							material_view_button.setColor(WHITE)

		LmbPressed = False
		RmbPressed = False

		screen.fill(BLACK)

		if ModelViewOn:
			mvmaxima = ts.getThermalMass().max()
			mvminima = ts.getThermalMass().min()
			for r, row in enumerate(ts.getThermalMass()):
				for c, cell in enumerate(row):
					model_square_map[r][c].setColor(scaled_color(cell,mvmaxima,mvminima))
		else:
			ts.iterate()
			for r, row in enumerate(ts.getState()):
				for c, cell in enumerate(row):				
					model_square_map[r][c].setColor(scaled_color(cell,maxima,minima))

		all_sprites_list.draw(screen)
		pygame.display.flip()
		clock.tick(120)
	pygame.quit()