import streamlit as st
import tools
from tools.fetch_stock_info import Anazlyze_stock
import yfinance as yf
st.title("Stock Analysis bot")
st.write("This bot scraps and gathers real time stock realted information and analyzes it using LLM")

ticker = st.text_input('Enter Ticker Symbol (e.g., AAPL, MSFT):')

import pandas as pd
def get_financial_statements(ticker):
# time.sleep(4) #To avoid rate limit error
    if "." in ticker:
        ticker=ticker.split(".")[0]
    else:
        ticker=ticker
    #ticker=ticker+".NS"    
    company = yf.Ticker(ticker)
    balance_sheet = company.balance_sheet
    Income_Statement= company.income_stmt 
    Dividend_payout= company.dividends
    cash_flow = company.cash_flow
    
    if balance_sheet.shape[1]>=3:
        balance_sheet=balance_sheet.T  # Remove 4th years data
        Income_Statement = Income_Statement.T
       # Dividend_payout = Dividend_payout
        cash_flow = cash_flow.T
    
    result = pd.concat([balance_sheet, Income_Statement, cash_flow], axis=1)
    resultsss = result[['Basic EPS','Gross Profit','Net Income From Continuing Operations','EBITDA','Total Assets','Total Liabilities Net Minority Interest','Total Debt','Operating Income','Operating Expense','Free Cash Flow']]
    return resultsss

Enter=st.button("Enter")
if Enter:
    resultsss = get_financial_statements(ticker)
    st.write(resultsss)
    
clear=st.button("Clear")

if clear:
    print(clear)
    st.markdown(' ')

if Enter:
    import time
    with st.spinner('Gathering all required information and analyzing. Be patient!!!!!'):
        out=Anazlyze_stock(ticker)
    st.success('Done!')
    st.write(out)


