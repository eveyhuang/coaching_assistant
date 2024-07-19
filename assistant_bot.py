
import time
import streamlit as st
from datetime import date, datetime
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import utils
import llm_chains
import schema
import json
import ast


app = utils.init_app()
ref = utils.init_db()
prev_goal = ''

 
# a schema for all the information the LLM should collect

user_init_proj = schema.ProjectSchema()


# LLM for tagging users' response into a schema 
proj_tagging_chain = llm_chains.proj_tag_chain
# ref_tagging_chain = llm_chains.ref_tag_chain

# a dictionary of items to ask and corredsponding definitions
proj_question_dict = schema.proj_Questions


# list of items to ask
ask_proj_init = list(proj_question_dict.keys())


# scehmas for facilitating novices to update and checkin
# 0 = init pydantic schema object
# 1 = question dictionaries
# 2 = list of items to ask 
# 3 = taggingchain
# 4 = pydantic schema
checkin_schemas = {
    "monitor": [user_init_proj, proj_question_dict, ask_proj_init, proj_tagging_chain, schema.ProjectSchema],
}  

proj_question_chain = llm_chains.proj_question_chain

# run LLM to formulate a question
def ask_for_info(chain, history, human_input, previous_goal, item, description, example):
    try:
        question = chain.invoke({"history": history, "human_input":human_input, "previous_goal":previous_goal, "item": item, "description": description, "example":example})
        return question
    except:
        print("Encountered errors when asking about ", item)
        print("history  : ", history)
        return example

# based on tagged data check what items are left to ask
def check_what_is_empty(user_peronal_details):
    ask_for = []
    for field, value in user_peronal_details.dict().items():
        if field not in ['previous_goal'] and value in [None, "", 0]: 
            ask_for.append(f'{field}')
    
    return ask_for

# add newly answered details into Reflection schema
def add_non_empty_details(current_details: schema.ProjectSchema, new_details: schema.ProjectSchema):
    non_empty_details = {k: v for k, v in new_details.dict().items() if v not in [None, "", False]}
    # updated_details = current_details.copy(update=non_empty_details)
    copied = current_details.copy() 
    for k, v in new_details.dict().items():
        if v not in [None, "", False]:
            if k in current_details.dict().keys():
                if copied.__dict__[k] in [None, "", False]:
                    copied.__dict__[k] = v
                elif v not in copied.__dict__[k]:
                    print("UPDATE: adding to [ " + k + " ] with: [ " + v + " ]")
                    copied.__dict__[k] += " " + v
    # updated_details = current_details
    return copied

# use tagging chain to fill in ReflectionDetails schema
def filter_response(tagging_chain, text_input, user_details):
    # print("Tagging input: ", text_input)
    # print("Old user details: ", user_details)
    try:
        res = tagging_chain.run(text_input)
        # print("**  after tagging: ", res)
        user_details = add_non_empty_details(user_details, res)

        print("**** Newest user detail: ", user_details)
        ask_for = check_what_is_empty(user_details)
        print("ask for: ", ask_for)
        return user_details, ask_for
    except:
        print("encountered errors while trying to tag input")
        return st.session_state.details, st.session_state.ask_for

# summarize data in user details
def summarize_all_details(user_details):
    name = ''
    copied = user_details.copy() 
    for k, v in user_details.dict().items():
        if k == 'full_name':
            name = copied.__dict__[k]
        else:
            copied.__dict__[k] = llm_chains.summary_chain.invoke({"information": v, "name": name})
    # updated_details = current_details
    return copied 

# return name in propper format
def format_name(name):
    lower = name.lower()
    val_name =' '.join(word[0].upper() + word[1:] for word in lower.split())
    return val_name

# save data to firebase db
def savedata(all_info, data, location):
    
    stu_name = all_info['full_name']
    if isinstance(data, dict):
        data['full_name']=format_name(stu_name)
        data['time']=datetime.now().isoformat()
    else:
        data={"full_name": stu_name,
              "log": data}
    ref.child(location).push().set(data)

# given a diagnosis returned by diagnose_chain, return a library that has diagnosed risk name as keys, 
# and a pair of value (reasoning for diagnosis, a question to ask)
def get_risk_library(diagnosis):
    risk_library = {}
    # print(type(diagnosis), diagnosis)

    # print("CALLING get_prevgoals with: " + name )
    
    if not isinstance(diagnosis, dict):
        diagnosis = json.loads(diagnosis.replace("'", "\""))
    if 'diagnosed_risks' in diagnosis.keys():
        for i in range(0, len(diagnosis['diagnosed_risks'])):
            risk_library[diagnosis['diagnosed_risks'][i]] = [diagnosis["reasoning_for_risks"][i], diagnosis['questions_to_ask'][i]]
    else:
        print("keys don't match: ", diagnosis.keys())
    # print("risk library: ", risk_library)
    return risk_library

# either load risk framework from db or save the one from schema to db and return
def get_risk_framework():
    snapshot = ref.child('risk_framework').order_by_key().limit_to_last(1).get()
    if snapshot:
        # print("retrieved risk framework from db: ", snapshot)
        return snapshot
    else:
        framework = schema.risk_model
        ref.child('risk_framework').push().set(framework)
        print("saved risk framework to db")
        return framework
    
# use risk framework to diagnose
def diagnose(user_details):
#   category = categorize_chain.invoke({"input": user_input, "areas": schema.risk_model.keys()})
#   cat_list = ast.literal_eval(category)
#   risk_area = [schema.risk_model[k] for k in cat_list]
    risk_framework = get_risk_framework()
    diagnosis = None
    try:
        diagnosis = llm_chains.diagnose_chain.invoke({"input": user_details, "risk": risk_framework})
    except:
        diagnosis = 'Sorry there was some technical error. Could you please try to refresh the page?'
           
    
    return diagnosis

# retrieve a student's previous planning from firebase db
def get_prevgoals(stu_name):
    global prev_goal
    name = format_name(stu_name)
    goal_ref = ref.child('check-in')

    # print("CALLING get_prevgoals with: " + name )
    snapshot = goal_ref.order_by_child('full_name').equal_to(name).limit_to_last(1).get()
        
    reflection = None
    if snapshot:
        for value in snapshot.items():
            reflection = value[1]
        if reflection:
            prev_goal = reflection['planning']


if "messages" not in st.session_state:
    question = "Hello, I am here to help you reflect on your recent progress, diagnose potential risks, and prepare for your upcoming coaching session. Before we start, what is your full name?"
    st.session_state.messages = [{"role":"assistant", "content":question}]
    
# default state should be reflections. but it can change    
if "mode" not in st.session_state:
    st.session_state.mode = "monitor"
 
if "details" not in st.session_state:
    st.session_state.details = checkin_schemas[st.session_state.mode][0]

if "ask_for" not in st.session_state:
    st.session_state.ask_for = checkin_schemas[st.session_state.mode][2]

if "diagnosis_library" not in st.session_state:
    st.session_state.diagnosis_library = []

if "risks" not in st.session_state:
    st.session_state.risks = []

if "last_risk" not in st.session_state:
    st.session_state.last_risk = ''

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if answer := st.chat_input("Please type your response here. "):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": answer})
    if "prev_goals" not in st.session_state:
        st.session_state.prev_goals = get_prevgoals(answer)
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(answer)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        tagging_chain = proj_tagging_chain
        
        # monitoring stage; ask monitoring questions based on st.session_state.ask_for
        if st.session_state.mode == 'monitor':    
            
            st.session_state.details, st.session_state.ask_for = filter_response(tagging_chain, st.session_state.messages[-2:], st.session_state.details)
            if st.session_state.ask_for != []:
                question_dict = checkin_schemas[st.session_state.mode][1]
                question_chain = proj_question_chain
                assistant_response = ask_for_info(
                                                question_chain,
                                                st.session_state.messages[-3:],
                                                answer,
                                                prev_goal,
                                                st.session_state.ask_for[0], 
                                                question_dict[st.session_state.ask_for[0]][0],
                                                question_dict[st.session_state.ask_for[0]][1])
            
            # once no more questions to ask, diagnose and move to diagnosis stage
            else:
                assistant_response = """I have a few follow up questions based on some risks that I have identified. Can I ask them?"""
                diagnosis = diagnose(st.session_state.details.dict())
                st.session_state.diagnosis_library = get_risk_library(diagnosis)
                st.session_state.mode = 'diagnose'
                st.session_state.risks = list(st.session_state.diagnosis_library.keys())
            
        # ask diagnosis questions based on st.session_state.risks
        elif st.session_state.mode == 'diagnose':
            if st.session_state.last_risk != '':
                st.session_state.diagnosis_library[st.session_state.last_risk].append(answer)
            
            if st.session_state.risks != []:
                print("diagnosed risks: ", st.session_state.risks)
                num_risks = len(st.session_state.risks)
                risk = st.session_state.risks[0]
                st.session_state.last_risk = risk
                reason_qs = st.session_state.diagnosis_library[risk]
                print("next risk to ask about: ", risk, reason_qs)
                next_question = llm_chains.diag_qa_chain.invoke({ "question": reason_qs[1], "risk": reason_qs[0], "history":st.session_state.messages[-3:], "human_input": answer})  
                assistant_response = next_question
                st.session_state.risks.pop(0)

            else:
                st.session_state.mode = 'summarize'
                st.session_state.last_risk = ''
                assistant_response = """Thank you for answering all of my questions.  \n
                                        Please navigate to your personal page for a summary of my diagnosis, and choose ones that you think are the most relevant to discuss during your next coaching session.
                                    """
                

                # save students' check-in and diagnosis to db
                st.session_state.details, st.session_state.ask_for = filter_response(tagging_chain, st.session_state.messages[-6:], st.session_state.details)
                
                final_details = summarize_all_details(st.session_state.details)
                final_details = final_details.dict()
                
                savedata(final_details, st.session_state.diagnosis_library, 'diagnosis')
                savedata(final_details, final_details, 'check_in')
                savedata(st.session_state.details.dict(), st.session_state.details.dict(), 'check_in_original' )
                savedata(final_details, st.session_state.messages, 'log')
        
        else:
            assistant_response = """Thank you for answering all of my questions.
                                 """
        
            
        for chunk in assistant_response.split():
            full_response += chunk + " "
            time.sleep(0.05)
            # Add a blinking cursor to simulate typing
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
        
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})