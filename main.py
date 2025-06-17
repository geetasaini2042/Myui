from flask import Flask, request, jsonify, make_response
import requests
from bs4 import BeautifulSoup
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

# 1️⃣ Existing App Details Endpoint (by package)
@app.route('/api/app-details', methods=['GET'])
def app_details():
    package_name = request.args.get('package')
    from google_play_scraper import app
    get_app = app
    if not package_name:
        return jsonify({"error": "Package name is required"}), 400

    try:
        result = get_app(package_name, lang='hi', country='us')
        return result
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 2️⃣ New App Search Endpoint (by query)
@app.route('/api/app-search', methods=['GET'])
def app_search():
    from google_play_scraper import search
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    try:
       result = search(
         query,
         country="us",  # defaults to 'us'
         n_hits=10  # defaults to 30 (= Google's maximum)
          )
      # print(result)
       return result
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/result", methods=["GET"])
def get_result():
    roll_no = request.args.get("roll_no")
    wb_id = request.args.get("wb_id")
    year = request.args.get("year")

    if not roll_no or not wb_id or not year:
        return jsonify({"status": "failed", "message": "Missing parameters"}), 400

    primary_url = (
        f"https://result.appanalytics.co.in/api/get-result"
        f"?tag=raj_10th_result&roll_no={roll_no}&year={year}&wb_id={wb_id}&source=1"
    )

    primary_json = None
    fallback_json = None

    # Try primary API
    try:
        primary_res = requests.get(primary_url, timeout=5)
        if primary_res.status_code >= 500:
            raise Exception("Server error on primary URL")

        try:
            primary_json = primary_res.json()
        except json.JSONDecodeError:
            raise Exception("Invalid JSON from primary URL")

        if primary_json.get("status") == "success":
            return jsonify(primary_json), 200

    except Exception as e:
        print("Primary request failed:", str(e))

    # Try fallback based on wb_id
    try:
        if wb_id == "89":
            fallback_url = f"https://www.fastresult.in/board-results/rajresultapi12/api/get-12th-result?roll_no={roll_no}"
        elif wb_id == "88":
            fallback_url = f"https://www.fastresult.in/board-results/rajresultapi10/api/get-10th-result?roll_no={roll_no}"
        else:
            return jsonify({"status": "failed", "message": "Invalid wb_id"}), 400

        fallback_res = requests.get(fallback_url, timeout=5)
        fallback_json = fallback_res.json()

        if fallback_json.get("status") == "success":
            return jsonify(fallback_json), 200
        else:
            return jsonify(fallback_json), 400

    except Exception as e:
        return jsonify({"status": "failed", "message": f"Fallback also failed: {str(e)}"}), 502

    return jsonify({"status": "failed", "message": "Result not found"}), 400



@app.route("/", methods=["GET"])
def fetch_result():
    roll_no = request.args.get("roll_no")
    query_string = request.query_string.decode()

    if "url=" not in query_string:
        return "Missing url parameter.", 400

    url_pos = query_string.find("url=")
    raw_url = query_string[url_pos + 4:]
    url = requests.utils.unquote(raw_url)

    if not roll_no or not url:
        return "Missing roll_no or url.", 400

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://rj-12-science-result.indiaresults.com',
        'Referer': 'https://rj-12-science-result.indiaresults.com/rj/bser/class-12-science-result-2022/query.htm',
        'User-Agent': 'Mozilla/5.0',
    }

    try:
        res = requests.post(url, data={"rollno": roll_no}, headers=headers, allow_redirects=True)
        soup = BeautifulSoup(res.text, 'html.parser')

        table = soup.find("table", string=lambda t: t and "Personal Details" in t and "Final Result" in t)
        if not table:
            tables = soup.find_all("table")
            for t in tables:
                if "Personal Details" in t.get_text() and "Final Result" in t.get_text():
                    table = t
                    break

        if table:
            result_table = str(table)
            #safe_table = result_table.replace("\\", "\\\\").replace("`", "\\`").replace("</script>", "<\\/script>")
            html = f"{result_table}"

            
            return make_response(html, 200)
        else:
            return make_response("""
            <html>
            <body style="background:white;font-family:sans-serif;text-align:center;margin-top:50px;">
                <h2>❌ Result Not Declared! Please try again later.</h2>
                <button onclick="history.back()" style="padding:10px 20px;background:#007bff;color:white;border:none;border-radius:5px;">🔙 Go Back</button>
            </body>
            </html>
            """, 400)

    except Exception as e:
        return make_response(f"Error occurred: {str(e)}", 500)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
