"""
Purpose:
This file manually tests the Gemini news analysis service.

It sends a sample news article to Gemini and displays the
generated summary, key takeaways, category, and sentiment.
"""

from pprint import pprint

from app.services.gemini_service import generate_news_summary


def main():
    title = "Artificial intelligence is changing software development"

    content = """
    Artificial intelligence tools are increasingly being adopted
    by software developers. These tools help developers generate code,
    identify bugs, write tests, and understand complex codebases.
    Companies are exploring ways to integrate AI into their
    development workflows while maintaining code quality and security.
    """

    result = generate_news_summary(
        title=title,
        content=content,
    )

    print("\nGEMINI NEWS ANALYSIS")
    print("=" * 50)

    pprint(result)


if __name__ == "__main__":
    main()
