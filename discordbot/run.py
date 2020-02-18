from titanembeds import Titan
from config import config

import argparse
import gc
import requests

def print_shards():
    token = config["bot-token"]
    url = "https://discordapp.com/api/v6/gateway/bot"
    headers = {"Authorization": "Bot {}".format(token)}
    r = requests.get(url, headers=headers)
    if r.status_code >= 200 and r.status_code < 300:
        print("Suggested number of shards: {}".format(r.json().get("shards", 0)))
    else:
        print("Status Code: {}".format(r.status_code))
        print(r.text)

def main():
    parser = argparse.ArgumentParser(
        description="Embed Discord like a True Titan (Discord Bot portion)"
    )
    parser.add_argument(
        "-sid",
        "--shard_id",
        help="ID of the shard",
        type=int,
        default=None
    )
    parser.add_argument(
        "-sc",
        "--shard_count",
        help="Number of total shards",
        type=int,
        default=None
    )
    parser.add_argument(
        "-s",
        "--shards",
        help="Prints the reccomended number of shards to spawn",
        action="store_true"
    )
    args = parser.parse_args()

    if args.shards:
        print_shards()
        return

    print("Starting...")
    te = Titan(
        shard_ids = [args.shard_id] if args.shard_id is not None else None,
        shard_count = args.shard_count
    )
    te.run()
    gc.collect()

if __name__ == '__main__':
    main()
