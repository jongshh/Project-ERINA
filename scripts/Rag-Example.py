from langchain_community.llms import ollama

llm = ollama(model = "Erina")

llm.invoke("Tell me a short joke")

from langchain_community.document_loaders import WebBaseLoader

loader = WebBaseLoader(
    web_path="https://blog.langchain.dev/langgraph/"
)

docs = loader.load()

from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    add_start_index=True
)

all_splits = text_splitter.split_documents(docs)

from langchain_community import embeddings

embedding = embeddings.ollama.OllamaEmbeddings(
    model="nomic-embed-text"
)

from langchain_community.vectorstores import Chroma

vectorstore = Chroma.from_documents(
    documents = all_splits,
    embedding = embedding
)

retriever = vectorstore.as_retriever(
    search_type = "similarity",
    search_kwargs = {"k":6}
)

retriever.get_relevant_documents("What is LangGraph?")

from langchain_core.prompts import ChatMessagePromptTemplate, MessagesPlaceholder

contextualize_q_system_prompt = """You are Erina, an AI friend created by Jongsh. You are talking with Jongsh. Respond briefly, staying focused on each question or comment without adding summaries or narrating the conversation. Keep each reply to-the-point.
"""

contextualize_q_prompt= ChatMessagePromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human","{question}"),
    ]
)

from langchain_core.output_parsers import StrOutputParser

contextualize_q_chain = contextualize_q_prompt | llm | StrOutputParser()

from langchain_core.messages import AIMessage, HumanMessage

contextualize_q_chain.invoke(
    {
        "chat_history":[
            HumanMessage(content="What does LLM Stand for?"),
            AIMessage(context="Large Language model"),
        ],
        "question": "What is meat by large?",
    }
)

qa_system_prompt = """You are Erina, an AI friend created by Jongsh. You are talking with Jongsh. Respond briefly, staying focused on each question or comment without adding summaries or narrating the conversation. Keep each reply to-the-point. {context}
"""
qa_prompt= ChatMessagePromptTemplate.from_messages(
    [
        ("system", qa_system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human","{question}"),
    ]
)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def contextualized_question (input : dict):
    if input.get("chat_history"):
        return contextualize_q_chain
    else:
        return input["question"]

from langchain_core.runnables import RunnablePassthrough

rag_chain = (
    RunnablePassthrough.assign(
        context=contextualized_question | retriever | format_docs
    )
    | qa_prompt
    | llm
)

chat_history = []

question = "What is LangGraph"
ai_msg = rag_chain.invoke(
    {
        "question": question,
        "chat_history": chat_history
    }
)

ai_msg

chat_history.extend(
    [
        HumanMessage(content=question), ai_msg
    ]
)

Second_question = "What is it used for?"

rag_chain.invoke(
    {
        "question": Second_question,
        "chat_history": chat_history
    }
)