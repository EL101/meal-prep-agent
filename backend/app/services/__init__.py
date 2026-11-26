"""Business logic. Services use repositories, own transactions (commit), and know nothing
about HTTP. Routes call services; services never import from app.api."""
