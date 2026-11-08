import re
from datetime import datetime
from typing import Dict, Optional, Sequence, Tuple

from rich import box
from rich.align import Align
from rich.cells import cell_len
from rich.columns import Columns
from rich.console import Console, Group
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

MAX_WIDTH = 78

TAG_STYLES = {
    "success": ("✔", "bold green"),
    "error": ("✖", "bold red"),
    "info": ("•", "cyan"),
    "prompt": ("›", "bold yellow"),
}

CATEGORY_ICONS = {
    "book": "📚",
    "magazine": "📰",
    "journal": "📓",
    "manga": "🎌",
    "western_comic": "💥",
    "research_paper": "🔬",
}

# borrow history views only show what identifies the loan, to keep the table readable
HISTORY_COLUMNS = {
    "category", "transactionid", "name", "borrow_date", "due_date", "return_date", "status",
}
NO_WRAP_COLUMNS = {"category", "id", "transactionid", "status"}

BANNER_COLORS = ((0, 215, 255), (176, 96, 255))  # cyan -> violet


def _gradient(text: str, start: Tuple[int, int, int], end: Tuple[int, int, int]) -> Text:
    """
    Colors each character of text along a linear RGB gradient.
    """
    result = Text()
    last = max(len(text) - 1, 1)
    for i, char in enumerate(text):
        rgb = tuple(round(s + (e - s) * i / last) for s, e in zip(start, end))
        result.append(char, style=f"bold rgb({rgb[0]},{rgb[1]},{rgb[2]})")
    return result


def _width() -> int:
    return min(console.width, MAX_WIDTH)


class Utils:
    @staticmethod
    def rich_print(message: str, tag: str = "info") -> None:
        """
        Prints messages with color coding and an icon based on the tag (success, error, info, prompt)

        :param message: The message to display.
        :param tag: The type of message - 'success', 'error', 'info', & 'prompt'
        """
        icon, style = TAG_STYLES.get(tag, TAG_STYLES["info"])
        # keep leading blank lines outside the icon line
        stripped = message.lstrip("\n")
        console.print("\n" * (len(message) - len(stripped)), end="")
        console.print(Text(f"{icon} {stripped.rstrip()}", style=style))

    @staticmethod
    def rich_prompting(prompt_message: str, tag: str = "info", password: bool = False) -> str:
        """
        Prompts the user for input with color scheme based on tag

        :param prompt_message: The prompt to display.
        :param tag: The type of message - 'success', 'error', 'info', & 'prompt'
        :param password: Hide the typed characters.
        :return: The user's input as a string.
        """
        _, style = TAG_STYLES.get(tag, TAG_STYLES["info"])
        return console.input(
            Text.assemble(("❯ ", "bold magenta"), (prompt_message, style), (": ", "dim")),
            password=password,
        )

    @staticmethod
    def status(message: str):
        """
        Context manager that shows a spinner while a slow step runs.
        """
        return console.status(f"[cyan]{escape(message)}[/cyan]", spinner="dots")

    @staticmethod
    def show_banner() -> None:
        """
        Prints the application banner.
        """
        title = _gradient("D O N O R W A R E", *BANNER_COLORS)
        body = Group(
            Align.center(Text("📚  ✦  📖  ✦  📰  ✦  📓  ✦  🎌  ✦  🔬")),
            Align.center(title),
            Align.center(Text("share what you've read, borrow what you'll love", style="italic dim")),
        )
        console.print()
        console.print(
            Panel(body, box=box.DOUBLE, border_style="bright_blue", padding=(1, 2), width=_width())
        )

    @staticmethod
    def show_menu(title: str, options: Sequence[Tuple[str, str]], subtitle: Optional[str] = None) -> None:
        """
        Prints a numbered menu inside a panel.

        :param title: Heading shown on the panel border.
        :param options: (key, label) pairs.
        :param subtitle: Optional text shown on the bottom border.
        """
        grid = Table.grid(padding=(0, 2))
        grid.add_column(justify="right", style="bold bright_magenta")
        grid.add_column()
        for key, label in options:
            grid.add_row(f"{key}", Text(label))
        console.print(
            Panel(
                grid,
                title=f"[bold bright_cyan]{escape(title)}[/]",
                subtitle=f"[dim]{escape(subtitle)}[/]" if subtitle else None,
                box=box.ROUNDED,
                border_style="bright_blue",
                padding=(1, 3),
                width=_width(),
            )
        )

    @staticmethod
    def show_dashboard(user_name: str, stats: Dict[str, int]) -> None:
        """
        Prints a row of stat cards for the logged in user.

        :param user_name: The user the stats belong to.
        :param stats: Counts for 'donated', 'borrowing', 'overdue' and 'returned'.
        """
        overdue = stats.get("overdue", 0)
        cards = [
            ("Donated", stats.get("donated", 0), "bright_green"),
            ("Borrowing", stats.get("borrowing", 0), "bright_yellow"),
            ("Overdue", overdue, "bold red" if overdue else "dim"),
            ("Returned", stats.get("returned", 0), "bright_cyan"),
        ]
        panels = [
            Panel(
                Align.center(Text(str(count), style=f"bold {style}")),
                title=label,
                box=box.ROUNDED,
                border_style=style,
                width=17,
            )
            for label, count, style in cards
        ]
        console.print()
        console.print(
            Panel(
                Columns(panels, align="center", expand=True),
                title=f"[bold bright_cyan]👤 {escape(user_name)}[/]",
                box=box.ROUNDED,
                border_style="bright_blue",
                width=_width(),
            )
        )
        if overdue:
            Utils.rich_print(
                f"You have {overdue} overdue item(s). Please return them soon.", tag="error"
            )

    @staticmethod
    def format_output_display(columns, results, title: Optional[str] = None):
        """
        Formats the output of search and item list results in a interactive table format

        :param columns: List of columns used.
        :param results: Query result
        :param title: Optional heading for the table.
        """
        table = Table(
            title=Text(title, style="bold bright_cyan") if title else None,
            box=box.ROUNDED,
            header_style="bold bright_magenta",
            border_style="bright_blue",
            row_styles=["", "on grey11"],
            show_lines=False,
        )

        names = [_pretty_name(c) for c in columns]
        lowered = [str(c).lower() for c in columns]

        is_history = "transactionid" in lowered and "status" in lowered

        # skip columns that are empty for every row (common in cross-category views),
        # and the user_name column, which is always the logged in user in these views
        keep = [
            i
            for i in range(len(columns))
            if lowered[i] != "user_name"
            and (not is_history or lowered[i] in HISTORY_COLUMNS)
            and any(i < len(row) and row[i] not in (None, "") for row in results)
        ]
        # a row can have more cells than named columns (e.g. a trailing donor name)
        extra = max((len(row) for row in results), default=0) - len(columns)
        keep += range(len(columns), len(columns) + max(extra, 0))

        status_idx = lowered.index("status") if "status" in lowered else None
        today = datetime.now().strftime("%Y-%m-%d")

        body = []
        for row in results:
            is_active = status_idx is None or (
                status_idx < len(row) and row[status_idx] == "borrowed"
            )
            body.append(
                [
                    _style_cell(
                        lowered[i] if i < len(lowered) else "",
                        row[i] if i < len(row) else None,
                        today,
                        is_active,
                    )
                    for i in keep
                ]
            )

        for pos, i in enumerate(keep):
            name = names[i] if i < len(names) else "Donor"
            column = lowered[i] if i < len(lowered) else ""
            if column in NO_WRAP_COLUMNS or column.endswith("date"):
                # fixed columns take exactly their content width; text columns absorb the shrinking
                width = max([cell_len(name)] + [cell_len(r[pos].plain) for r in body])
                table.add_column(name, no_wrap=True, min_width=width)
            else:
                table.add_column(name, max_width=30, overflow="fold")

        for cells in body:
            table.add_row(*cells)

        console.print()
        console.print(table)
        console.print(Text(f"{len(results)} row(s)", style="dim"), justify="right")


def _pretty_name(column) -> str:
    """
    Turns a column key such as 'TransactionId' or 'user_name' into a readable header.
    """
    if str(column).lower() == "transactionid":
        return "Txn"
    if str(column).lower() == "id":
        return "ID"
    spaced = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", str(column)).replace("_", " ")
    return spaced.title()


def _style_cell(column: str, value, today: str, is_active: bool) -> Text:
    """
    Builds a table cell. Text is used instead of a string so user data is never read as markup.
    """
    if value is None or value == "":
        return Text("")
    text = str(value)
    if column == "category":
        icon = CATEGORY_ICONS.get(text, "•")
        return Text(f"{icon} {text.replace('_', ' ')}", style="cyan")
    if column in ("id", "transactionid"):
        return Text(text, style="bold bright_magenta")
    if column == "name":
        return Text(text, style="bold")
    if column == "status":
        return Text(text, style="yellow" if text == "borrowed" else "green")
    if column == "due_date" and is_active and text < today:
        return Text(f"{text} ⚠", style="bold red")
    return Text(text)
