from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from groq import Groq

# API Keys
ALPHA_VANTAGE_API_KEY = "0UJ6Y46VWBK8EU7B"
client = Groq(api_key="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")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

def get_stock_news(symbol):
    """Fetch news headlines for the stock symbol using Alpha Vantage API."""
    try:
        url = f"https://www.alphavantage.co/query"
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": symbol,
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        news_data = response.json()

        if "feed" in news_data:
            return [article["title"] for article in news_data["feed"]]
        else:
            return ["No recent news found."]
    except Exception as e:
        print("Error fetching news:", e)
        return [f"Unable to retrieve news: {str(e)}"]

def analyze_news_with_groq(news_headlines):
    """Send news headlines to GROQ API to analyze for summary and recommendation."""
    headlines_text = "\n".join(news_headlines)
    conversation_history = [
        {
            "role": "system",
            "content": "You are a financial analysis assistant. Summarize the following news and provide a single-word recommendation: 'Buy' or 'Sell'."
        },
        {
            "role": "user",
            "content": headlines_text
        }
    ]
    
    try:
        chat_completion = client.chat.completions.create(
            messages=conversation_history,
            model="llama3-70b-8192",
            temperature=0.5,
            max_tokens=1024,
            top_p=1
        )
        response = chat_completion.choices[0].message.content.strip()
        return "Buy" if "Buy" in response else "Sell"
    except Exception as e:
        print("Error analyzing news with GROQ:", e)
        return "Unable to retrieve analysis."

@app.route('/api/get_news', methods=['POST', 'OPTIONS'])
def fetch_news():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'preflight passed'}), 200

    request_data = request.get_json()
    stock_symbol = request_data.get("stockSymbol", "").upper()

    if not stock_symbol:
        return jsonify({'error': 'No stock symbol provided'}), 400

    news_headlines = get_stock_news(stock_symbol)
    if "Unable to retrieve" in news_headlines[0]:
        return jsonify({'error': news_headlines[0]}), 500

    analysis = analyze_news_with_groq(news_headlines)

    return jsonify({
        'stockSymbol': stock_symbol,
        'newsHeadlines': news_headlines,
        'analysis': analysis
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5001)
