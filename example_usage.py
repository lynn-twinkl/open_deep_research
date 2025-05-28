import asyncio  
import uuid  
import os  
from langgraph.checkpoint.memory import MemorySaver  
from langgraph.types import Command  
from open_deep_research.graph import builder  
from dotenv import load_dotenv
load_dotenv()
  
async def conduct_deep_research(  
    topic: str,  
    search_api: str = "tavily",  
    planner_provider: str = "openai",   
    planner_model: str = "o4-mini",  
    writer_provider: str = "openai",  
    writer_model: str = "gpt-4.1-mini",  
    max_search_depth: int = 2,  
    report_structure: str = None,  
    feedback_on_plan: str = None,  
    auto_approve: bool = False  
):  
    """  
    Conduct automated deep research on a given topic.  
      
    Args:  
        topic: The research topic  
        search_api: Search API to use (tavily, perplexity, exa, etc.)  
        planner_provider: LLM provider for planning  
        planner_model: Specific model for planning  
        writer_provider: LLM provider for writing  
        writer_model: Specific model for writing  
        max_search_depth: Maximum research iterations per section  
        report_structure: Custom report structure (optional)  
        feedback_on_plan: Feedback to provide on the initial plan (optional)  
        auto_approve: Whether to automatically approve the plan  
          
    Returns:  
        str: The final research report  
    """  
      
    # Set up the graph with memory  
    memory = MemorySaver()  
    graph = builder.compile(checkpointer=memory)  
      
    # Configure the research thread  
    thread_config = {  
        "configurable": {  
            "thread_id": str(uuid.uuid4()),  
            "search_api": search_api,  
            "planner_provider": planner_provider,  
            "planner_model": planner_model,  
            "writer_provider": writer_provider,  
            "writer_model": writer_model,  
            "max_search_depth": max_search_depth,  
        }  
    }  
      
    # Add custom report structure if provided  
    if report_structure:  
        thread_config["configurable"]["report_structure"] = report_structure  
      
    print(f"Starting research on: {topic}")  
      
    # Step 1: Generate initial report plan  
    print("Generating report plan...")  
    plan_generated = False  
    async for event in graph.astream({"topic": topic}, thread_config, stream_mode="updates"):  
        if '__interrupt__' in event:  
            interrupt_value = event['__interrupt__'][0].value  
            print("\n" + "="*50)  
            print("REPORT PLAN GENERATED")  
            print("="*50)  
            print(interrupt_value)  
            plan_generated = True  
            break  
      
    if not plan_generated:  
        raise Exception("Failed to generate report plan")  
      
    # Step 2: Handle feedback or approval  
    if feedback_on_plan and not auto_approve:  
        print(f"\nProviding feedback: {feedback_on_plan}")  
        async for event in graph.astream(  
            Command(resume=feedback_on_plan),   
            thread_config,   
            stream_mode="updates"  
        ):  
            if '__interrupt__' in event:  
                interrupt_value = event['__interrupt__'][0].value  
                print("\n" + "="*50)  
                print("UPDATED REPORT PLAN")  
                print("="*50)  
                print(interrupt_value)  
                break  
      
    # Step 3: Approve the plan and generate the report  
    print("\nApproving plan and starting research...")  
    async for event in graph.astream(  
        Command(resume=True),   
        thread_config,   
        stream_mode="updates"  
    ):  
        # Print progress updates  
        if event and not '__interrupt__' in event:  
            for node_name, node_data in event.items():  
                if node_name != '__metadata__':  
                    print(f"Processing: {node_name}")  
      
    # Step 4: Get the final report  
    final_state = graph.get_state(thread_config)  
    final_report = final_state.values.get('final_report')  
      
    if not final_report:  
        raise Exception("Failed to generate final report")  
      
    print("\n" + "="*50)  
    print("RESEARCH COMPLETE")  
    print("="*50)  
      
    return final_report  
  
# Example usage function  
async def main():  
    """Example of how to use the research function"""  
      
    # Set required API keys (you'll need these)  
    required_keys = ["TAVILY_API_KEY", "OPENAI_API_KEY"]  
    for key in required_keys:  
        if not os.getenv(key):  
            print(f"Warning: {key} not set")  
      
    # Example 1: Basic research  
    topic = "Overview of the AI inference market with focus on Fireworks, Together.ai, Groq"  
      
    try:  
        report = await conduct_deep_research(  
            topic=topic,  
            search_api="tavily",  
            max_search_depth=1,  
            auto_approve=True  # Skip human feedback for automation  
        )  
          
        print(f"\nFinal Report Length: {len(report)} characters")  
        print("\nFirst 500 characters of report:")  
        print(report[:500] + "...")  
          
        # Save to file  
        with open("research_report.md", "w") as f:  
            f.write(report)  
        print("\nReport saved to research_report.md")  
          
    except Exception as e:  
        print(f"Research failed: {e}")  
  
# Run the example  
if __name__ == "__main__":  
    asyncio.run(main())
