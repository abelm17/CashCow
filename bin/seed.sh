#!/bin/bash

set -e

echo "Creating database tables..."
python -m scripts.create_tables

echo "Seeding database..."
python -m scripts.seed

echo "Database setup complete!"
