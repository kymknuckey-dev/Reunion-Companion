from pathlib import Path
from .shell import run
import argparse

def main():
 p=argparse.ArgumentParser();p.add_argument("--db",default=str(Path.home()/".reunion-companion"/"companion.sqlite3"));a=p.parse_args();run(a.db)

if __name__=="__main__": main()
