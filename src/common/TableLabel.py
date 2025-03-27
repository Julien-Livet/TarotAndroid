import io
import kivy.core.image
import kivy.uix.image
from PIL import Image

class TableLabel(kivy.uix.image.Image):
    def __init__(self, window, image: Image = None):
        super().__init__()
        self._window = window
        self.setImage(image)
        self._mousePressPos = None
        self._pressed = False
        self.img = None
    
    def setImage(self, image: Image):
        self._image = image
        
        if (image):
            self.img_byte_arr = io.BytesIO()
            image.save(self.img_byte_arr, format='PNG')
            self.img_byte_arr.seek(0)
            self.img = kivy.core.image.Image(self.img_byte_arr, ext="png")
            self.texture = self.img.texture
            self.size = self.img.texture.size
            self.size_hint = (None, None)

    def imageWidth(self):
        if (not self.img):
            return 0
            
        return self.img.texture.size[0]

    def imageHeight(self):
        if (not self.img):
            return 0
            
        return self.img.texture.size[1]

    def on_touch_up(self, touch):
        super().on_touch_up(touch)
        if (not self._pressed):
            p = self.to_window(touch.x, touch.y)
            self._mousePressPos = [p[0], self._window.height - p[1]]
        else:
            self._mousePressPos = None

    def on_touch_down(self, touch):
        super().on_touch_down(touch)
        self._mousePressPos = None
        self._pressed = False
