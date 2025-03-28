import pygame, os, json
from constants import *

pygame.init()


pygame.joystick.init()

# Check if a joystick is connected
if pygame.joystick.get_count() > 0:
	joystick = pygame.joystick.Joystick(0)
	joystick.init()
else:
	joystick = None  # No controller connected

class Camera:
	# Camera class that follows a target entity and handles viewport calculations"""
	def __init__(self, width, height):

		self.viewport = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
		self.width = width
		self.height = height
		self.locked = False  # Add a lock state for the camera
		self.offset_x = 0
		self.offset_y = 0
	
	def apply(self, obj):
		# Apply camera offset to an entity or rect.

		if isinstance(obj, pygame.Rect):
			return obj.move(self.offset_x, self.offset_y)
		return obj.rect.move(self.offset_x, self.offset_y)

	def apply_rect(self, rect):
	   # Apply camera offset to a rectangle

		return rect.move(self.offset_x, self.offset_y)
	
	def update(self, target):
		# Move the camera to follow a target entity

		# If camera is locked (during death sequence), don't update position
		if self.locked:
			return
		
		# Calculate the offset to center the target on screen
		self.offset_x = SCREEN_WIDTH // 2 - target.rect.centerx
		self.offset_y = SCREEN_HEIGHT // 2 - target.rect.centery
		
		# Clamp camera to level boundaries
		self.offset_x = min(0, max(-(self.width - SCREEN_WIDTH), self.offset_x))
		self.offset_y = min(0, max(-(self.height - SCREEN_HEIGHT), self.offset_y))
		
		# Update viewport for other calculations
		self.viewport = pygame.Rect(-self.offset_x, -self.offset_y, self.width, self.height)

class CameraAwareGroup(pygame.sprite.Group):
	"""A sprite group that automatically applies camera transformations."""
	def __init__(self, camera):
		super().__init__()
		self.camera = camera

	def draw(self, surface):
		"""Override draw to apply camera offsets."""
		for sprite in self.sprites():
			offset_rect = sprite.rect.move(self.camera.offset_x, self.camera.offset_y)
			surface.blit(sprite.image, offset_rect)

class Button:
	# Interactive button class for UI elements
	def __init__(self, x, y, width, height, text):
		# Initialize a button with position and text
		"""
		Args:
			x (int): X position
			y (int): Y position
			width (int): Button width
			height (int): Button height
			text (str): Button text
		"""
		self.rect = pygame.Rect(x, y, width, height)
		self.default_color = GRAY
		self.hover_color = LIGHT_GRAY
		self.clicked = False
		self.hovered = False
		self.text = text
		self.hover_sound = pygame.mixer.Sound(os.path.join("assets", "sounds", "HoverSound.mp3"))
		self.select_sound = pygame.mixer.Sound(os.path.join("assets", "sounds", "SelectSound.mp3"))
		self.hover_sound_played = False
		self.click_sound_played = False

	def draw(self, surface, font, text_color=(0, 0, 0)):
		# Draw the button on a surface
		"""
		Args:
			surface (pygame.Surface): Surface to draw on
			font (pygame.font.Font): Font for text rendering
			text_color (tuple): RGB color for text
		"""
		# Use hover color if hovered, otherwise default color
		color = self.hover_color if self.hovered else self.default_color
		
		# Draw button rectangle
		pygame.draw.rect(surface, color, self.rect)
		
		# Render and center text
		text_surface = font.render(self.text, True, text_color)
		text_rect = text_surface.get_rect(center=self.rect.center)
		surface.blit(text_surface, text_rect)

	def handle_event(self, event):
		# Handle mouse events for the button
		"""
		Args:
			event (pygame.event.Event): Pygame event to process
			
		Returns:
			bool: True if button was clicked, False otherwise
		"""
		if event.type == pygame.MOUSEMOTION:
			# Check for hover state
			pos = pygame.mouse.get_pos()
			self.hovered = self.rect.collidepoint(pos)
			
			# Play hover sound once when first hovering
			if self.hovered and not self.hover_sound_played:
				self.hover_sound.play()
				self.hover_sound_played = True
			elif not self.hovered:
				self.hover_sound_played = False
				
		elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
			# Check for click state
			pos = pygame.mouse.get_pos()
			is_clicked = self.rect.collidepoint(pos)
			
			# Play select sound once when clicked
			if is_clicked and not self.click_sound_played:
				self.select_sound.play()
				self.click_sound_played = True
				self.clicked = True
			elif not is_clicked:
				self.click_sound_played = False
				
		elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
			was_clicked = self.clicked
			self.clicked = False
			return was_clicked and self.rect.collidepoint(pygame.mouse.get_pos())
			
		return False


class SceneManager:
	# Handles scene transitions and effects
	@staticmethod
	def fade_in(screen, image, duration, background_color=(255, 255, 255)):
		# Fade in a scene on the screen
		"""
		Args:
			screen (pygame.Surface): The screen surface
			image (pygame.Surface): Image to fade in
			duration (float): Duration in seconds
			background_color (tuple): RGB background color
		"""
		clock = pygame.time.Clock()
		alpha = 0
		
		# Scale image to fit screen
		scaled_image = pygame.transform.smoothscale(image, (screen.get_width(), screen.get_height()))
		
		# Calculate alpha increment per frame (60 FPS)
		alpha_increment = 255 / (duration * 60)
		
		# Fill background
		screen.fill(background_color)
		pygame.display.flip()
		
		# Fade in loop
		while alpha < 255:
			alpha += alpha_increment
			scaled_image.set_alpha(int(alpha))
			screen.fill(background_color)
			screen.blit(scaled_image, (0, 0))
			pygame.display.flip()
			clock.tick(60)

	@staticmethod
	def fade_out(screen, image, duration, background_color=(1, 1, 1)):
		# Fade out a scene from the screen
		"""
		Args:
			screen (pygame.Surface): The screen surface
			image (pygame.Surface): Image to fade out
			duration (float): Duration in seconds
			background_color (tuple): RGB background color
		"""
		clock = pygame.time.Clock()
		start_time = pygame.time.get_ticks()
		
		# Scale image to fit screen
		scaled_image = pygame.transform.smoothscale(image, (screen.get_width(), screen.get_height()))
		
		# Fade out loop
		while pygame.time.get_ticks() - start_time < duration * 1000:
			# Calculate alpha based on elapsed time
			elapsed = pygame.time.get_ticks() - start_time
			alpha = int(elapsed / (duration * 2.5))
			alpha = max(0, min(255, alpha))
			
			# Apply alpha and draw
			scaled_image.set_alpha(255 - alpha)
			screen.fill(background_color)
			screen.blit(scaled_image, (0, 0))
			pygame.display.flip()
			clock.tick(60)
 


LOOPMAX = 32
OUT_SIDE = 256

class_type = list[pygame.Mask, pygame.Rect, pygame.Rect]

class Mask:

# Copyright (c) 2023-2025 UCSTORM
# Tous droits réservés.

	class_type = class_type
	
	def clear(sensor1):
		sensor1[0].clear()

	def newSensor(rect, center_point) -> class_type: # rect_to_mask
		""" INSIDE: MASK, RECT+CENTER_POINT, ORIGINAL_RECT"""
		mask = pygame.mask.from_surface(pygame.Surface((rect[2], rect[3])))
		return [mask, pygame.Rect(rect[0]+center_point[0], rect[1]+center_point[1], rect[2], rect[3]), rect]

	def surface_to_mask(surface, rect) -> class_type:
		mask = pygame.mask.from_surface(surface)
		return [mask, pygame.Rect(rect[0], rect[1], surface.get_size()[0], surface.get_size()[1]), pygame.Rect(rect[0], rect[1], surface.get_size()[0], surface.get_size()[1])]

	
	def blit(mask_chunk, coord, sensor) -> class_type:
		sensor[0].draw(mask_chunk[0],coord)
		return sensor

	def collide(sensor1, sensor2):
		offset = [sensor2[1][0] - sensor1[1][0], sensor2[1][1] - sensor1[1][1]]
		overlap = sensor1[0].overlap(sensor2[0], offset)
		if overlap:
			print("Overlap found at offset:", offset, "Overlap point:", overlap)
		return overlap

	def colliderect(sensor1, sensor2):
		return sensor1[1].colliderect(sensor2[1])
	
	def sensor_draw(surface, sensor, color):
		pygame.draw.rect(surface, color, sensor[1])

	def rotation_sensor(sensor, MODE, center_point):
		""" POSSIBILITY: 0 ,1, 2, 3"""
		rect = [0, 0, 0, 0]
		if MODE == 0: rect = [sensor[2][0], sensor[2][1], sensor[2][2], sensor[2][3]]
		elif MODE == 1: rect = [sensor[2][1], -(sensor[2][0] + sensor[2][2]), sensor[2][3], sensor[2][2]]
		elif MODE == 2: rect = [-(sensor[2][0] + sensor[2][2]), -(sensor[2][1] + sensor[2][3]), sensor[2][2], sensor[2][3]]
		elif MODE == 3: rect = [-(sensor[2][1] + sensor[2][3]), sensor[2][0], sensor[2][3], sensor[2][2]]

		return Mask.rect_to_mask(rect, center_point)

	def collide_inside_y(sensor1, sensor2):
		running = True
		LOOP = 0

		while running:
			if sensor1[0].overlap(sensor2[0], [sensor2[1][0] - sensor1[1][0], sensor2[1][1] - (sensor1[1][1]-LOOP)]):
				LOOP += 1
			else: running = False
			if LOOP >= LOOPMAX:
				running = False
		return LOOP

	def collide_outside_y(sensor1, sensor2):
		running = True
		LOOP = 0

		while running:
			if not sensor1[0].overlap(sensor2[0], [sensor2[1][0] - sensor1[1][0], sensor2[1][1] - (sensor1[1][1] + LOOP)]):
				LOOP += 1
			else:running = False
			if LOOP >= LOOPMAX: running = False
		return LOOP

	def collide_inside_x(sensor1, sensor2):
		running = True
		LOOP = 0

		while running:
			if sensor1[0].overlap(sensor2[0], [sensor2[1][0] - (sensor1[1][0]-LOOP), sensor2[1][1] - (sensor1[1][1])]):
				LOOP += 1
			else: running = False
			if LOOP >= LOOPMAX:running = False
		return LOOP


	def collide_outside_x(sensor1, sensor2):
		running = True
		LOOP = 0

		while running:
			if not sensor1[0].overlap(sensor2[0], [sensor2[1][0] - (sensor1[1][0]+ LOOP), sensor2[1][1] - (sensor1[1][1])]):
				LOOP += 1
			else:running = False
			if LOOP >= LOOPMAX: running = False
		return LOOP


	def collide_inside_y_minus(sensor1, sensor2):
		running = True
		LOOP = 0

		while running:
			if sensor1[0].overlap(sensor2[0], [sensor2[1][0] - sensor1[1][0], sensor2[1][1] - (sensor1[1][1]+LOOP)]):
				LOOP += 1
			else: running = False
			if LOOP >= LOOPMAX:running = False
		return -LOOP


	def collide_outside_y_minus(sensor1, sensor2):
		running = True
		LOOP = 0

		while running:
			if not sensor1[0].overlap(sensor2[0], [sensor2[1][0] - sensor1[1][0], sensor2[1][1] - (sensor1[1][1] - LOOP)]):
				LOOP += 1
			else:running = False
			if LOOP >= LOOPMAX: running = False
		return -LOOP


	def collide_inside_x_minus(sensor1, sensor2):
		running = True
		LOOP = 0

		while running:
			if sensor1[0].overlap(sensor2[0], [sensor2[1][0] - (sensor1[1][0]+LOOP), sensor2[1][1] - (sensor1[1][1])]):
				LOOP += 1
			else: running = False
			if LOOP >= LOOPMAX:running = False
		return -LOOP


	def collide_outside_x_minus(sensor1, sensor2):
		running = True
		LOOP = 0

		while running:
			if not sensor1[0].overlap(sensor2[0], [sensor2[1][0] - (sensor1[1][0]- LOOP), sensor2[1][1] - (sensor1[1][1])]):
				LOOP += 1
			else:running = False
			if LOOP >= LOOPMAX: running = False
		return -LOOP