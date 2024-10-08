import streamlit as st
import utils
import pandas as pd
import numpy as np
from streamlit_dynamic_filters import DynamicFilters
import hmac
from datetime import datetime
import schema
import llm_chains

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["c_password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False


if not check_password():
    st.stop()  # Do not continue if check_password is not True.

app = utils.init_app()
ref = utils.init_db()

if "coaching_goals" not in st.session_state:
    st.session_state.coaching_goals = ""

st.set_page_config(
    page_title='Coaching Dahsboard / Individual View',
    initial_sidebar_state="expanded"
)

# load data from ref and do some manipulations 
def load_data(collection):
    data = ref.child(collection).get()    
    return data

# use llm to generate questions based on project info and chosen risks to discuss
def generate_Qs(project_info, risk_to_discuss, coaching_outcome):
    chosen_risks={}
    framework = schema.q_framework
    q_chain = llm_chains.coach_question_chain
    if "Risks" in risk_to_discuss.keys():
        if len(risk_to_discuss["Risks"])>0:
            for risks in risk_to_discuss["Risks"]:
                if risks in stu_dia_dict.keys():
                    chosen_risks[risks] = stu_dia_dict[risks]
                elif risks in dia_dict.keys():
                    if not isinstance(dia_dict[risks], list):
                        chosen_risks[risks] = dia_dict[risks]
                    else:
                        chosen_risks[risks] = dia_dict[risks][0]
                else:
                    chosen_risks['student notes'] = risks
    else:
        chosen_risks = stu_dia_dict
    
    try:
        print("Suggesting questions for risks :", chosen_risks)
        response = q_chain.invoke({"information": project_info, "diagnosis": chosen_risks, "framework": framework, "outcome": coaching_outcome})
        return response
    except:
        return "Sorry, I am having some technical issues, please try again later."

# load and save reflection df
reflection_data = load_data('check_in')
reflection_df = utils.format_reflection(reflection_data)

diagnosis_data = load_data('diagnosis')
diagnosis_df = utils.format_reflection(diagnosis_data)

student_data = load_data('students')
student_df = utils.format_data(student_data)

risk_framework = ref.child('risk_framework').order_by_key().limit_to_last(1).get()
risk_df = utils.format_risk_framework(risk_framework)

stu_dia_data = load_data('coaching_agenda')
stu_dia_df = utils.format_stu_diagnosis(stu_dia_data)
# print("retrieved student diagnosis data:     ", stu_dia_df)

dynamic_filters = DynamicFilters(reflection_df, filters = ['full_name', 'date'])

with st.sidebar:
    dynamic_filters.display_filters()


filtered_ref_df = dynamic_filters.filter_df()
filtered_ref_df.sort_values('time', ascending=False)

sel_stu = filtered_ref_df.iloc[0]['full_name']
sel_date = filtered_ref_df.iloc[0]['date']
filtered_dia_df = diagnosis_df[(diagnosis_df['full_name']==sel_stu) & (diagnosis_df['date']==sel_date)]
filt_stu_dia_df = stu_dia_df[(stu_dia_df['full_name']==sel_stu) & (stu_dia_df['date']==sel_date)]
filt_stu_dia_df.sort_values('date', ascending=False)

if not filtered_dia_df.empty:
    st.markdown('### ' + sel_stu)

    # section to display the most recent reflection
    st.markdown("#### Summary of Project Info")
    ref_toshow = filtered_ref_df.iloc[:1][['project_information', 'process', 'learning', 'obstacles', 'planning']].copy()


    col= ['project_information', 'current_focus', 'learning', 'obstacles', 'planning', 'emotions', 'coaching_outcome']
    try:
        ref_toshow = filtered_ref_df.iloc[:1][col].copy()
    except:
        filtered_ref_df=filtered_ref_df.rename(columns = {'process':'current_focus'})
        ref_toshow = filtered_ref_df.iloc[:1][col].copy()
    ref_toshow = ref_toshow.T
    ref_toshow.columns=['information']
    st.table(ref_toshow)

    st.markdown('---')

    # section to show diagnosis 
    st.markdown("#### Diagnosis")
    st.markdown('Click on risks that you would like to discuss with the student.')
    list_diagnosed_risks = list(filtered_dia_df.columns)
    list_all_risks = list(risk_df.columns)
    list_stu_risks = list(filt_stu_dia_df.columns) if not filt_stu_dia_df.empty else {}
    
    st.markdown('##### Risks chosen by student')

    # build a dictionary of risks chosen by students
    stu_dia_dict = {}
    if not filt_stu_dia_df.empty:
        for col in filt_stu_dia_df.columns:
            # print("NEXT COLUMN:    ", col)
            if col in list_all_risks:
                items = filt_stu_dia_df.iloc[0][col]
                if isinstance(items, list):
                    diag = [col, items[0], items[1], items[2]]
                    stu_dia_dict[col]=[items[0], items[1], items[2]]
                elif type(items)==str:
                    stu_dia_dict[col] = items
                else:
                    list_stu_risks.remove(col)
            elif col == "student_submitted":  
                items = filt_stu_dia_df.iloc[0][col]
                if len(items)>0:
                    stu_dia_dict['notes_from_student'] = items 
                   

    # display students' diagnosed risks in tabs
    stu_tab_labels = list(stu_dia_dict.keys())
    if len(stu_tab_labels)>0:
        tabs = st.tabs(stu_tab_labels)
        for label, tab in zip(stu_tab_labels, tabs):
            with tab:
                if isinstance(stu_dia_dict[label], list):
                    st.checkbox(":gray-background["+ stu_dia_dict[label][0]+']', key=label)
                    st.markdown(":blue[**Question:** "+stu_dia_dict[label][1] + ']')
                    st.markdown(":green[ **Response:**]" + ":green[ " +stu_dia_dict[label][2] + ']')
                else: 
                    st.checkbox(":gray-background["+ stu_dia_dict[label]+']', key=label)
    else:
        st.markdown(":red[The student has not conducted any diagnosis yet.]")

    with st.expander('##### Other risks diagnosed by system'):
        # dictionary of risks diagnosed by system but not chosen by student
        dia_dict = {}
        
        for col in filtered_dia_df.columns:
            
            if col in list_all_risks and col not in list_stu_risks:
                
                items = filtered_dia_df.iloc[0][col]
                
                if isinstance(items, list):
                    diag = [col, items[0], items[1], items[2]]
                    dia_dict[col]=[items[0], items[1], items[2]]
                else:
                    list_diagnosed_risks.remove(col)
        
        # display other risks 
        sys_tab_labels = list(dia_dict.keys())
        if len(sys_tab_labels):
            tabs = st.tabs(sys_tab_labels)
            for label, tab in zip(sys_tab_labels, tabs):
                with tab:
                    st.checkbox(":gray-background["+ dia_dict[label][0]+']', key=label)
                    st.markdown(":blue[**Question Asked:** "+dia_dict[label][1] + ']')
                    st.markdown(":green[ **Response:**]" + ":green[ " +dia_dict[label][2] + ']')
        else:
            st.markdown('---')

    # with st.expander("##### All other risks in the framework"):
        
    #     for col in list_all_risks:
    #         if col not in list_diagnosed_risks:
    #             st.checkbox(":gray[ "+ col + ": " + risk_df.iloc[0][col] + ']', key=col)

    st.markdown('---')
    # area for coaches to add notes
    st.markdown("#### Coaching Agenda / Notes")
    agenda_data = load_data('coaches_notes')

    agenda_df = utils.format_agenda(agenda_data)
    filt_agenda_df = agenda_df[(agenda_df['full_name']==sel_stu)]
    if not filt_agenda_df.empty:  
        with st.expander("##### Saved notes"):  
            try:
                st.dataframe(filt_agenda_df[['date', 'Notes', 'Risks']], hide_index=True)
            except:
                print("Error showing coaching notes")

    # this is for saving to coaching agenda
    risk_to_disucss = {}
    # this is for generating questions, have more details
    
    for risk in list_diagnosed_risks:
        if risk in list_all_risks:
            is_clicked = st.session_state[risk]
            if is_clicked:
                st.markdown("* " +risk)
                try:
                    risk_to_disucss['Risks'].append(risk)
                except:
                    risk_to_disucss['Risks'] = [risk]
      
    for risk in list_stu_risks:
        if (risk not in list_diagnosed_risks) & (risk in list_all_risks):
            is_clicked = st.session_state[risk]
            if is_clicked:
                st.markdown("* " +risk)
                try:
                    risk_to_disucss['Risks'].append(risk)
                except:
                    risk_to_disucss['Risks'] = [risk]
        elif risk == 'student_submitted':
            if "notes_from_student" in stu_dia_dict.keys():
                stu_risk = stu_dia_dict['notes_from_student']
                is_clicked = st.session_state['notes_from_student']
                if is_clicked:
                    st.markdown("* " + stu_risk)
                    try:
                        risk_to_disucss['Risks'].append(stu_risk)
                    except:
                        risk_to_disucss['Risks'] = [stu_risk]
                
   

    with st.form('additional_risk'):
        
        stu_risk = st.text_input("Write down desired coaching outcomes below, and the system will suggest questions you could ask based on the outcomes and chosen risks.", "")
        submitted = st.form_submit_button("Submit and see suggestted questions")
        
        if submitted:
            
            risk_to_disucss['Notes'] = stu_risk
            st.session_state.coaching_goals = stu_risk
            risk_to_disucss['full_name'] = sel_stu
            risk_to_disucss['date'] = datetime.today().strftime('%Y-%m-%d')
            

            questions = generate_Qs(ref_toshow.to_dict(), risk_to_disucss, st.session_state.coaching_goals)
            st.markdown(questions)
            
            risk_to_disucss['questions'] = questions
            ref.child('coaches_notes').push().set(risk_to_disucss)
            # st.write("Agenda saved! Thank you.")    

         
    
    