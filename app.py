from flask import Flask, request, jsonify
from search_engine import search_smartphones, get_filter_options
from flask import render_template


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
    

    results = search_smartphones(
        query=query,
        ram_min=ram_min,
        camera_min=camera_min,
        battery_min=battery_min,
        screen_min=screen_min,
        year=year
    )

    return render_template("results.html", results=results[:20], query=query)

@app.route("/filters", methods=["GET"])
def filters():
    options = get_filter_options()
    return jsonify(options)


if __name__ == "__main__":
    app.run(debug=True)
