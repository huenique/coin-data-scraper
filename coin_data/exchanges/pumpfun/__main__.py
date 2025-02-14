import json

from coin_data.exchanges.pumpfun.parser import find_coin_info
from coin_data.exchanges.pumpfun.request import fetch_coin_data
from coin_data.exchanges.pumpfun.token_explorer import PumpfunTokenDataExplorer

if __name__ == "__main__":
    explorer = PumpfunTokenDataExplorer()
    csv_data = explorer.retrieve_token_activity()
    json_data = explorer.convert_csv_to_json(csv_data)

    mint_id = "61V8vBaqAGMpgDQi4JcAwo1dmBGHsyhzodcPqnEVpump"
    coin_data = fetch_coin_data(mint_id)
    coin_info = find_coin_info(coin_data)
    if coin_info:
        print(json.dumps(coin_info, indent=4))
