import operator
import OpenGL.GL as gl

# Not yet thread safe, only call stuff from main thread

quads = set()

flat_texture = None
def initialize():
	global flat_texture
	flat_texture = Texture()
	flat_texture.update_raw(1, 1, 'RGBA', b'\xff' * 4)


def render():
	# FIXME: maybe make sorting invariant for efficiency?
	for quad in sorted({q for q in quads if not q.hidden}, key = operator.attrgetter('z')):
		quad.render()



class Texture:
	def __init__(self, image=None, persistent=True):
		self.persistent = persistent
		self.concrete = False
		self.width = None
		self.height = None
		self.tid = gl.glGenTextures(1)
		gl.glBindTexture(gl.GL_TEXTURE_2D, self.tid)
		gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
		gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
		gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
		if image is not None:
			self.update_image(image)

	def update_raw(self, width, height, mode, pixels):
		glformat = {'RGB': gl.GL_RGB, 'RGBA': gl.GL_RGBA, 'BGRA': gl.GL_BGRA}[mode]
		glinternal = {'RGB': gl.GL_RGB, 'RGBA': gl.GL_RGBA, 'BGRA': gl.GL_RGBA}[mode]

		gl.glBindTexture(gl.GL_TEXTURE_2D, self.tid)
		gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, glinternal, width, height, 0, glformat, gl.GL_UNSIGNED_BYTE, pixels)
		gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

		self.width = width
		self.height = height
		self.concrete = True

	def update_image(self, img):
		if img is None:
			return
		self.update_raw(img.width, img.height, img.mode, img.tobytes())

	def destroy(self, force=False):
		if self.persistent and not force:
			return
		self.concrete = False
		gl.glDeleteTextures([self.tid])
		del self.tid
		del self.concrete
		del self.persistent

	def __str__(self):
		return f'<Texture ({self.tid}) {self.width}x{self.height}{" concrete" if self.concrete else ""}{" persistent" if self.persistent else ""}>'

	def __repr__(self):
		return str(self)


class ExternalTexture:
	def __init__(self, tid):
		self.concrete = True
		self.tid = tid

	def destroy(self, force=False):
		if not force:
			return
		self.concrete = False
		gl.glDeleteTextures([self.tid])
		del self.tid
		del self.concrete

	def __str__(self):
		return f'<Texture ({self.tid}) external>>'

	def __repr__(self):
		return str(self)


class Quad:
	def __init__(self, x, y, w, h, z, texture=None, image=None, color=None):
		self.x = x
		self.y = y
		self.z = z
		self.w = w
		self.h = h
		self.hidden = False
		self.texture = Texture(image=image, persistent=False) if texture is None else texture
		self.color = (1, 1, 1, 1) if color is None else color
		quads.add(self)

	@property
	def pos(self):
		return (self.x, self.y)
	@pos.setter
	def pos(self, newpos):
		self.x, self.y = newpos

	@property
	def x1(self):
		return min(self.x, self.x + self.w)

	@property
	def x2(self):
		return max(self.x, self.x + self.w)

	@property
	def y1(self):
		return min(self.y, self.y + self.h)

	@property
	def y2(self):
		return max(self.y, self.y + self.h)

	def update_image(self, image):
		self.texture.update_image(image)

	def destroy(self):
		quads.remove(self)
		self.texture.destroy()
		del self.x # trigger AttributeError if we're used still
		del self.texture  # trigger AttributeError if we're used still

	def render(self):
		if not self.texture.concrete:
			return
		gl.glColor4f(*self.color)
		gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture.tid)
		gl.glBegin(gl.GL_QUADS)
		gl.glTexCoord2f(0.0, 1.0)
		gl.glVertex2f(self.x1, self.y1)
		gl.glTexCoord2f(1.0, 1.0)
		gl.glVertex2f(self.x2, self.y1)
		gl.glTexCoord2f(1.0, 0.0)
		gl.glVertex2f(self.x2, self.y2)
		gl.glTexCoord2f(0.0, 0.0)
		gl.glVertex2f(self.x1, self.y2)
		gl.glEnd()
		gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

	def __str__(self):
		return f'<{type(self).__name__} {self.x}x{self.y} +{self.w}+{self.h} @{self.z}>'

	def __repr__(self):
		return str(self)



class FlatQuad(Quad):
	def __init__(self, x, y, w, h, z, color):
		super().__init__(x, y, w, h, z, texture=flat_texture, color=color)
