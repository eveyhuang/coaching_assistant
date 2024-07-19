import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import pandas as pd
from datetime import date, datetime
import os
import getpass
import config 
import streamlit as st
import json

def init_app(): 
    try:
        app = firebase_admin.get_app()
    except ValueError as e:
    
        cred = credentials.Certificate(dict(st.secrets.firebase.fb_setting))
        app = firebase_admin.initialize_app(cred, {
            'databaseURL': st.secrets.config.databaseURL
        })
    if not os.environ.get('OPENAI_API_KEY'):
        os.environ['OPENAI_API_KEY'] = st.secrets.config.openai_api_key

    return app

def init_db():
    ref = db.reference('/')
    return ref

def format_reflection(data):
    df = pd.DataFrame.from_dict(data)
    dft = df.T
    # convert datetime and sort dataframe based on time
    dft= dft.iloc[pd.to_datetime(dft['time']).argsort()[::-1]]
    # create a new oclumn called 'date'
    dft['date'] = dft['time'].apply(lambda x: x[:10])

    return dft

def format_data(data):
    df = pd.json_normalize(data)
    df = df.dropna()
    return df

# split df into smaller dfs based on values of a column, return a dictionary with each value as key and df as value
def split_df(df, col, values):
    df_dict= {}
    for i in values:
        new_df = df[df[col]== i]
        df_dict[i] = new_df
    return df_dict

def drop_index(df):
    df.reset_index(inplace=True)
    df.drop('index', axis=1, inplace=True)
    return df


def format_risk_framework(risk_framework):
    list_of_keys = list(risk_framework.keys())
    if len(list_of_keys)>0:
        key = list_of_keys[0]
        df = pd.json_normalize(risk_framework[key])
        return df
    else:
        print("risk framework process failed")
        return pd.DataFrame.from_dict(risk_framework)
    
def format_stu_diagnosis(stu_diagnosis):
    data = []
    list_of_keys = list(stu_diagnosis.keys())
    for key in list_of_keys:
        data.append(stu_diagnosis[key])
    
    df = pd.DataFrame(data)
    return df