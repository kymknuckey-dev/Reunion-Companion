from pathlib import Path
import argparse
from .beta_ui import run_ui
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--db",default=str(Path.home()/".reunion-companion"/"companion.sqlite3"))
    p.add_argument("--host",default="127.0.0.1");p.add_argument("--port",type=int,default=8765);p.add_argument("--no-browser",action="store_true")
    a=p.parse_args();run_ui(a.db,a.host,a.port,not a.no_browser)
if __name__=="__main__":main()
