

from typing import TypedDict,Annotated
import operator
from langchain_core.messages import AnyMessage

class TravelState(TypedDict):
    messages:Annotated[list[AnyMessage],operator.add] #reducer object to append messages to the list
    user_query:str #user query
    flight_results:str #flight results
    hotel_results:str #hotel results
    itinerary:str #itinerary
    llm_calls:int #number of LLM calls