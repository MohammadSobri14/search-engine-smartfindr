from flask import Flask, request, jsonify, render_template
from search_engine import search_smartphones, get_filter_options, data_df
import math

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/search")
def search_page():
    query = request.args.get("q", "").lower()
    ram_min = request.args.get("ram_min", type=int)
    camera_min = request.args.get("camera_min", type=int)
    battery_min = request.args.get("battery_min", type=int)
    screen_min = request.args.get("screen_min", type=float)
    year = request.args.get("year", type=int)
    sort_by = request.args.get("sort_by", "similarity")
    order = request.args.get("order", "desc")
    page = request.args.get("page", default=1, type=int)
    per_page = 10

    all_results = search_smartphones(
        query=query,
        ram_min=ram_min,
        camera_min=camera_min,
        battery_min=battery_min,
        screen_min=screen_min,
        year=year,
        sort_by=sort_by,
        order=order
    )

    total_results = len(all_results)
    total_pages = max(math.ceil(total_results / per_page), 1)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_results = all_results[start:end]

    return render_template(
        "results.html",
        results=paginated_results,
        query=query,
        sort_by=sort_by,
        order=order,
        current_page=page,
        total_pages=total_pages
    )

@app.route("/filters", methods=["GET"])
def filters():
    options = get_filter_options()
    return jsonify(options)

@app.route("/suggest")
def suggest():
    query = request.args.get("q", "").lower()
    if not query:
        return jsonify([])

    df = data_df.copy()
    df = df[df['name'].str.lower().str.contains(query)]
    suggestions = df[['name', 'image_url']].drop_duplicates().head(5).to_dict(orient="records")
    return jsonify(suggestions)

if __name__ == "__main__":
    app.run(debug=True)
