"""Define a custom Reasoning and Action agent for Amazon shopping.

Works with a chat model with tool calling support.
"""

from datetime import datetime, timezone
from typing import Dict, List, Literal, cast

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from react_agent.configuration import Configuration
from react_agent.state import InputState, State
from react_agent.amazon_connection.tool import AMAZON_TOOLS
from react_agent.utils import load_chat_model
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Define the function that calls the model
async def call_model(
    state: State, config: RunnableConfig
) -> Dict[str, List[AIMessage]]:
    """Call the LLM powering our "agent".

    This function prepares the prompt, initializes the model, and processes the response.

    Args:
        state (State): The current state of the conversation.
        config (RunnableConfig): Configuration for the model run.

    Returns:
        dict: A dictionary containing the model's response message.
    """
    try:
        # Create a new Configuration instance
        configuration = Configuration()

        # Add the configuration to the config dict so tools can access it
        if "configurable" not in config:
            config["configurable"] = {}
        config["configurable"].update({
            "model": configuration.model,
            "system_prompt": configuration.system_prompt,
            "max_search_results": configuration.max_search_results,
            # Set keep_browser_open to True for better performance in multi-step conversations
            "keep_browser_open": True
        })

        logger.info(f"Configuration loaded with model: {configuration.model}")

        # Initialize the model with tool binding
        model = load_chat_model(configuration.model).bind_tools(AMAZON_TOOLS)

        # Format the system prompt
        system_message = configuration.system_prompt.format(
            system_time=datetime.now(tz=timezone.utc).isoformat()
        )

        # Get the model's response
        response = cast(
            AIMessage,
            await model.ainvoke(
                [{"role": "system", "content": system_message}, *state.messages],
                config
            ),
        )

        # Handle the case when it's the last step and the model still wants to use a tool
        if state.is_last_step and response.tool_calls:
            return {
                "messages": [
                    AIMessage(
                        id=response.id,
                        content="Sorry, I could not complete your shopping request in the specified number of steps. Please try a more specific request.",
                    )
                ]
            }

        return {"messages": [response]}

    except Exception as e:
        logger.error(f"Error in call_model: {str(e)}")
        raise


# Define a new graph
builder = StateGraph(State, input=InputState, config_schema=Configuration)

# Create tool node with Amazon tools
tool_node = ToolNode(AMAZON_TOOLS)

# Add nodes to the graph
builder.add_node(call_model)
builder.add_node("tools", tool_node)

# Set the entrypoint
builder.add_edge("__start__", "call_model")


def route_model_output(state: State) -> Literal["__end__", "tools"]:
    """Determine the next node based on the model's output.

    This function checks if the model's last message contains tool calls.

    Args:
        state (State): The current state of the conversation.

    Returns:
        str: The name of the next node to call ("__end__" or "tools").
    """
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(
            f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
        )
    # If there is no tool call, then we finish
    if not last_message.tool_calls:
        return "__end__"
    # Otherwise we execute the requested actions
    return "tools"


# Add a conditional edge to determine the next step after `call_model`
builder.add_conditional_edges(
    "call_model",
    # After call_model finishes running, the next node(s) are scheduled
    # based on the output from route_model_output
    route_model_output,
)

# Add a normal edge from `tools` to `call_model`
# This creates a cycle: after using tools, we always return to the model
builder.add_edge("tools", "call_model")

# Compile the builder into an executable graph
graph = builder.compile(
    interrupt_before=[],
    interrupt_after=[],
)
graph.name = "Amazon Shopping Assistant"  # Custom name for LangSmith
