from typing import Dict

from coin_data.requests import APIRequest


def get_bonding_curve(token: str, api_key: str):
    endpoint: str = "bonding_curve"
    headers: Dict[str, str] = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
    }

    params: Dict[str, str] = {
        "token": token,
    }

    api_request = APIRequest("rpc.api-pump.fun", use_ssl=True)
    response = api_request.get(endpoint=endpoint, headers=headers, params=params)

    if response.status_code == 200:
        return response.to_json()
    else:
        response.raise_for_status()


# Example usage:
# if __name__ == "__main__":
#     TOKEN: str = "your_token"
#     API_KEY: str = "your_api_key"
#     bonding_curve_data = get_bonding_curve(TOKEN, API_KEY)
#     print(bonding_curve_data)
