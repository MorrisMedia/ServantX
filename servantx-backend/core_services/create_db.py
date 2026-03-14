#!/usr/bin/env python3
"""
Database Creation Script

Creates the database if it doesn't exist.
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

load_dotenv()

def create_db():
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        print('❌ Error: DATABASE_URL environment variable is not set')
        return
    
    db_name = db_url.split('/')[-1]
    
    if 'postgresql+asyncpg://' in db_url:
        url_without_protocol = db_url.replace('postgresql+asyncpg://', '')
    elif 'postgresql://' in db_url:
        url_without_protocol = db_url.replace('postgresql://', '')
    else:
        url_without_protocol = db_url
    
    parts = url_without_protocol.split('/')
    conn_part = parts[0]
    user_pass, host_port = conn_part.split('@')
    user, password = user_pass.split(':')
    host, port = host_port.split(':')
    
    conn_string = f"host={host} port={port} user={user} password={password} dbname=postgres"
    
    try:
        conn = psycopg2.connect(conn_string)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        db_exists = cursor.fetchone() is not None
        
        if not db_exists:
            print(f'📦 Creating database {db_name}...')
            cursor.execute(f'CREATE DATABASE "{db_name}"')
            print(f'✅ Database {db_name} created successfully!')
        else:
            print(f'✅ Database {db_name} already exists!')
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f'❌ Error creating database: {e}')

if __name__ == "__main__":
    create_db()
