from database import Base, engine

# Run this file when DB has been changed & a new one needs to be implemented.

# Drop all tables
Base.metadata.drop_all(bind=engine)
print("✅ Dropped all tables")

# Recreate all tables
Base.metadata.create_all(bind=engine)
print("✅ Created all tables with new schema")