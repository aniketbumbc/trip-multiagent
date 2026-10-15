from tavily import TavilyClient
from dotenv import load_dotenv
import os

load_dotenv()

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

def search_tavily(query: str) -> str:
    response = client.search(query, max_results=3)
    results = []

    for i, r in enumerate(response["results"],1):
        title = r.get("title", "")
        url = r.get("url", "")
        description = r.get("description", "")
        snippet = r.get("content", "").strip()
        
        if len(snippet) > 300:
            snippet = snippet[:300].rsplit(" ", 1)[0] + "..."

        results.append(f"{i}. **{title}**   \n{description}\n{snippet}\n{url}")

    return "\n\n".join(results)



