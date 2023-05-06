from textual.app import App, ComposeResult
from textual.widgets import Static, DataTable, Input, TextLog

from rich.table import Table
from rich.syntax import Syntax
from textual import events
from itertools import cycle
import csv
import io

ROWS = [
    ("time", "action", "amount", "price", "total"),
    ("10:15:20", "buy", "100", "0.0032", "0.321"),
    ("11:20:30", "sell", "50", "0.004", "0.199"),
    ("12:35:40", "buy", "200", "0.0035", "0.702"),
    ("13:45:50", "sell", "75", "0.0038", "0.278"),
    ("14:50:10", "buy", "150", "0.0037", "0.557"),
    ("15:55:20", "sell", "100", "0.0039", "0.388"),
    ("16:59:40", "sell", "80", "0.0041", "0.319"),
    ("18:02:50", "buy", "120", "0.0036", "0.434"),
    ("19:10:10", "sell", "60", "0.0043", "0.253"),
    ("20:15:30", "buy", "250", "0.0034", "0.859"),
    ("21:20:40", "sell", "120", "0.0042", "0.502"),
    ("22:25:50", "buy", "50", "0.0038", "0.195"),
    ("23:30:10", "sell", "200", "0.004", "0.799"),
    ("00:35:20", "buy", "180", "0.0036", "0.651"),
    ("01:40:30", "sell", "90", "0.0039", "0.347"),
    ("02:45:40", "buy", "100", "0.0037", "0.377"),
    ("03:50:50", "sell", "50", "0.004", "0.199"),
    ("04:55:10", "buy", "150", "0.0038", "0.557"),
    ("06:00:20", "sell", "75", "0.0041", "0.304"),
    ("07:05:30", "buy", "200", "0.0035", "0.702"),
]


class GridLayoutExample(App):
    CSS_PATH = "ui.css"

    def compose(self) -> ComposeResult:
        yield Static("Chart [b](WETH/PEPE)", classes="box", id="chart")
        #yield Static("Trades", classes="box", id="trades")
        yield DataTable(classes="box", id="trades", )
        #yield Static(">> cli", classes="box", id="cli")
        yield TextLog(classes="box", id="cli")
        yield Static("gas", classes="box", id="gas")
        yield Input(placeholder="twap", classes="box", id="input")



    def on_mount(self) -> None:

        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.column_widths=[10, 5, 10, 40, 10]
        table.zebra_stripes = True
        table.add_columns(*ROWS[0])
        table.add_rows(ROWS[1:])

    def on_key(self, event: events.Key) -> None:
        """Write Key events to log."""
        text_log = self.query_one(TextLog)
        if event.is_printable:
            #text_log.write(event.key)
            pass
        text_log.write(event)
app = GridLayoutExample()
if __name__ == "__main__":
    app.run()
