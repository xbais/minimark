import asyncio
from textual.app import App
from textual.widgets import ProgressBar

class ProgressApp(App):
    total_steps: int = 100  # Define the total number of steps

    def compose(self):
        # Create a progress bar widget
        self.progress_bar = ProgressBar(show_percentage=True, total=self.total_steps)
        return [self.progress_bar]  # Return a list of widgets directly

    async def on_mount(self) -> None:
        # Start the asynchronous task that updates the progress bar
        await self.run_progress_task()

    async def run_progress_task(self) -> None:
        for step in range(self.total_steps):
            await asyncio.sleep(0.1)  # Simulate work being done
            self.progress_bar.advance()  # Increment the progress bar

if __name__ == "__main__":
    app = ProgressApp()  # Create an instance of ProgressApp
    app.run()  # Call run on the instance
