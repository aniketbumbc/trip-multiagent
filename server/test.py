from tools.tavily_tool import search_tavily
from tools.flight_tool import search_flights
#res = search_tavily("What is the best hotel in Mumbai?")
#print(res)
res = search_flights("Plan a 7 days Newyork trip from Mumbai")
print(res)