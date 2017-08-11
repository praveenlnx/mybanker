from flask import current_app as app
from forex_python.converter import CurrencyRates, CurrencyCodes

# Get currency list
def getCurrencyList():
  c = CurrencyRates()
  currencies = []
  curRates = c.get_rates('GBP')
  for item in curRates.keys():
    currencies.append(item)
  currencies.append('GBP')
  return sorted(currencies)

# Get conversion rate
def getConversionRate(fromcur, tocur, amount):
  c = CurrencyRates()
  codes = CurrencyCodes()
  converted = c.convert(fromcur, tocur, amount)
  fromSymbol = codes.get_symbol(fromcur)
  toSymbol = codes.get_symbol(tocur)
  conversion_result = "%s %0.2f = %s %0.2f" % (fromSymbol, amount, toSymbol, converted)
  return conversion_result
