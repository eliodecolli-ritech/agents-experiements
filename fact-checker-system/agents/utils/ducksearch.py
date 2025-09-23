from ddgs import DDGS
from typing import List, Dict
import time
import random


class DuckSearch:
    def __init__(self):
        self.ddgs = DDGS()

    def search(self, query: str, num_results: int = 10) -> List[Dict[str, str]]:
        """
        Search DuckDuckGo for the given query and return results with title and URL.

        Args:
            query: The search query string
            num_results: Maximum number of results to return (default: 10)

        Returns:
            List of dictionaries with 'title' and 'url' keys
        """
        try:
            # Add random delay to be respectful
            time.sleep(random.uniform(0.5, 1.5))

            # Perform the search
            results = []
            search_results = self.ddgs.text(
                query=query,
                max_results=num_results,
            )

            for result in search_results:
                if 'title' in result and 'href' in result:
                    results.append({
                        'title': result['title'].strip(),
                        'url': result['href']
                    })

            return results

        except Exception as e:
            print(f"Error searching DuckDuckGo: {e}")
            return []

    def search_news(self, query: str, num_results: int = 10) -> List[Dict[str, str]]:
        """
        Search DuckDuckGo News for the given query.

        Args:
            query: The search query string
            num_results: Maximum number of results to return (default: 10)

        Returns:
            List of dictionaries with 'title' and 'url' keys
        """
        try:
            time.sleep(random.uniform(0.5, 1.5))

            results = []
            news_results = self.ddgs.news(
                keywords=query,
                max_results=num_results,
                safesearch='moderate'
            )

            for result in news_results:
                if 'title' in result and 'url' in result:
                    results.append({
                        'title': result['title'].strip(),
                        'url': result['url']
                    })

            return results

        except Exception as e:
            print(f"Error searching DuckDuckGo News: {e}")
            return []