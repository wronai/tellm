import argparse
from tellm.server import TellmServer
from tellm.config import load_config
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--db", default="tellm.db")
    args = parser.parse_args()
    config = load_config()
    server = TellmServer(host=args.host or config.host, port=args.port or config.port, db_path=args.db)
    server.register_function("now", lambda p: print("Now:", p))
    server.register_function("cron", lambda p: print("Cron:", p))
    server.register_function("event", lambda p: print("Event:", p))
    server.run()
if __name__ == "__main__": main()