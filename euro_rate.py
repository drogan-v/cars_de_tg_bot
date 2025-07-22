import requests

class EuroRate:
    def __init__(self) -> None:
        self.url = "https://www.cbr-xml-daily.ru/daily_json.js"

    def euro_rate(self):
        response = requests.get(self.url)
        data = response.json()
        return data["Valute"]["EUR"]["Value"]

    def euro_to_rub(self, price: float) -> float:
        return price * self.euro_rate()


if __name__ == "__main__":
    e = EuroRate()
    print(e.euro_rate())