import streamlit as st
import yfinance as yf
ticker_symbol = 'BTC-USD'


ticker = yf.Ticker(ticker_symbol)


news = ticker.news
def display_news(news_data=news):
    for news_item in news_data:
        st.markdown(f"## {news_item['title']}")
        st.write(f"**Publisher:** {news_item['publisher']}")
        st.write(f"**Publish Time:** {news_item['providerPublishTime']}")
        st.write(f"**Link:** [{news_item['link']}]({news_item['link']})")
        if news_item.get('relatedTickers'):
            st.write(f"**Related Tickers:** {', '.join(news_item['relatedTickers'])}")
        if news_item.get('summary'):
            st.write(f"**Summary:** {news_item['summary']}")
        if news_item.get("thumbnail"):
            st.image(news_item['thumbnail']['resolutions'][0]['url'], width=400)
        st.write("----")