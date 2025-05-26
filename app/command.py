import click
from flask.cli import with_appcontext
from app import app, db


@click.command("reset-db-data")
@with_appcontext
def reset_db_data_command():
    """Clears all data from the database tables."""
    if click.confirm(
        "Are you sure you want to delete all data from all tables? This cannot be undone.",
        abort=True,
    ):
        # Ensure all your models are imported here so SQLAlchemy metadata is populated
        # e.g., from . import models
        meta = db.metadata
        session = db.session
        try:
            for table in reversed(meta.sorted_tables):
                click.echo(f"Clearing data from table: {table.name}")
                session.execute(table.delete())
            session.commit()
            click.echo("All data cleared successfully.")
        except Exception as e:
            session.rollback()
            click.echo(f"Error clearing data: {e}", err=True)
            raise
        finally:
            session.close()


with app.app_context():
    app.cli.add_command(reset_db_data_command)
