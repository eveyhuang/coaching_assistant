from langchain_community.chat_models import ChatOpenAI
from langchain_openai import OpenAI
from langchain.chains import LLMChain
from langchain_core.output_parsers import StrOutputParser
import ast
from langchain_community.utils.openai_functions import (
    convert_pydantic_to_openai_function,
)
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.runnables import RunnablePassthrough, ConfigurableField
from langchain.output_parsers.openai_functions import PydanticOutputFunctionsParser
from langchain.chains import create_tagging_chain_pydantic
import schema
from langchain_core.messages import AIMessage
import json
import re
from typing import List, Optional
from langchain_community.utils.openai_functions import (
    convert_pydantic_to_openai_function,
)
from langsmith.wrappers import wrap_openai
from langsmith import traceable
import openai
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_groq import ChatGroq

# llm model
#llm = ChatOpenAI(temperature=0, model="gpt-4")
llm = ChatGroq(
    temperature=0,
    model="llama3-70b-8192"
)

#### TAGGING CHAINS; take a schema return a tagging chain model
# ref_tag_chain = create_tagging_chain_pydantic(schema.ReflectionSchema, ChatOpenAI(temperature=0, model="gpt-4"))
#proj_tag_chain = create_tagging_chain_pydantic(schema.ProjectSchema, ChatOpenAI(temperature=0, model="gpt-4"))
proj_tag_chain = create_tagging_chain_pydantic(schema.ProjectSchema, llm)


# (V1) prommt for formulating questions to checkin in with students 
# ref_quesion_prompt = """ You are a coaching assistant who ask users reflective questions to help them reflect on their progress.
#     Formulate a question in a friendly and supportive tone about an item: {item}, based on its description: {description}. An example will be {example}.
#     If the item is "progress", you should remind the user what his previous goal was from your last check in ({previous_goal}).
#     However, if previous goal ({previous_goal}) is not available, you should ask the user to remind you what was the goal they set for themselves to work on last week. 
#     You should only ask about {item}, ask one question at a time. 
#     Do not make up any answers for the human. Wait for them to respond.
    
#     History of conversation: {history}
#     User: {human_input}
#     Assistant: 
# """



#checkin_model = ChatOpenAI(temperature=0, model="gpt-4")
checkin_model = llm


# prommt for formulating questions to help students provide information on project 
proj_quesion_prompt = """ You are an experienced entrepreneurship coach. You are coaching users by asking them reflective questions to help them articulate their project details.
    Formulate a question that is tailored to the context of the chat, in a friendly and supportive tone about {item}, based on its description: {description}. 
    An example will be: {example}.
    You should only ask about {item}, ask one question at a time. 
    Do not make up any answers for the human. Wait for them to respond.
    
    History of conversation: {history}
    User: {human_input}
    Assistant: 
"""

question_prompt = ChatPromptTemplate.from_template(proj_quesion_prompt)
proj_question_chain = question_prompt | checkin_model | StrOutputParser()


# checkin_chains = {
#     "project": proj_chain,
#     "reflections": ref_chain
# }

# return the llm chain to formulate checkin questions based on mode (reflection or project)
# def getCheckinChain(mode):
#     return checkin_chains[mode]



# Prompt for summarizing check-in for coaches

summary_prompt_template = """ You are a helpful assistant that extracts and summarizes information about the user's venture by 
    generating an accurate and concise summary of a conversation that is provided between the following `information` json blocks.
    In your summaries, refer to the user with only first name.  Do not make up any information that is not in the provided `information` json blocks. 
    Start your summary by saying that this is the recap of what the user has told you today and asks the user to confirm whether your summary is accurate at the end.
    <checkin>
        {information} 
    <checkin/>

    Assistant: 
"""

summary_prompt = ChatPromptTemplate.from_template(summary_prompt_template)
# summary_model = ChatOpenAI(temperature=0, model="gpt-4")
# openai_functions = [convert_pydantic_to_openai_function(schema.CoachingSchema)]
# output_parser = PydanticOutputFunctionsParser(pydantic_schema=schema.CoachingSchema)
# summary_chain = summary_prompt | coach_model.bind(functions=openai_functions) | output_parser
summary_chain = summary_prompt | llm | StrOutputParser()


summary_risk_template = """ You are a helpful and friendly assistant. 
Start by saying that you have summarized the list of risks that you have diagnosed,
then summarizes each of the risk and reasoning of the risk in `diagnosis` into one coherent sentence in supportive and friendly tone.
Return these sentences into bullet points each in a new paragraph. 
End by asking the user which one of the risk do they think is the most pressing and relevant. 

{diagnosis}
    Assistant: 
"""

summary_risk_prompt = ChatPromptTemplate.from_template(summary_risk_template)
summary_risk_chain = summary_risk_prompt | llm | StrOutputParser()

# coach_model = ChatOpenAI(temperature=0, model="gpt-4")
# coach_prompt = ChatPromptTemplate.from_template(summary_prompt_template)
# openai_functions = [convert_pydantic_to_openai_function(schema.CoachingSchema)]
# output_parser = PydanticOutputFunctionsParser(pydantic_schema=schema.CoachingSchema)
# summary_chain = coach_prompt | coach_model.bind(functions=openai_functions) | output_parser


# project_model = ChatOpenAI(temperature=0, model="gpt-4")
# project_prompt = ChatPromptTemplate.from_template(summary_prompt_template)
# proj_openai_functions = [convert_pydantic_to_openai_function(schema.ProjectSchema)]
# proj_output_parser = PydanticOutputFunctionsParser(pydantic_schema=schema.ProjectSchema)
# proj_summary_chain = project_prompt | project_model.bind(functions=proj_openai_functions) | proj_output_parser



# Custom parser
def extract_json(message: AIMessage) -> List[dict]:
    """Extracts JSON content from a string where JSON is embedded between ```json and ``` tags.

    Parameters:
        text (str): The text containing the JSON content.

    Returns:
        list: A list of extracted JSON strings.
    """
    text = message.content
    # Define the regular expression pattern to match JSON blocks
    pattern = r"```json(.*?)```"

    # Find all non-overlapping matches of the pattern in the string
    matches = re.findall(pattern, text, re.DOTALL)

    # Return the list of matched JSON strings, stripping any leading or trailing whitespace
    try:
        return [json.loads(match.strip()) for match in matches]
    except Exception:
        raise ValueError(f"Failed to parse: {message}")
    

# LLM chain for categorizing 
categorize_chain = (
    PromptTemplate.from_template(
        """Given the user input below, classify it as which of these areas: {areas} that the user's input is most likely to belong.
           Respond with no more than three areas.

<input>
{input}
</input>

Classification:"""
    )
    | llm
    | StrOutputParser()
)

# diagnosis schema
diagnosis_schema =[
    ResponseSchema(name="diagnosed_risks", description="list of the names of diagnosed risks"),
    ResponseSchema(name="reasoning_for_risks", description="list of the reasoning for each of the diagnosed risks"),
    # ResponseSchema(name="questions_to_ask", description="list of questions to ask the user"),
]

output_parser=StructuredOutputParser.from_response_schemas(diagnosis_schema)
format_instructions = output_parser.get_format_instructions()

prompt = PromptTemplate(
    template="""You are a helpful thought partner that challenges novice entrepreneurs' 
        assumptions and help them identify possible risks that may make their products fail. 
        Given the user (who is a novice entrepreneur) input below, and a list of common risks: {risk}
        Use each of the risk to evaluate user input and diganose the top three risks that are most relevant to the input, might be present, and might occur in the near future. Explain your reasoning on your diagnosis. 
        structure your output into json format using these keys: diagnosed_risks, reasoning_for_risks, questions_to_ask. follow format instruction: \n{format_instructions}

<input>
{input}
</input>

""",
    input_variables=["input", "risk"],
    partial_variables={"format_instructions": format_instructions},
)

diagnose_chain = prompt | llm | output_parser


# LLM chain for diagnosis
diag_qa_chain = (
    PromptTemplate.from_template(
        """You are a helpful thought partner that asks users reflective questions to help them articulate thinking and realize possible risk in their project. 
        In a coherent setence, tell the user the potential risk you have identifed: {risk} 
        and ask this question: {question} in friendly and supportive tone. 
        make sure the question is tailored to the context in the history.

    History of conversation: {history}
    User: {human_input}
    Assistant: 

Classification:"""
    )
    | llm
    | StrOutputParser()
)