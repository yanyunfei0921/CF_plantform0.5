from flask import Flask
from flask import render_template
from flask import request
from flask import send_from_directory

app = Flask(__name__,static_folder="static",template_folder="templates")

app.jinja_env.variable_start_string="**DIM LIGHT**"
app.jinja_env.variable_end_string="**DIM LIGHT**"

@app.route('/')
def index():
    return render_template('index.html')

@app.after_request
def add_no_cache_header(response):
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
    return response

if __name__ == '__main__':
    app.run(debug=True)