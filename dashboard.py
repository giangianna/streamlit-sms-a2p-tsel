import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import numpy as np
from data_a2p import A2P
import yaml
from yaml.loader import SafeLoader

# Set the page configuration
st.set_page_config(layout="wide")
st.logo('images/telkomsel_logo.png', icon_image='images/icon-telkomsel-lama.png')
st.html("""
  <style>
    [alt=Logo] {
      height: 3rem;
    }
  </style>
        """)

with open('./config/config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

# Create a login widget
name, authentication_status, username = authenticator.login('sidebar')

if authentication_status:
    # Your Streamlit app code here
    df = A2P.init_data()
    df = A2P.mapping_facebook_group(df)

    col1, col2, col3 = st.columns([1,2,1])

    with col1:
        st.write(f'Welcome {name}')

    with col2:
        pass

    with col3:
        authenticator.logout('Logout', 'main')

    with st.sidebar:
        st.subheader('Silahkan upload file A2P BI Tellin')
        uploaded_files  = st.file_uploader('Choose a CSV file', accept_multiple_files=True)

        if uploaded_files:
            df = A2P.multiple_data(uploaded_files)
            df = A2P.mapping_facebook_group(df)
        
        st.subheader('Sample format CSV')
        def on_download():
            st.write("Download button clicked!")
        
        @st.cache_data
        def convert_df(df):
            # IMPORTANT: Cache the conversion to prevent computation on every rerun
            return df.to_csv(index=False).encode("utf-8")

        csv = convert_df(pd.read_csv('./data/A2P_Tsel_012024.csv'))

        st.download_button(
            label="Download Sample Data A2P",
            data=csv,
            file_name="A2P_Tsel_012024.csv",
            mime="text/csv",
            on_click=on_download
        )

        st.caption('Gian Gianna - Copyright (c) 2024 - v1.0')

    st.title(A2P.sms)

    tab2, tab3, tab4 = st.tabs(["Transactions A2P", "Top 10 OA and Partners", "Growth OA & Partners"])

    with tab2:
        st.subheader('Transactions A2P by Facebook Category')
        col1, col2 = st.columns([2, 2])
        with col1:
            # Mengambil start_date & end_date dari date_input
            start_date, end_date = st.date_input(
                label='Select Date Range',
                min_value=df['Date'].min(),
                max_value=df['Date'].max(),
                value=[df['Date'].min(), df['Date'].max()]
            )
        with col2:
            target = st.number_input(
                'Target Initiatif',
                min_value=100000,
                max_value=5000000,
                value=2250000,
                step=50000
            )
        
        pv_df = A2P.pivot(df, target)

        pv_df = pv_df[(pv_df.index >= pd.to_datetime(start_date)) & (pv_df.index <= pd.to_datetime(end_date))]
        st.line_chart(pv_df, x_label='Date')
        st.dataframe(data=pv_df)

    with tab3:
        st.subheader('Daily Top 10 OA')
        col1, col2 = st.columns([1, 1])
        with col1:
            selected_date_oa = st.date_input(label='Filter by Date', key='oa', 
                                             min_value=df['Date'].min(), 
                                             max_value=df['Date'].max(),
                                             value=df['Date'].max())
            selected_date_oa = pd.to_datetime(selected_date_oa)

            st.write(selected_date_oa.strftime("%d %B %Y"))

        with col2:
            selected_oa = st.multiselect(label='Filter By OA', options=df['OA'].sort_values().unique())
            # Display the selected options
            st.write('You selected:', selected_oa)

        col1, col2 = st.columns([2.5, 1])

        top_oa_today, donut_oa = A2P.graph_top_10_oa(df, selected_date_oa, selected_oa)

        with col1:
            # Display chart in Streamlit
            st.altair_chart(donut_oa, use_container_width=True)

        with col2:
            st.dataframe(data=top_oa_today)
        
        

        st.subheader('Daily Top 10 Partner')
        col1, col2 = st.columns([1, 1])
        with col1:
            selected_date_partners = st.date_input(label='Filter by Date', key='partners', min_value=df['Date'].min(), max_value=df['Date'].max())
            selected_date_partners = pd.to_datetime(selected_date_partners)

            st.write(selected_date_partners.strftime("%d %B %Y"))

        with col2:
            selected_partners = st.multiselect(label='Filter By Partner', options=df['Partners'].sort_values().unique())
            # Display the selected options
            st.write('You selected:', selected_partners)
        
        col1, col2 = st.columns([2.5, 1])

        top_partners_today, donut = A2P.graph_top_10_partners(df, selected_date_partners, selected_partners)

        with col1:
            # Display chart in Streamlit
            st.altair_chart(donut, use_container_width=True)

        with col2:
            st.dataframe(data=top_partners_today)

    with tab4:
        col1, col2 = st.columns([1, 3])
        with col1:
            selected_date = st.date_input(label='Filter by Date', key='growth', min_value=df['Date'].min(), max_value=df['Date'].max())
            selected_date = pd.to_datetime(selected_date)

            st.write(selected_date.strftime("%d %B %Y"))

        growth_fb_direct = A2P.growth_fb_category(df, selected_date, fb_category='Facebook Direct')

        st.subheader('Growth Facebook Direct')
        st.dataframe(data=growth_fb_direct)

        growth_fb_non_direct = A2P.growth_fb_category(df, selected_date, fb_category='Facebook Non Direct')
        st.subheader('Growth Facebook Non Direct')
        st.dataframe(data=growth_fb_non_direct)

        growth_non_fb = A2P.growth_fb_category(df, selected_date, fb_category='Non Facebook Group')
        st.subheader('Growth Non Facebook Group')
        st.dataframe(data=growth_non_fb)
        
        growth_partners = A2P.growth_partners(df, selected_date)
        st.subheader('Growth Partners')
        st.dataframe(data=growth_partners)
        # st.write(growth_partners.to_html(escape=False), unsafe_allow_html=True)

elif authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your username and password')




