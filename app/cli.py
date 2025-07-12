import click
from flask.cli import with_appcontext
from .models import db, User

@click.command('seed')
@with_appcontext
def seed_command():
    """Seeds the database with initial data, like default admin users."""

    # Create default admin users if they don't exist
    admin_users = [
        {'username': 'john', 'email': 'john@admin.com', 'first_name': 'John', 'last_name': 'Admin'},
        {'username': 'kamila', 'email': 'kamila@admin.com', 'first_name': 'Kamila', 'last_name': 'Admin'}
    ]

    click.echo("Seeding database with default admin users...")

    for admin_data in admin_users:
        existing_user = User.query.filter_by(username=admin_data['username']).first()
        if not existing_user:
            admin_user = User(
                username=admin_data['username'],
                email=admin_data['email'],
                first_name=admin_data['first_name'],
                last_name=admin_data['last_name'],
                role='admin'
            )
            admin_user.set_password('Johnston')
            db.session.add(admin_user)
            click.echo(f"  -> Created admin user: {admin_user.username}")
        else:
            click.echo(f"  -> Admin user '{existing_user.username}' already exists. Skipping.")

    db.session.commit()
    click.echo("✅ Admin users seeded successfully.")

def init_app(app):
    """Register CLI commands with the Flask app."""
    app.cli.add_command(seed_command)
