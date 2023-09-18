from flask import Flask, jsonify, request
from sixth.sdk import Sixth

app = Flask(__name__)

# Define some example routes
@app.route("/")
def index():
    return "Home Page"

@app.route("/about")
def about():
    return "About Page"

@app.route("/contact")
def contact():
    return {
        "ope":request.args.get("ope")
    }

@app.route('/post_example/', methods=['POST'])
def post_example():
    # Access the data sent in the request's JSON body
    print("request coming in is ", request.get_json())
    data = request.get_json()

    # Process the data (in this example, we'll simply return it)
    return jsonify(data)



app = Sixth("YVawS7tr1SaBmeG4NVZt3OniEw52", app).init()
if __name__ == "__main__":
    app.run()