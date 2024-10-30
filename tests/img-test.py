from textual.app import App, ComposeResult
from textual.widgets import Static
from textual import scroll_view as ScrollView
import os
import subprocess

# Custom Widget to call timg and display image using Kitty protocol
class TimgImageWidget(Static):
    def __init__(self, image_path: str):
        super().__init__()
        self.image_path = image_path

    # Render method to display the image using timg
    def render(self) -> str:
        # Command to display image using timg and Kitty protocol
        timg_cmd = f"timg {self.image_path}"
        
        try:
            # Execute timg in the terminal
            result = subprocess.run(timg_cmd, shell=True, check=True, capture_output=True)
            return result.stdout.decode()  # Returning the stdout as a string
        except subprocess.CalledProcessError as e:
            return f"Error displaying image: {e}"

# Textual App to host the Scrollable Widget
class ImageApp(App):
    def compose(self) -> ComposeResult:
        scroll_view = ScrollView()  # Create a scrollable container
        image_path = "image.png"  # Specify your image path here
        
        # Create the widget and mount it inside the scrollview
        image_widget = TimgImageWidget(image_path)
        scroll_view.mount(image_widget)

        # Yield the scrollable view
        yield scroll_view

# Run the Textual app
if __name__ == "__main__":
    app = ImageApp()
    app.run()

