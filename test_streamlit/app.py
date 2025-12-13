import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title=f"Hello test_streamlit",
    page_icon=":wave:",
)

st.title("Welcome to Streamlit! :wave:")

st.markdown(
    """
    Streamlit is an open-source app framework built specifically for
    Machine Learning and Data Science projects.
    """
)

if st.button('Click me'):
    st.write('You clicked the button!')

st.header("Sample Data")
chart_data = pd.DataFrame(
    np.random.randn(20, 3),
    columns=['a', 'b', 'c']
)

st.line_chart(chart_data)
