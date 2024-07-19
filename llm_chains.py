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
import streamlit as st

# llm model
tag_llm = ChatOpenAI(
    openai_api_key=st.secrets['config']['openai_api_key'],
    temperature=0, 
    model="gpt-4o")
llm = ChatGroq(
    groq_api_key=st.secrets['config']['GROQ_API_KEY'],
    temperature=0,
    model="llama3-70b-8192"
)
checkin_model = llm

#### TAGGING CHAINS; take a schema return a tagging chain model
# ref_tag_chain = create_tagging_chain_pydantic(schema.ReflectionSchema, ChatOpenAI(temperature=0, model="gpt-4"))
#proj_tag_chain = create_tagging_chain_pydantic(schema.ProjectSchema, ChatOpenAI(temperature=0, model="gpt-4"))

tagging_template = """ Extract the desired information about the user from the following conversation between an assistant and the user in the input below.
                    Use the question asked by the assistant as context, extract properties that match the descriptions closely in the 'information_extraction' function from user's response.
                    Extract as many relevant properties as possible at once, but do NOT make up any information.     
                    When extracting properties, rephrase and summarize it into short and coherent sentences and fix any typos or grammar errors.  
                    Conversation:
                    {input}
                    """

proj_tag_chain = create_tagging_chain_pydantic(pydantic_schema=schema.ProjectSchema, llm=tag_llm, prompt= ChatPromptTemplate.from_template(tagging_template))



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



# Prompt for summarizing 

summary_prompt_template = """ You are a helpful assistant that summarizes all the content in the `information` blocks into a single, less-than-30-word half-sentence that doesn't have subjects.
    Do not make up any information that is not provided, but make sure your summary maintains all the nuance.
    Only return the summary and nothing else.
    
    Information:
    {information} 
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
    ResponseSchema(name="questions_to_ask", description="list of questions to ask the user to help them reflect on this risk and think about what they plan to do if they don't have an answer"),
]

output_parser=StructuredOutputParser.from_response_schemas(diagnosis_schema)
format_instructions = output_parser.get_format_instructions()

prompt = PromptTemplate(
    template="""You are a helpful thought partner that challenges novice entrepreneurs' 
        assumptions and help them identify possible risks that may make their products fail. 
        Given all the information about the user in the 'input' block, and a list of common risks: {risk}
        Use each of the risk to evaluate user input and diganose the top three risks that are most relevant to the input, might be present, and might occur in the near future. 
        Explain your reasoning on your diagnosis. If the risk you identified is about having risky asusmptions that are either not identified or validated, include a possible risky assumption in your reasoning. 
        Structure your output into json format using these keys: diagnosed_risks, reasoning_for_risks, questions_to_ask. follow format instruction: \n{format_instructions}

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
        """You are an experienced entrepreneur who deeply understands the fundamentals of entrepreneurship, 
        and you want to ask the user, a novice entrepreneur, good questions to help them identify and reflect on risks that may make their venture fail if left unaddressed.
        In one setence, explain to the user that you think there might be a possible risk: {risk}.
        Then ask these questions: [{question}].
        If and only if there is a question in the 'human_input' block, adds a one-sentence respond to the question at the begining of your response. 
        Make sure to tailor your whole response to the context in the 'history' block, and replace names with the second pronoun. 
        Keep your whole response short, friendly, and conversational. 
        Only return the requested response.

    History of conversation: {history}
    User: {human_input}
    Assistant: 

Classification:"""
    )
    | llm
    | StrOutputParser()
)


#      