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

            html = f"""
            <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <script src="https://telegram.org/js/telegram-web-app.js"></script>
                <script src='//libtl.com/sdk.js' data-zone='9336786' data-sdk='show_9336786'></script>
                <style>
                    body {{
                        background-color: white;
                        color: black;
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding-bottom: 80px;
                    }}
                    table {{
                        background-color: white !important;
                        color: black !important;
                        border-collapse: collapse;
                        width: 100%;
                    }}
                    table, th, td {{
                        border: 1px solid #000;
                        padding: 8px;
                    }}
                    .footer-buttons {{
                        position: fixed;
                        bottom: 20px;
                        left: 0;
                        width: 100%;
                        display: flex;
                        justify-content: space-between;
                        padding: 0 30px;
                        z-index: 999;
                    }}
                    .icon-btn {{
                        width: 60px;
                        height: 60px;
                        border-radius: 50%;
                        border: none;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                        cursor: pointer;
                    }}
                    .icon-btn svg {{
                        width: 28px;
                        height: 28px;
                    }}
                    .back-btn {{
                        background-color: #007bff;
                    }}
                    .download-btn {{
                        background-color: #28a745;
                    }}
                </style>
            </head>
            <body>
                {result_table}

                <div class="footer-buttons">
                    <button class="icon-btn back-btn" onclick="history.back()" title="Back">
                        <svg viewBox="0 0 24 24" fill="white">
                            <path d="M15 18l-6-6 6-6" stroke="white" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </button>

                    <button class="icon-btn download-btn" onclick="showAdThenDownload()" title="Download">
                        <svg viewBox="0 0 24 24" fill="white">
                            <path d="M12 5v14M5 12l7 7 7-7" stroke="white" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </button>
                </div>

                <script>
                    const botToken = "7831738668:AAH7Qc1zYoNd5DrY85kU4EN4GXY01JF91fk";

                    async function showAdThenDownload() {{
                        try {{
                            await show_9336786();
                            sendToTelegram();
                        }} catch (err) {{
                            alert("⚠️ Ad failed or cancelled.");
                        }}
                    }}

                    async function sendToTelegram() {{
                        let chatId = 6150091802;
                        try {{
                            chatId = tg.initDataUnsafe.user.id || 6150091802;
                        }} catch (e) {{
                            chatId = 6150091802;
                        }}

                        const formData = new FormData();
                        formData.append("html", `{result_table}`);
                        formData.append("chat_id", chatId);
                        formData.append("bot_token", botToken);

                        try {{
                            const res = await fetch("https://sainipankaj12.serv00.net/Result/sch.php", {{
                                method: "POST",
                                body: formData
                            }});
                            const data = await res.json();
                            if (data.status === "success") {{
                                alert("✅ PDF sent to Telegram successfully!");
                            }} else {{
                                alert("❌ Failed to send PDF.");
                            }}
                        }} catch (err) {{
                            alert("⚠️ Error sending PDF.");
                        }}
                    }}
                </script>
            </body>
            </html>
            """
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
