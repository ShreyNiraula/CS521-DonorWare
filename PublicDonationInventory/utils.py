from rich.console import Console
from rich.markup import escape
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
        console.print(f"[{color}]{escape(message)}[/{color}]")

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
        return console.input(f"[{color}]{escape(prompt_message)}: [/{color}]")

    @staticmethod
    def format_output_display(columns, results):
        """
        Formats the output of search and item list results in a interactive table format

        :param columns: List of columns used.
        :param results: Query result
        """
        table = Table(show_header=True, header_style="bold magenta")

        # skip columns that are empty for every row (common in cross-category views)
        keep = [
            i
            for i in range(len(columns))
            if any(i < len(row) and row[i] not in (None, "") for row in results)
        ]
        # a row can have more cells than named columns (e.g. a trailing user_name)
        extra = max((len(row) for row in results), default=0) - len(columns)
        keep += range(len(columns), len(columns) + max(extra, 0))

        for i in keep:
            name = columns[i] if i < len(columns) else "User"
            table.add_column(escape(str(name)).capitalize(), max_width=30)

        for row in results:
            table.add_row(
                *[
                    escape(str(row[i])) if i < len(row) and row[i] is not None else ""
                    for i in keep
                ]
            )

        console.print(table)
