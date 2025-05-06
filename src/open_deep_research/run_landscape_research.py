import uuid 
import os, getpass
import asyncio
import open_deep_research   
from IPython.display import Image, display, Markdown
from langgraph.types import Command
from langgraph.checkpoint.memory import MemorySaver
from open_deep_research.graph import builder
from dotenv import load_dotenv

load_dotenv()

## -------------- MEMORY AND STATE ------------

# Create a memory-based checkpointer and compile the graph
# This enables state persistence and tracking throughout the workflow execution

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

## -------------- ENV VALIDATION ------------

# Helper function to set environment variables for API keys
# This ensures all necessary credentials are available for various services
def set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

set_env("OPENAI_API_KEY")
set_env("ANTHROPIC_API_KEY")
set_env("TAVILY_API_KEY")
set_env("GROQ_API_KEY")
set_env("PERPLEXITY_API_KEY")

################################
# RESEARCH PARAMETERS
################################

REPORT_STRUCTURE = """
Your goal is to conduct research on the EDU landscape for a given state and topics. When prompted to conduct research and write a report you must ensure you use this structure:
---
# Weekly K-12 Educational Development Digest**
## TEXAS EDUCATIONAL DEVELOPMENTS
## SIGNIFICANT SHIFTS
- Output the 5 most important points regarding key policy/legislative changes, new state initiatives, or major trend shifts in Texas education. Use no more than 16 words per point.
## ACCOLADES
- Output the 5 most important points regarding notable recognition or positive achievements within Texas education. Use no more than 16 words per point. 
## CONTROVERSIES
- Output the 5 most important points regarding significant debates, conflicts, or legal challenges in Texas education. Use no more than 16 words per point.
---
Repeat the structure above for each state.
"""

# ---------------- AGENT & RESEARCH CONFIGURATION -----------------

thread = {"configurable": {"thread_id": str(uuid.uuid4()),
                           "search_api": "tavily",
                           "planner_provider": "openai",
                           "planner_model": "o3",
                           "writer_provider": "openai",
                           "writer_model": "o3",
                           "max_search_depth": 3,
                           "report_structure": REPORT_STRUCTURE,
                           }}

# Define research topic about K-12 education
topic = "Conduct research on K-12 education in Texas and Florida for the last week of April 2025. Identify significant policy shifts, notable accolades, key controversies, and movements by digital/edtech resource providers. Focus on gathering information relevant for strategic decision-making purposes"

# ---------------- RESEARCH FUNCTIONS -----------------

# Function to conduct superficial research to determine structure.
## While we won't be using HITL, this is still useful for validating that the REPORT_STRUCTURE is being used.

async def run_research():
    print("Running preliminary research...")
    async for event in graph.astream({"topic": topic}, thread, stream_mode="updates"):
        if '__interrupt__' in event:
            interrupt_value = event['__interrupt__'][0].value
            print(interrupt_value)
    print("Research workflow completed.")


    # Automatically approve the final plan and execute the report generation. We skip the feddback submission part.
    # The system will now initiate deep research.

    print("Running deep research...")
    async for event in graph.astream(Command(resume=True), thread, stream_mode="updates"):
        print(event)
        print("\n")

    final_state = graph.get_state(thread)
    report_content = final_state.values.get('final_report')

    if report_content:
        with open('../../../final_report.md', 'w') as report_file:
            report_file.write(report_content)
        print("Report succesffully saved!")
    else:
        print("Error: No report content found in final_state")



## ------ USAGE ------
if __name__ == "__main__":
    print(f"Using open_deep_research version: {open_deep_research.__version__}")
    asyncio.run(run_research())
