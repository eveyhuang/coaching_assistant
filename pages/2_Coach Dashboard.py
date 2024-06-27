import streamlit as st
import utils
import pandas as pd
import numpy as np
from st_aggrid import AgGrid
import plotly.express as px 
from datetime import datetime
from streamlit_card import card
from streamlit_dynamic_filters import DynamicFilters



app = utils.init_app()
ref = utils.init_db()


st.set_page_config(
    page_title='Coaching Dahsboard / Individual View',
    initial_sidebar_state="expanded"
)

# load data from ref and do some manipulations 

def load_data(collection):
    data = ref.child(collection).get()    
    return data



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

sel_stu = filtered_ref_df.iloc[0]['full_name']
sel_date = filtered_ref_df.iloc[0]['date']
filtered_dia_df = diagnosis_df[(diagnosis_df['full_name']==sel_stu) & (diagnosis_df['date']==sel_date)]
filt_stu_dia_df = stu_dia_df[(stu_dia_df['full_name']==sel_stu) & (stu_dia_df['date']==sel_date)]
# print("filtered student diagnosis data with name: ", sel_stu, "; Date:   ", sel_date, ":   ", filt_stu_dia_df)
# section for student and project information

st.markdown('### ' + sel_stu)


# section to display the most recent reflection
st.markdown("#### Check-in")
ref_toshow = filtered_ref_df.iloc[:1][['project_information', 'process', 'learning', 'obstacles', 'planning', 'emotions']].copy()
ref_toshow = ref_toshow.T
ref_toshow.columns=['information']
st.table(ref_toshow)


# section to show diagnosis 
st.markdown("#### Diagnosis")
list_diagnosed_risks = list(filtered_dia_df.columns)
list_all_risks = list(risk_df.columns)
list_stu_risks = list(filt_stu_dia_df.columns) if not filt_stu_dia_df.empty else {}

st.markdown('##### Risks chosen by student')

# build a dictionary of risks chosen by students
stu_dia_dict = {}
if not filt_stu_dia_df.empty:
    for col in filt_stu_dia_df.columns:
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
                stu_dia_dict['Other risks identified by student'] = items 

# display students' diagnosed risks in tabs
stu_tab_labels = list(stu_dia_dict.keys())
if len(stu_tab_labels)>0:
    tabs = st.tabs(stu_tab_labels)
    for label, tab in zip(stu_tab_labels, tabs):
        with tab:
            if isinstance(stu_dia_dict[label], list):
                st.checkbox(":gray-background[Risk: "+ stu_dia_dict[label][0]+']', key=label)
                st.markdown(":blue[**Question Asked:** "+stu_dia_dict[label][1] + ']')
                st.markdown(":green[**Student's Response:** " +stu_dia_dict[label][2] + ']')
            else: 
                st.checkbox(":gray-background[Risk: "+ stu_dia_dict[label]+']', key=label)
else:
    st.markdown(":red[The student has not conducted any diagnosis yet.]")

st.markdown('##### Other risks diagnosed by system')


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
tabs = st.tabs(sys_tab_labels)
for label, tab in zip(sys_tab_labels, tabs):
    with tab:
        st.checkbox(":gray-background[Risk: "+ dia_dict[label][0]+']', key=label)
        st.markdown(":blue[**Question Asked:** "+dia_dict[label][1] + ']')
        st.markdown(":green[**Student's Response:** " +dia_dict[label][2] + ']')


# area for coaches to add notes
st.markdown("#### Coaching Agenda", help = "Choose risks that you think are the most relevant, or write down additional risks that you have diagnosed.")
risk_to_disucss = {}
for risk in list_diagnosed_risks or list_stu_risks:
    if risk in list_all_risks:
        is_clicked = st.session_state[risk]
        if is_clicked:
            st.markdown("* " +risk )
            if risk in dia_dict.keys():
                risk_to_disucss[risk]=dia_dict[risk]
            else:
                risk_to_disucss[risk]= risk_df.iloc[0][risk]

with st.form('additional_risk'):
    
    stu_risk = st.text_input("Add additional risks or items that you would like to discuss with the student", "")
    submitted = st.form_submit_button("Submit")
    if submitted:
        risk_to_disucss['student_submitted'] = stu_risk
        risk_to_disucss['full_name'] = sel_stu
        risk_to_disucss['date'] = sel_date
        ref.child('coaches_notes').push().set(risk_to_disucss)
        st.write("Agenda saved! Thank you.")
        