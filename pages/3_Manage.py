import streamlit as st
import utils
import pandas as pd
import hmac

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


st.set_page_config(
    page_title='Edit and manage risk framework',
    initial_sidebar_state="expanded"
)

# load data from ref and do some manipulations 

def load_data(collection):
    data = ref.child(collection).get()    
    return data


# save data to firebase db
def savedata(df, location, key):
    cur_ref = ref.child(location)
    for index, row in df.iterrows():
        id_key = row[key]
        str_key = str(int(id_key))
        snapshot = cur_ref.order_by_child(key).equal_to(id_key).get()
        row_dict = row.to_dict()
        if snapshot:
            cur_ref.child(str_key).update(row_dict)
        else:
            cur_ref.child(str_key).set(row_dict)


# return df of updated and new rows
def diff_pd(df1, df2):
    diff_df= df1.merge(df2, how='outer', indicator=True).loc[lambda d: d.pop('_merge').eq('right_only')]
    return diff_df

# Risk framework
st.markdown("### Risk Framework")
risk_framework = ref.child('risk_framework').order_by_key().limit_to_last(1).get()
key = list(risk_framework.keys())[0]
# print("returned by firebase: ", risk_framework)
# print("key is : " + key)
risk_df = (pd.json_normalize(risk_framework[key])).T
risk_df.columns = ['description']
st.session_state.risk_df = risk_df


with st.form("risk_editor_form"):
    st.caption("Edit Risk Framework Below")
    st.session_state.edited_risk = st.data_editor(st.session_state.risk_df, use_container_width=True, num_rows="dynamic")
    submit_risk_button = st.form_submit_button("Submit")

if submit_risk_button:
    data= st.session_state.edited_risk.to_dict()
    keys = list(data.keys())
    if len(keys)>0:
        data = data[keys[0]]
        ref.child('risk_framework').push().set(data)
        st.markdown(":green[Saved new risk framework to database.]")
    else:
        st.write(":red[Failed to save risk framework to databse.]")
    
    # print("Saved to firebase: ", data[0])
    

# #Student data
# st.markdown("### Add and Edit Student Information")
# student_data = load_data('students')
# student_df = pd.json_normalize(student_data)

# with st.form("student_editor_form"):
#     st.caption("Edit Student Information Below")
#     edited_student = st.data_editor(student_df, use_container_width=True, num_rows="dynamic")
#     submit_student_button = st.form_submit_button("Submit")

# if submit_student_button:
#     # savedata(edited_group.to_dict(), 'groups')
#     # new_data = [None, {'coach': 'Mike', 'id': 1, 'meeting_time': 'Wednesday 2-3pm', 'quarter': 'Fall 2024'}, {'coach': 'Mike', 'id': 2, 'meeting_time': 'Thursday 1-2pm', 'quarter': 'Fall 2024'}, {'coach': 'Mike', 'id': 3, 'meeting_time': 'Thursday 1-2pm', 'quarter': 'Spring 2024'}]
#     m = diff_pd(student_df, edited_student)
#     print("difference: ", m)
#     savedata(m, 'students', 'student_id')


# #GROUP data
# st.markdown("### Add and Edit Coaching Groups")
# group_data = load_data('groups')
# group_df = pd.json_normalize(group_data)


# with st.form("group_editor_form"):
#     st.caption("Edit Group Information Below")
#     edited_group = st.data_editor(group_df, use_container_width=True, num_rows="dynamic")
#     submit_group_button = st.form_submit_button("Submit")

# if submit_group_button:
#     # savedata(edited_group.to_dict(), 'groups')
#     # new_data = [None, {'coach': 'Mike', 'id': 1, 'meeting_time': 'Wednesday 2-3pm', 'quarter': 'Fall 2024'}, {'coach': 'Mike', 'id': 2, 'meeting_time': 'Thursday 1-2pm', 'quarter': 'Fall 2024'}, {'coach': 'Mike', 'id': 3, 'meeting_time': 'Thursday 1-2pm', 'quarter': 'Spring 2024'}]
#     m = diff_pd(group_df, edited_group)
#     savedata(m, 'groups', 'id')