from client import Window
import locale
import os
import kivy.app

class App(kivy.app.App):
    def build(self):
        kivy.core.window.Window.orientation = 'landscape'

        return Window.Window(self)

if (__name__ == "__main__"):
    locale_dir = os.path.join(os.path.dirname(__file__), 'locales')
    lang = locale.getlocale()[0]
    
    from jnius import autoclass
    Locale = autoclass('java.util.Locale')
    loc = Locale.getDefault()
    lang = loc.getLanguage() + "_" + loc.getCountry()

    lang = gettext.translation('messages', localedir = locale_dir, languages = [lang], fallback = True)
    lang.install()

    app = App()
    app.run()

