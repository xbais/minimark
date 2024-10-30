from textual.app import App, ComposeResult
from textual_image.widget import Image

class ImageApp(App[None]):
    CSS = """
    Image {
        background: transparent;
    }
    """

    def compose(self) -> ComposeResult:
        im = Image("image.png")
        im.styles.margin = 0
        im.styles.padding = 0
        yield im

ImageApp().run()
