# manage.py

import argparse
from app import init_db, load_voters_from_excel

def main():
    parser = argparse.ArgumentParser(description="Manage the Voting System")
    parser.add_argument('command', choices=['init_db', 'load_voters'], help="Command to run")
    parser.add_argument('--file', type=str, help="Path to Excel file for loading voters")

    args = parser.parse_args()

    if args.command == 'init_db':
        init_db()
        print('✅ Database initialized successfully.')

    elif args.command == 'load_voters':
        if not args
