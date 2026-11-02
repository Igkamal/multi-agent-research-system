
from agents import (
    build_reader_agent,
    build_search_agent,
    writer_chain,
    critic_chain,
)


def run_research_pipeline(topic: str) -> dict:
    state = {}

    # ==================================================
    # STEP 1: SEARCH AGENT
    # ==================================================
    print("\n" + "=" * 50)
    print("STEP 1 - Search Agent is working...")
    print("=" * 50)

    search_agent = build_search_agent()

    # Shorter prompt to reduce input token usage
    search_result = search_agent.invoke({
        "messages": [
            (
                "user",
                f"Research this topic: {topic}. "
                "Find 3 reliable sources. Return each source's "
                "title, URL, and a short relevant snippet. "
                "Keep the response concise. Do not invent facts."
            )
        ]
    })

    state["search_results"] = search_result["messages"][-1].content

    print("\nSEARCH RESULTS:\n")
    print(state["search_results"])

    # ==================================================
    # STEP 2: READER AGENT
    # ==================================================
    print("\n" + "=" * 50)
    print("STEP 2 - Reader Agent is scraping webpages...")
    print("=" * 50)

    reader_agent = build_reader_agent()

    # Pass only the search results needed by the Reader
    reader_result = reader_agent.invoke({
        "messages": [
            (
                "user",
                f"Topic: {topic}\n\n"
                f"Search results:\n{state['search_results']}\n\n"
                "Choose ONE relevant source from these results. "
                "Call scrape_url with its exact HTTP or HTTPS URL. "
                "Use the actual tool output as evidence. "
                "If scraping fails, clearly report the failure. "
                "Do not invent webpage content."
            )
        ]
    })

    # Print Reader messages for debugging
    print("\n--- READER AGENT DEBUG OUTPUT ---")

    for index, message in enumerate(reader_result["messages"]):
        print(f"\nMessage {index}")
        print("Type:", type(message).__name__)
        print("Content:", repr(message.content))

        tool_calls = getattr(message, "tool_calls", None)
        if tool_calls:
            print("Tool calls:", tool_calls)

    # Extract actual output from scrape_url
    scraped_outputs = []

    for message in reader_result["messages"]:
        message_type = getattr(message, "type", "")
        message_name = getattr(message, "name", "")

        if message_type == "tool" and message_name == "scrape_url":
            content = message.content

            if isinstance(content, str) and content.strip():
                scraped_outputs.append(content)

    if scraped_outputs:
        state["scraped_content"] = "\n\n".join(scraped_outputs)
    else:
        state["scraped_content"] = (
            "SCRAPING FAILED: No output was returned by scrape_url. "
            "Search snippets are not verified webpage content."
        )

    print("\nSCRAPED CONTENT:\n")
    print(state["scraped_content"])

    # ==================================================
    # STEP 3: WRITER
    # ==================================================
    print("\n" + "=" * 50)
    print("STEP 3 - Writer is drafting the report...")
    print("=" * 50)

    # Give the Writer the available evidence
    research_combined = (
        f"SEARCH RESULTS:\n{state['search_results']}\n\n"
        f"SCRAPED CONTENT:\n{state['scraped_content']}\n\n"
        "REPORTING RULES:\n"
        "- Distinguish search snippets from scraped content.\n"
        "- Do not invent facts, dates, statistics, or sources.\n"
        "- If scraping failed, disclose that limitation.\n"
        "- Include the source URLs found in the research.\n"
        "- Clearly identify claims that the evidence cannot verify.\n"
        "- Keep the report detailed but concise."
    )

    state["report"] = writer_chain.invoke({
        "topic": topic,
        "research": research_combined,
    })

    print("\nFINAL REPORT:\n")
    print(state["report"])

    # ==================================================
    # STEP 4: CRITIC
    # ==================================================
    print("\n" + "=" * 50)
    print("STEP 4 - Critic is reviewing the report...")
    print("=" * 50)

    state["feedback"] = critic_chain.invoke({
        "report": state["report"]
    })

    print("\nCRITIC REVIEW:\n")
    print(state["feedback"])

    return state


# ==================================================
# RUN THE PIPELINE
# ==================================================
if __name__ == "__main__":
    topic = input("\nEnter a research topic: ").strip()

    if topic:
        run_research_pipeline(topic)
    else:
        print("Please enter a research topic.")
