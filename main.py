from flask import Flask, request, jsonify, make_response
import requests
from bs4 import BeautifulSoup
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all domains

@app.route("/", methods=["GET"])
def fetch_result():
    roll_no = request.args.get("roll_no")
    query_string = request.query_string.decode()
    
    # Extract 'url=' part
    if "url=" not in query_string:
        return "Missing url parameter.", 400

    url_pos = query_string.find("url=")
    raw_url = query_string[url_pos + 4:]
    url = requests.utils.unquote(raw_url)

    if not roll_no or not url:
        return "Missing roll_no or url.", 400

    # Send POST request
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://rj-12-science-result.indiaresults.com',
        'Referer': 'https://rj-12-science-result.indiaresults.com/rj/bser/class-12-science-result-2022/query.htm',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    try:
        res = requests.post(url, data={"rollno": roll_no}, headers=headers, allow_redirects=True)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Find the result table
        table = soup.find("table", string=lambda t: t and "Personal Details" in t and "Final Result" in t)
        if not table:
            # fallback if string lambda didn't match due to encoding
            tables = soup.find_all("table")
            for t in tables:
                if "Personal Details" in t.get_text() and "Final Result" in t.get_text():
                    table = t
                    break

        if table:
            return make_response(str(table), 200)
        else:
            return make_response("Result Not Decleared! Please try again later", 400)

    except Exception as e:
        return make_response(f"Error occurred: {str(e)}", 500)

if __name__ == "__main__":
    app.run(debug=True)
