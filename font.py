import PIL.Image, PIL.ImageDraw, PIL.ImageFont
import OpenGL.GL as gl
from dataclasses import dataclass

from logger import Logger



# FIXME: WIP
import time
import threading
def do_renders():
	while True:
		#print(f'Font render thread: {len(do_renders.scheduled)}')
		while do_renders.scheduled:
			text = do_renders.scheduled.pop(0)
			text.render()
		time.sleep(0.01)
do_renders.scheduled = []
threading.Thread(target=do_renders, daemon=True).start()



class Text:
	log = Logger(module='Font', color=Logger.Black + Logger.Bright)
	font = None
	text = None
	max_width = None
	max_lines = 1
	width = 0
	height = 0
	image = None
	_texture = None

	def __init__(self, font, text, max_width=None, max_lines=1):
		self.font = font
		self.max_width = max_width
		self.max_lines = max_lines

		self.set_text(text)

	def set_text(self, text):
		if text != self.text:
			self.text = text
			#self.render()
			do_renders.scheduled.append(self)

	def get_size(self, text):
		image = PIL.Image.new('RGBA', (8, 8), (0, 164, 201))
		w, h = PIL.ImageDraw.Draw(image).textsize(text, self.font.font, stroke_width=self.font.stroke_width)
		del image
		return w, h

	def render(self):
		self.log.info(f'Rendering text: "{self.text}"')


		# short-circuit: render single line
		#width = self.max_width or 4096
		#height = round(self.font.size * 1.25)
		#image = PIL.Image.new('RGBA', (width, height), (0, 164, 201, 0))
		#PIL.ImageDraw.Draw(image).text(
		#	(0, 0),
		#	self.text,
		#	font=self.font.font,
		#	fill=(255, 255, 255),
		#	stroke_width=self.font.stroke_width,
		#	stroke_fill=(0, 0, 0)
		#)
		#self.width = width
		#self.height = height
		#self.image = image
		#return


		text = self.text
		max_width = self.max_width or 4096
		height = 0
		width = 0
		lines = []
		while len(lines) < self.max_lines and text:
			line_width = 0
			idx = 1
			while line_width < max_width and idx <= len(text):
				idx += 1
				line_width, h = self.get_size(text[:idx])
			idx -= 1
			lines.append(text[:idx])
			text = text[idx:]
			width = max(width, line_width)
			height += h

		# Draw text
		image = PIL.Image.new('RGBA', (width, height), (0, 164, 201, 0))
		PIL.ImageDraw.Draw(image).text(
			(0, 0),
			'\n'.join(lines),
			font=self.font.font,
			fill=(255, 255, 255),
			stroke_width=self.font.stroke_width,
			stroke_fill=(0, 0, 0)
		)

		self.width = width
		self.height = height
		self.image = image

	def texture(self):
		if self.image is None:
			return self._texture

		if self._texture is None:
			self._texture = gl.glGenTextures(1)

		gl.glBindTexture(gl.GL_TEXTURE_2D, self._texture)
		gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
		gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
		gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, self.width, self.height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, self.image.tobytes())
		gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

		# FIXME: is this valid?
		del self.image
		self.image = None

		return self._texture


class Font:
	log = Logger(module='Font', color=Logger.Black + Logger.Bright)
	font = None
	name = None
	size = None
	stroke_width = 0

	def __init__(self, fontname, size, stroke_width):
		self.log.info(f'Creating instance for {fontname} {size}')
		self.name = fontname
		self.size = size
		self.font = PIL.ImageFont.truetype(fontname, size)
		self.stroke_width = stroke_width

	def text(self, text, max_width=None, max_lines=1):
		t = Text(self, text, max_width, max_lines)
		return t
