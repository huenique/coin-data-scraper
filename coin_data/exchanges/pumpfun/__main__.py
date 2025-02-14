from coin_data.exchanges.pumpfun.parser import find_coin_info
from coin_data.exchanges.pumpfun.request import fetch_coin_data
from coin_data.exchanges.pumpfun.token_explorer import PumpfunTokenDataExplorer

if __name__ == "__main__":
    explorer = PumpfunTokenDataExplorer()
    csv_data = explorer.retrieve_token_activity()
    json_data = explorer.convert_csv_to_dict(csv_data)

    for token in json_data:
        coin_data = fetch_coin_data(token.token_address)
        coin_info = find_coin_info(coin_data)
        print(coin_info.__dict__)
