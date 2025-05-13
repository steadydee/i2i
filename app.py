from dotenv import load_dotenv
load_dotenv()   
import streamlit as st
from backend.graph import run_workflow
st.title("i2i demo")
prompt = st.text_input("What do you need?")

if prompt:
    st.write(run_workflow(prompt))
