

class TradeEngine:
    def __init__(self, capital:float, entry_price:float, rr_ratio:float, sl:float, symbol:str):
        self.capital = capital
        self.entry_price = entry_price
        self.rr_ratio = rr_ratio
        self.symbol = symbol
        self.volume = 0

        self.pips_value = 0


        self.stop_loss = 0
        self.take_profit = 0
        self.position = None
        self.status = "OPEN"
        self.result = None

        def risk_amount(self):
            return self.capital * self.rr_ratio
        
        def volume_size(self):
            return self.risk_amount() / (self.entry_price - self.stop_loss)