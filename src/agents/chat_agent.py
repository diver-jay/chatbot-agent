from abc import ABC, abstractmethod
from langchain.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder


class ChatAgent(ABC):
    @abstractmethod
    def load_prompt(self):
        pass

    @abstractmethod
    def act(self, **kwargs):
        """Execute the agent's action with the given input."""
        pass