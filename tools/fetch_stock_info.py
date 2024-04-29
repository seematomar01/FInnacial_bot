import json
import time
from bs4 import BeautifulSoup
import re
import requests

from langchain.llms import OpenAI
from langchain.agents import load_tools, AgentType, Tool, initialize_agent
import yfinance as yf

import openai
import warnings
import os
warnings.filterwarnings("ignore")


os.environ["OPENAI_API_KEY"] = "YOUR KEY"


llm=OpenAI(temperature=0,
           model_name="gpt-3.5-turbo-16k-0613")


# Fetch stock data from Yahoo Finance
def get_stock_price(ticker,history=1000):
    # time.sleep(4) #To avoid rate limit error
    if "." in ticker:
        ticker=ticker.split(".")[0]
    #ticker=ticker+".NS"
    stock = yf.Ticker(ticker)
    df = stock.history(period="1y")
    df=df[["Close","Volume"]]
    df.index=[str(x).split()[0] for x in list(df.index)]
    df.index.rename("Date",inplace=True)
    df=df[-history:]
    # print(df.columns)
    
    return df.to_string()

# Script to scrap top5 googgle news for given company name
def google_query(search_term):
    if "news" not in search_term:
        search_term=search_term+" stock news"
    url=f"https://www.google.com/search?q={search_term}&cr=countryIN"
    url=re.sub(r"\s","+",url)
    return url

def get_recent_stock_news(company_name):
    # time.sleep(4) #To avoid rate limit error
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}

    g_query=google_query(company_name)
    res=requests.get(g_query,headers=headers).text
    soup=BeautifulSoup(res,"html.parser")
    news=[]
    for n in soup.find_all("div","n0jPhd ynAwRc tNxQIb nDgy9d"):
        news.append(n.text)
    for n in soup.find_all("div","IJl0Z"):
        news.append(n.text)

    if len(news)>6:
        news=news[:4]
    else:
        news=news
    news_string=""
    for i,n in enumerate(news):
        news_string+=f"{i}. {n}\n"
    top5_news="Recent News:\n\n"+news_string
    
    return top5_news


# Fetch financial statements from Yahoo Finance
# def get_financial_statements(ticker):
    time.sleep(4) #To avoid rate limit error
    # if "." in ticker:
        # ticker=ticker.split(".")[0]
    # else:
        # ticker=ticker
   #ticker=ticker+".NS"    
    # company = yf.Ticker(ticker)
    # balance_sheet = company.balance_sheet
    # if balance_sheet.shape[1]>=3:
        # balance_sheet=balance_sheet.iloc[:,:3]    # Remove 4th years data
    # balance_sheet=balance_sheet.dropna(how="any")
    # balance_sheet = balance_sheet.to_string()
    # return balance_sheet
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
    
#Openai function calling
function=[
        {
        "name": "get_company_Stock_ticker",
        "description": "This will get the indian NSE/BSE stock ticker of the company",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker_symbol": {
                    "type": "string",
                    "description": "This is the stock symbol of the company.",
                },

                "company_name": {
                    "type": "string",
                    "description": "This is the name of the company given in query",
                }
            },
            "required": ["company_name","ticker_symbol"],
        },
    }
]


def get_stock_ticker(query):
    response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            temperature=0,
            messages=[{
                "role":"user",
                "content":f"Given the user request, what is the comapany name and the company stock ticker ?: {query}?"
            }],
            functions=function,
            function_call={"name": "get_company_Stock_ticker"},
    )
    message = response["choices"][0]["message"]
    arguments = json.loads(message["function_call"]["arguments"])
    company_name = arguments["company_name"]
    company_ticker = arguments["ticker_symbol"]
    return company_name,company_ticker

def Anazlyze_stock(query):
    #agent.run(query) Outputs Company name, Ticker
    Company_name,ticker=get_stock_ticker(query)
    print({"Query":query,"Company_name":Company_name,"Ticker":ticker})
    stock_data=get_stock_price(ticker,history=1000)
    stock_financials=get_financial_statements(ticker)
    stock_news=get_recent_stock_news(Company_name)

    available_information=f"Stock Price: {stock_data}\n\nStock Financials: {stock_financials}\n\nStock News: {stock_news}"
    #available_information=f"Stock Financials: {stock_financials}\n\nStock News: {stock_news}"

    # print("\n\nAnalyzing.....\n")
    analysis=llm(f"Give detail stock analysis, Use the available data and provide investment recommendation. \
             The user is fully aware about the investment risk, dont include any kind of warning like 'It is recommended to conduct further research and analysis or consult with a financial advisor before making an investment decision' in the answer \
             User question: {query} \
             You have the following information available about {Company_name}. Write (10-12) pointwise investment analysis based on values available in {stock_financials} for analysis, make sure financial match with {stock_financials} i want only those value which are getting in this. At the end conclude with proper explaination.Try to Give positives and negatives  : \
              {available_information} "
             )
    # print(analysis)

    return analysis
