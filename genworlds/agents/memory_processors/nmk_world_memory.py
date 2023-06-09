from typing import List

from langchain import PromptTemplate, LLMChain
from langchain.chat_models import ChatOpenAI

from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings


class OneLineEventSummarizer:
    def __init__(self, openai_api_key: str, model_name: str = "gpt-3.5-turbo"):
        self.summary_template = """
        This is The last event coming from a web-socket, it is in JSON format:
        {event}
        Summarize what happened in one line.
        """

        self.summary_prompt = PromptTemplate(
            template=self.summary_template,
            input_variables=[
                "event",
            ],
        )

        self.chat = ChatOpenAI(
            temperature=0, model_name=model_name, openai_api_key=openai_api_key
        )
        self.chain = LLMChain(llm=self.chat, prompt=self.summary_prompt)

    def summarize(
        self,
        event: str,
    ) -> str:
        """
        Summarize the event in one line.
        """
        return self.chain.run(event=event)


class FullEventStreamSummarizer:
    def __init__(self, openai_api_key: str, model_name: str = "gpt-3.5-turbo"):
        self.small_summary_template = """
        This is the full event stream coming from a web-socket, it is in JSON format:
        {event_stream}
        Summarize what happened during the event stream in {k} paragraphs.
        
        SUMMARY:
        """

        self.summary_prompt = PromptTemplate(
            template=self.small_summary_template,
            input_variables=[
                "event_stream",
                "k",
            ],
        )

        self.chat = ChatOpenAI(
            temperature=0, model_name=model_name, openai_api_key=openai_api_key
        )
        self.small_summary_chain = LLMChain(llm=self.chat, prompt=self.summary_prompt)

    def summarize(
        self,
        event_stream: List[str],
        k: int = 5,
    ) -> str:
        """
        Summarize the event stream in k paragraphs.
        """
        if len(event_stream) <= 100:
            return self.small_summary_chain.run(event_stream=event_stream, k=k)
        else:
            return self._summarize_large_event_stream(event_stream=event_stream)

class NMKWorldMemory:
    def __init__(self, openai_api_key: str, model_name: str = "gpt-3.5-turbo", n: int = 5, m: int = 5, k: int = 5):
        self.n = n # last events
        self.m = m # similar events
        self.k = k # paragraphs in the summary

        self.world_events = []
        self.summarized_events = []
        self.one_line_summarizer = OneLineEventSummarizer(
            openai_api_key=openai_api_key, model_name=model_name
        )
        self.embeddings_model = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.embedding_size = 1536

        self.embeddings_model
        self.events_chroma_db 
        self.summarized_events_chroma_db

    def add_event(self, event, summarize: bool = False):
        self.world_events.append(event)
        if summarize:
            self._add_summarized_event(event)

    def _add_summarized_event(self, event):
        sum_event = self.one_line_summarizer.summarize(event)
        self.summarized_events.append(sum_event)

    def _get_n_last_events(self, n: int = 5, summarized: bool = False):
        if summarized:
            return self.summarized_events[-n:]
        else:
            return self.world_events[-n:]

    def _get_m_similar_events(self, m: int = 5, summarized: bool = False):
        if summarized:
            m_events = self.summarized_events_chroma_db.similarity_search()
            return m_events
        else:
            m_events = self.events_chroma_db.similarity_search()
            return m_events            

    def get_event_stream_memories(self, n:int = 5, m:int = 5, summarized: bool = False):
        last_events = self._get_n_last_events(n=n, summarized=summarized)
        similar_events = self._get_m_similar_events(m=m, summarized=summarized)
        n_plus_m_events = "# Last events\n\n"+ "\n".join(last_events) + "\n\n# Similar events\n\n" + "\n".join(similar_events)
        return n_plus_m_events

