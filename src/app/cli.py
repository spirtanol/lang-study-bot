import typer

from app.console import chat

app = typer.Typer()
app.add_typer(chat.cli)


if __name__ == "__main__":
    app()
