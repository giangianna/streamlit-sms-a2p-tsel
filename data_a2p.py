import streamlit as st
import pandas as pd
import altair as alt
import math

class A2P:
    # Class attribute
    sms = "Dashboard SMS International A2P Telkomsel"

    def __init__(self, name, age):
        # Instance attributes
        self.df_prev = name
        self.df_now = age

    # Instance method
    def init_data():
        df_prev_month = pd.read_csv('./data/A2P_Tsel_012024.csv', usecols=['Date','Partners','OA','Transactions'])
        df_this_month = pd.read_csv('./data/A2P_Tsel_022024.csv', usecols=['Date','Partners','OA','Transactions'])

        df = pd.concat([df_prev_month, df_this_month]).reset_index(drop=True)
        df['Partners'] = df['Partners'].str.upper()
        df['OA'] = df['OA'].str.upper()
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    
    def multiple_data(files):
        list_df = []
        for file in files:
            df = pd.read_csv(file, usecols=['Date','Partners','OA','Transactions'])
            list_df.append(df)
        df = pd.concat(list_df).reset_index(drop=True)

        df['Partners'] = df['Partners'].str.upper()
        df['OA'] = df['OA'].str.upper()
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    
    def mapping_facebook_group(df):
        fb_direct = df[df['Partners'] == 'FACEBOOK']
        fb_non_direct = df[(df['Partners'] != 'FACEBOOK') & (df.OA.isin(['FACEBOOK','INSTAGRAM','WHATSAPP']))]
        non_fb_group = df[(df['Partners'] != 'FACEBOOK') & (~df.OA.isin(['FACEBOOK','INSTAGRAM','WHATSAPP']))]

        pd.options.mode.copy_on_write = True

        fb_direct['FB Category'] = 'Facebook Direct'
        fb_non_direct['FB Category'] = 'Facebook Non Direct'
        non_fb_group['FB Category'] = 'Non Facebook Group'

        df = pd.concat([fb_direct, fb_non_direct, non_fb_group]).reset_index(drop=True)
        df['Date'] = pd.to_datetime(df['Date'])

        return df

    def pivot(df, target):
        pv_df = pd.pivot_table(df, values=['Transactions'], index=['Date'], columns=['FB Category'], aggfunc="sum", fill_value=0)
        pv_df = pv_df['Transactions']

        pv_df['Submission'] = pv_df['Facebook Direct'] + pv_df['Facebook Non Direct'] + pv_df['Non Facebook Group']
        pv_df['Target Initiatif'] = target

        return pv_df
    
    def graph_top_10_oa(df, selected_date, selected_oa):
        if selected_oa:
            # pivot tabel berdasarkan Kolom Transaksi dan Baris OA filter hari ini
            df_today = pd.pivot_table(df[(df["Date"] == selected_date) & (df["OA"].isin(selected_oa))], values='Transactions', index=['OA'], aggfunc="sum", fill_value=0)
            try: 
                top_oa_today = df_today.sort_values('Transactions',axis=0,ascending=False).head(len(selected_oa))
            except:
                st.warning('Tidak Ada Transaksi pada OA ini !', icon="⚠️")
        else:
            # pivot tabel berdasarkan Kolom Transaksi dan Baris OA filter hari ini
            df_today = pd.pivot_table(df[df["Date"] == selected_date], values='Transactions', index=['OA'], aggfunc="sum", fill_value=0)
            top_oa_today = df_today.sort_values('Transactions',axis=0,ascending=False).head(10)

        # daftar 10 oa teratas
        list_top_oa = top_oa_today.index.tolist()

        # data oa hari ini selain top 10
        oa_others = pd.pivot_table(df[(df["Date"] == selected_date) & (~df["OA"].isin(list_top_oa))], values='Transactions', index=['OA'], aggfunc="sum", fill_value=0)

        top_oa_today.loc['OTHERS'] = oa_others.sum()

        data_tsel = top_oa_today.reset_index()

        # Create a base chart
        base = alt.Chart(data_tsel).mark_arc(innerRadius=50).encode(
            theta="Transactions",
            color="OA:N",
            order=alt.Order("Transactions", sort='descending'),
        )

        # Create a pie chart
        pie = base.mark_arc(outerRadius=120)

        # Create a hole in the middle to make it a donut chart
        donut_oa = base.mark_arc(innerRadius=50, outerRadius=120)

        return top_oa_today, donut_oa
    
    def graph_top_10_partners(df, selected_date, selected_partners):
        if selected_partners:
            df_partner_today = pd.pivot_table(df[(df["Date"] == selected_date) & (df["Partners"].isin(selected_partners))], values='Transactions', index=['Partners'], aggfunc="sum", fill_value=0)
            try:
                top_partners_today = df_partner_today.sort_values('Transactions',axis=0,ascending=False).head(len(selected_partners))
            except:
                st.warning('Tidak Ada Transaksi pada Partner ini !', icon="⚠️")
        else:
            df_partner_today = pd.pivot_table(df[df["Date"] == selected_date], values='Transactions', index=['Partners'], aggfunc="sum", fill_value=0)
            top_partners_today = df_partner_today.sort_values('Transactions',axis=0,ascending=False).head(10)

        list_top_partners = top_partners_today.index.tolist()
        # data partners hari ini selain top 10
        partners_others = pd.pivot_table(df[(df["Date"] == selected_date) & (~df["Partners"].isin(list_top_partners))], values='Transactions', index=['Partners'], aggfunc="sum", fill_value=0)
        top_partners_today.loc['OTHERS'] = partners_others.sum()

        data_tsel = top_partners_today.reset_index()
        # Create a base chart
        base = alt.Chart(data_tsel).mark_arc(innerRadius=50).encode(
            theta="Transactions",
            color="Partners:N",
            order=alt.Order("Transactions", sort='descending'),
        )

        # Create a pie chart
        pie = base.mark_arc(outerRadius=120)

        # Create a hole in the middle to make it a donut chart
        donut = base.mark_arc(innerRadius=50, outerRadius=120)

        return top_partners_today, donut

    
    def growth_fb_category(df, selected_date, fb_category):

        today = selected_date
        yesterday = today - pd.Timedelta("1 day")
        last_week = today - pd.Timedelta("7 day")

        # perhitungan untuk fb direct
        pv_fb_direct = df[(df['FB Category'] == fb_category)]
        pv_fb_direct = pv_fb_direct.pivot_table(index=['Date'], columns=['OA'], values=['Transactions'], aggfunc="sum")

        growth_fb_direct = pv_fb_direct.filter(items=[today, yesterday, last_week], axis=0)
        growth_fb_direct = growth_fb_direct.transpose()
        growth_fb_direct = growth_fb_direct.reset_index(level="OA").set_index("OA")

        growth_fb_direct.loc['SUBTOTAL'] = growth_fb_direct.sum()

        growth_fb_direct['DoD'] = (growth_fb_direct[today] / growth_fb_direct[yesterday] -1) * 100
        growth_fb_direct['WoW'] = (growth_fb_direct[today] / growth_fb_direct[last_week] -1) * 100

        sum_fb_direct_last_month = pv_fb_direct.iloc[:int(today.strftime('%d')),:].sum().reset_index(level="OA").set_index("OA")
        sum_fb_direct_last_month.loc['SUBTOTAL'] = sum_fb_direct_last_month.sum()
        sum_fb_direct_this_month = pv_fb_direct.iloc[-int(today.strftime('%d')):,:].sum().reset_index(level="OA").set_index("OA")
        sum_fb_direct_this_month.loc['SUBTOTAL'] = sum_fb_direct_this_month.sum()

        growth_fb_direct['MoM'] = ((sum_fb_direct_this_month / sum_fb_direct_last_month) -1) * 100

        growth_fb_direct['Portion'] = (growth_fb_direct[today] / df[df['Date'] == today]['Transactions'].sum()) * 100
        growth_fb_direct['Portion DoD'] = (growth_fb_direct[today] / df[df['Date'] == today]['Transactions'].sum()) - (growth_fb_direct[yesterday] / df[df['Date'] == yesterday]['Transactions'].sum()) * 100
        growth_fb_direct['Portion WoW'] = (growth_fb_direct[today] / df[df['Date'] == today]['Transactions'].sum()) - (growth_fb_direct[last_week] / df[df['Date'] == last_week]['Transactions'].sum()) * 100

        sum_trx_this_month = df.pivot_table(index=['Date'], values=['Transactions'], aggfunc="sum").iloc[:int(today.strftime('%d')),:].sum().iloc[0]
        sum_trx_last_month = df.pivot_table(index=['Date'], values=['Transactions'], aggfunc="sum").iloc[-int(today.strftime('%d')):,:].sum().iloc[0]

        growth_fb_direct['Portion MoM'] = ((sum_fb_direct_this_month / sum_trx_this_month) - (sum_fb_direct_last_month / sum_trx_last_month)) * 100 

        growth_fb_direct = growth_fb_direct.drop(columns=[yesterday,last_week])
        growth_fb_direct = growth_fb_direct.rename(columns={today: "Submission"})

        # fungsi untuk merubah warna text growth
        def add_icon(value):
            if value > 0:
                return f'{value:,.1f} % 📈'
            elif value < 0:
                return f'{value:,.1f} % 📉'
            else:
                return f'{value:,.1f} %'
        
        def format_float(value):
            return f'{value:,.0f}'
        
        df_style = growth_fb_direct.style.format({'Submission':format_float, 'DoD': add_icon, 'WoW': add_icon, 'MoM': add_icon,
                                                 'Portion': add_icon, 'Portion DoD': add_icon, 'Portion WoW': add_icon, 'Portion MoM': add_icon})
        
        return df_style
    
    def growth_partners(df, selected_date):
        today = selected_date
        yesterday = today - pd.Timedelta("1 day")
        last_week = today - pd.Timedelta("7 day")
        # perhitungan growth untuk Partners
        pv_partners = df.pivot_table(index=['Date'], columns=['Partners'], values=['Transactions'], aggfunc="sum")

        growth_partners = pv_partners.filter(items=[today, yesterday, last_week], axis=0)
        growth_partners = growth_partners.transpose()
        growth_partners = growth_partners.reset_index(level="Partners").set_index("Partners")

        growth_partners.loc['SUBTOTAL'] = growth_partners.sum()

        growth_partners['DoD'] = (growth_partners[today] / growth_partners[yesterday] -1) * 100
        growth_partners['WoW'] = (growth_partners[today] / growth_partners[last_week] -1) * 100

        sum_partners_last_month = pv_partners.iloc[:int(today.strftime('%d')),:].sum().reset_index(level="Partners").set_index("Partners")
        sum_partners_last_month.loc['SUBTOTAL'] = sum_partners_last_month.sum()
        sum_partners_this_month = pv_partners.iloc[-int(today.strftime('%d')):,:].sum().reset_index(level="Partners").set_index("Partners")
        sum_partners_this_month.loc['SUBTOTAL'] = sum_partners_this_month.sum()

        growth_partners['MoM'] = ((sum_partners_this_month / sum_partners_last_month) -1) * 100

        growth_partners['Portion'] = (growth_partners[today] / df[df['Date'] == today]['Transactions'].sum()) * 100
        growth_partners['Portion DoD'] = (growth_partners[today] / df[df['Date'] == today]['Transactions'].sum()) - (growth_partners[yesterday] / df[df['Date'] == yesterday]['Transactions'].sum()) * 100
        growth_partners['Portion WoW'] = (growth_partners[today] / df[df['Date'] == today]['Transactions'].sum()) - (growth_partners[last_week] / df[df['Date'] == last_week]['Transactions'].sum()) * 100

        sum_trx_this_month = df.pivot_table(index=['Date'], values=['Transactions'], aggfunc="sum").iloc[:int(today.strftime('%d')),:].sum().iloc[0]
        sum_trx_last_month = df.pivot_table(index=['Date'], values=['Transactions'], aggfunc="sum").iloc[-int(today.strftime('%d')):,:].sum().iloc[0]

        growth_partners['Portion MoM'] = ((sum_partners_this_month / sum_trx_this_month) - (sum_partners_last_month / sum_trx_last_month)) * 100

        growth_partners = growth_partners.drop(columns=[yesterday,last_week])
        growth_partners = growth_partners.rename(columns={today: "Submission"})

        # fungsi untuk merubah warna text growth
        def add_icon(value):
            if value > 0:
                return f'{value:,.1f} % 📈'
            elif value < 0:
                return f'{value:,.1f} % 📉'
            else:
                return f'{value:,.1f} %'
        
        def format_float(value):
            return f'{value:,.0f}'
        
        df_style = growth_partners.style.format({'Submission':format_float, 'DoD': add_icon, 'WoW': add_icon, 'MoM': add_icon,
                                                 'Portion': add_icon, 'Portion DoD': add_icon, 'Portion WoW': add_icon, 'Portion MoM': add_icon})
        
        return df_style


