import streamlit as st
import utils
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

dynamic_filters = DynamicFilters(reflection_df, filters = ['full_name', 'date'])

with st.sidebar:
    dynamic_filters.display_filters()


filtered_ref_df = dynamic_filters.filter_df()
filtered_ref_df.sort_values('time', ascending=False)

sel_stu = filtered_ref_df.iloc[0]['full_name']
sel_date = filtered_ref_df.iloc[0]['date']
filtered_dia_df = diagnosis_df[(diagnosis_df['full_name']==sel_stu) & (diagnosis_df['date']==sel_date)]


# section for student and project information
if not filtered_dia_df.empty:
    st.markdown('### ' + sel_stu)

    # section to display the most recent reflection
    st.markdown("#### Summary of your project information")


    col= ['project_information', 'current_focus', 'learning', 'obstacles', 'planning', 'coaching_outcome', 'emotions']
    # print("*****     shape of DF : ", filtered_ref_df.shape)
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

    st.markdown('##### Top 3 Risks diagnosed by system')
    # st.table(filtered_dia_df)
    st.markdown('Click on risks that you would like to discuss and get help from your coach in your next session.')
    list_diagnosed_risks = list(filtered_dia_df.columns)
    list_all_risks = list(risk_df.columns)

    # new_diag_df = []
    dia_dict = {}
    for col in filtered_dia_df.columns:
        if col in list_all_risks:
            items = filtered_dia_df.iloc[0][col]
            if isinstance(items, list):
                diag = [col, items[0], items[1], items[2]]
                dia_dict[col]=[items[0], items[1], items[2]]
                
            else:
                list_diagnosed_risks.remove(col)


    tab_labels = list(dia_dict.keys())
    tabs = st.tabs(tab_labels)
    for label, tab in zip(tab_labels, tabs):
        with tab:
            st.checkbox(":gray-background["+ dia_dict[label][0]+']', key=label)
            st.markdown(":blue[**Question Asked:** "+dia_dict[label][1] + ']')
            st.markdown(":green[ **Your Response:**]" + ":green[ "+dia_dict[label][2] + ']')

    st.markdown('---')
    st.markdown('##### Other general risks to consider')
    with st.expander("Click on risks that you would like to discuss with your coach in your next session."):
        
        for col in list_all_risks:
            if col not in list_diagnosed_risks:
                st.checkbox(":gray[ "+ col + ": " + risk_df.iloc[0][col] + ']', key=col)

    st.markdown('---')

    st.markdown("#### Coaching Agenda")
    risk_to_disucss = {}
    for risk in list_all_risks:
        is_clicked = st.session_state[risk]
        if is_clicked:
            st.markdown("* " +risk )
            if risk in dia_dict.keys():
                risk_to_disucss[risk]=dia_dict[risk]
            else:
                risk_to_disucss[risk]= risk_df.iloc[0][risk]


    with st.form('additional_risk'):
        
        stu_risk = st.text_input("Write down additional discussion points or relevant information that you would like to include in your agenda:", "")
        submitted = st.form_submit_button("Submit")
        if submitted:
            risk_to_disucss['student_submitted'] = stu_risk
            risk_to_disucss['full_name'] = sel_stu
            risk_to_disucss['date'] = sel_date
            ref.child('coaching_agenda').push().set(risk_to_disucss)
            st.write("Agenda saved! Thank you.")
            