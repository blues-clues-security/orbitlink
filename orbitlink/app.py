from flask import *
from flask_cors import CORS
from scapy.all import *

app = Flask(__name__)
CORS(app)

@app.route('/ttc', methods=['GET'])
def get_ttc():
    with open("data/ttc.json", "r") as f:
        ttc_data = json.load(f)

    return jsonify({
        'ttc_data': ttc_data,
        })

@app.route('/sosi', methods=['GET'])
def get_sosi():
    with open("data/sosi.json", "r") as f:
        sosi_data = json.load(f)
        
    return jsonify({
        'sosi_data': sosi_data,
        })

@app.route('/imagery', methods=['GET'])
def get_imagery():
    with open("data/imagery.json", "r") as f:
        imagery_data = json.load(f)

    return jsonify({
        'imagery_data': imagery_data,
        })

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)