import argparse
import sqlite3
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend import vault


parser=argparse.ArgumentParser(description='Assign an Aegis local account role.')
parser.add_argument('username')
parser.add_argument('role',choices=('user','supervisor','administrator'))
parser.add_argument('--database',default='data/workbench.sqlite3')
args=parser.parse_args()

database=Path(args.database).resolve()
if not database.is_file():
    raise SystemExit(f'Database not found: {database}')
with (vault.database(database) if vault.enabled(database) else sqlite3.connect(database)) as con:
    columns={row[1] for row in con.execute('PRAGMA table_info(users)')}
    if 'role' not in columns:
        con.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
    row=con.execute('SELECT id,username,role FROM users WHERE lower(username)=lower(?)',(args.username,)).fetchone()
    if not row:
        raise SystemExit(f'User not found: {args.username}')
    con.execute('UPDATE users SET role=? WHERE id=?',(args.role,row[0]))
print(f'{row[1]}: {row[2]} -> {args.role}')
