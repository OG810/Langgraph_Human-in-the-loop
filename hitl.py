"""
here  to implement HITL we introduce the concept of interrupt in the flow of the graph. 
HITL ke liye check point use krna is extremely useful bcoz , during interrupt of hitl , the workflow of the graph stops, so when it stopswe need to store its state somewhere ,
so we will use in memory saver. 


"""

########################################################################
from typing import Annotated

from langchain_openai import ChatOpenAI
from langchain_core.messages import AnyMessage, AIMessage

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from dotenv import load_dotenv
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
########################################################################
load_dotenv()

########################################################################

llm = ChatOpenAI(model="gpt-4.1-mini")

########################################################################

from langgraph.graph.message import add_messages

class ChatState(TypedDict):

    messages: Annotated[list[BaseMessage], add_messages]

########################################################################

def chat_node(state: ChatState):

    decision = interrupt({
        "type": "approval",
        "reason": "Model is about to answer a user question.",
        "question": state["messages"][-1].content,
        "instruction": "Approve this question? yes/no"
    })
    
    if decision["approved"] == 'no':
        return {"messages": [AIMessage(content="Not approved.")]}

    else:
        response = llm.invoke(state["messages"])
        return {"messages": [response]}
########################################################################

# 3. Build the graph: START -> chat -> END
builder = StateGraph(ChatState)

builder.add_node("chat", chat_node)

builder.add_edge(START, "chat")
builder.add_edge("chat", END)

# Checkpointer is required for interrupts
checkpointer = MemorySaver()

# Compile the app
app = builder.compile(checkpointer=checkpointer)

########################################################################

app

########################################################################

# Create a new thread id for this conversation
config = {"configurable": {"thread_id": '1234'}}

# ---- STEP 1: user asks a question ----
initial_input = {
    "messages": [
        ("user", "Explain gradient descent in very simple terms.")
    ]
}

# Invoke the graph for the first time
result = app.invoke(initial_input, config=config)
########################################################################
result

########################################################################
message = result['__interrupt__'][0].value
message

########################################################################

user_input = input(f"\nBackend message - {message} \n Approve this question? (y/n): ")
########################################################################

# Resume the graph with the approval decision
final_result = app.invoke(
    Command(resume={"approved": user_input}),
    config=config,
)
########################################################################

print(final_result["messages"][-1].content)
########################################################################


########################################################################
