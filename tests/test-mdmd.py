from textual.app import App, ComposeResult
from textual.widgets import DataTable
from rich.console import Console
from rich.markdown import Markdown

class MarkdownDataTableApp(App):
    """An example of using inline markdown in a DataTable."""

    def compose(self) -> ComposeResult:
        # Create a DataTable widget
        table = DataTable(id="my_table")

        # Define columns for the table
        table.add_columns("ID", "Description")

        # Define markdown content
        markdown_content_1 = Markdown("This is **bold** and *italic*.")
        markdown_content_2 = Markdown("Another **markdown** content with `code`.")

        # Render markdown to plain text using Console
        console = Console()

        # Convert markdown to renderable Text
        rendered_md_1 = console.render_str(markdown_content_1)
        rendered_md_2 = console.render_str(markdown_content_2)

        # Add rows to the table with rendered markdown text
        table.add_row("1", rendered_md_1)
        table.add_row("2", rendered_md_2)

        yield table

if __name__ == "__main__":
    MarkdownDataTableApp().run()

