from rich.console import Console
from rich.table import Table
console = Console()

class Utils:
    @staticmethod
    def rich_print(message: str, tag: str = "info") -> None:
        """
        Prints messages with color coding based on the tag (success, error, info, prompt)

        :param message: The message to display.
        :param tag: The type of message - 'success', 'error', 'info', & 'prompt'
        """
        colors = {"success": "green", "error": "red", "info": "cyan", "prompt": "yellow"}
        color = colors.get(tag, "cyan")
        console.print(f"[{color}]{message}[/{color}]")

    @staticmethod
    def rich_prompting(prompt_message: str, tag: str = "info") -> str:
        """
        Prompts the user for input with color scheme based on tag

        :param prompt_message: The prompt to display.
        :param tag: The type of message - 'success', 'error', 'info', & 'prompt'
        :return: The user's input as a string.
        """
        colors = {"success": "green", "error": "red", "info": "cyan", "prompt": "yellow"}
        color = colors.get(tag, "cyan")
        return console.input(f"[{color}]{prompt_message}: [/{color}]")

    @staticmethod
    def format_output_display(columns, results):
        """
        Formats the output of search and item list results in a interactive table format

        :param columns: List of columns used.
        :param results: Query result
        """
        table = Table(show_header=True, header_style="bold magenta")

        # columns to table
        for col in columns:
            table.add_column(col.capitalize(), max_width=30)

        # add rows to the table, replacing None values with an empty string
        for row in results:
            table.add_row(*[str(cell) if cell is not None else "" for cell in row])

        console.print(table)
