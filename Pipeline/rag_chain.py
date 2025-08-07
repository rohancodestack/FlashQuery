import os
import re
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.schema.runnable import RunnableMap
from langchain.tools import Tool
from langchain_community.utilities import SerpAPIWrapper

# ✅ Load .env variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

# ✅ Setup SerpAPI Wrapper
search = SerpAPIWrapper(
    serpapi_api_key=SERPAPI_API_KEY,
    params={"num": 3, "hl": "en", "gl": "us", "timeout": 3}
)

search_tool = Tool.from_function(
    func=search.run,
    name="search",
    description="Search the web for current or real-time information like latest news, stats, updates, etc."
)

class RAGChainWithContext:
    def __init__(self):
        self.pdf_context = ""
        self.memory = ConversationBufferMemory(memory_key="history", return_messages=True)

        # ✅ Chat Prompt Template
        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You're FlashQuery, a helpful AI assistant. Answer clearly and concisely. "
                "If it's a math problem, solve step-by-step. If it's a writing question, keep it polite. "
                "Use PDF context if provided. Use web data carefully. Provide structured steps if user asks how/why/guide."
            ),
            ("human", "{input}")
        ])

        # ✅ Load LLM with Groq
        self.llm = ChatGroq(model="llama3-8b-8192", api_key=GROQ_API_KEY)
        self.chain = self.prompt | self.llm

        self.wrapped_chain = RunnableMap({
            "output": lambda x: self._invoke_chain(x["input"])
        })

    def _invoke_chain(self, prompt: str) -> str:
        try:
            print("[📤 Prompt sent to LLM]:", prompt)
            result = self.chain.invoke({"input": prompt})
            return result.content.strip() if hasattr(result, "content") else str(result).strip()
        except Exception as e:
            print(f"[❌ Error in _invoke_chain]: {str(e)}")
            return "⚠️ Sorry, I couldn't generate a proper response right now."

    def is_pdf_related(self, question: str) -> bool:
        q = question.lower()
        return any(k in q for k in [
            "in the pdf", "according to the document", "based on the file",
            "from the report", "this document", "in this file", "from uploaded", "as per the pdf"
        ])

    def should_use_serpapi(self, question: str) -> bool:
        q = question.lower()
        if any(k in q for k in ["latest", "current", "today", "now", "recent", "trending", "live", "news"]):
            return True
        if q.startswith(("who is", "what is", "when is", "how many", "how much", "where is")) and len(q.split()) <= 12:
            return True
        return False

    def is_grammar_or_intro_query(self, question: str) -> bool:
        q = question.lower()
        return any(k in q for k in [
            "say on the phone", "how to say", "what's better", "is it okay to say",
            "polite way", "this is rohan", "how should i introduce"
        ])

    def clean_serp_output(self, raw, question: str = "") -> str:
        if isinstance(raw, list):
            raw = " ".join([str(item) for item in raw])
        elif not isinstance(raw, str):
            raw = str(raw)

        raw = re.sub(r"[\[\]\"']", "", raw)
        sentences = re.split(r'(?<=[.?!])\s+|\n', raw)
        seen, filtered = set(), []

        for sent in sentences:
            clean = sent.strip()
            if clean and clean not in seen and len(clean.split()) > 4:
                seen.add(clean)
                filtered.append(clean)

        step_pattern = re.compile(r"^\s*\d+\.")
        steps = [s for s in filtered if step_pattern.match(s)]
        if len(steps) >= 3:
            return " ".join(steps[:5]).strip() + " ✅"

        question_keywords = re.findall(r"\b[a-zA-Z]{4,}\b", question.lower())
        for sentence in filtered:
            if any(qk in sentence.lower() for qk in question_keywords):
                return sentence.strip() + " ✅"

        return filtered[0].strip() + " ✅" if filtered else "⚠️ No meaningful answer found."

    def run(self, question: str, context: str = None) -> str:
        if context:
            self.pdf_context = context.strip()

        print("[🧠 Incoming Question]:", question)

        if self.pdf_context and self.is_pdf_related(question):
            print("[📄 Using PDF Context]")
            prompt = f"{self.pdf_context[:1500]}\n\nQuestion: {question}"
            return self._invoke_chain(prompt)

        if self.is_grammar_or_intro_query(question):
            print("[✍️ Detected Grammar/Intro Query → LLM Preferred]")
            return self._invoke_chain(question)

        if self.should_use_serpapi(question):
            try:
                serp_result = search_tool.run(question)
                if serp_result:
                    print("[🌐 Real-Time Web Search Triggered]")
                    print(f"[🔎 SerpAPI Result]: {serp_result}")
                    return self.clean_serp_output(serp_result, question)
            except Exception as e:
                print(f"[❌ SerpAPI Fallback Error]: {str(e)}")

        print("[💬 Falling Back to LLM]")
        return self._invoke_chain(question)

    def load_pdf_text(self, text: str):
        self.pdf_context = text.strip()
        print("[📎 PDF Context Loaded into RAG]")

# ✅ Export Singleton
rag_chain = RAGChainWithContext()
