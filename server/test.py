from tools.tavily_tool import search_tavily
from tools.flight_tool import search_flights
from app import run_travel_agent
#res = search_tavily("What is the best hotel in Mumbai?")
#print(res)
#res = search_flights("Plan a 7 days Newyork trip from Mumbai")
#print(res)

user_input = input("Enter your query: ")
res = run_travel_agent(user_input,thread_id="test_thread")
print("Final Response:\n")
print(res["answer"])