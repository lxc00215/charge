import json
import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
DATA_FILE = 'data.json'

# 初始化数据文件
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump({}, f)

def load_data():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

# 1. 获取所有数据 (JSON URL形式)
@app.route('/api/data')
def get_data():
    return jsonify(load_data())

# 2. 新增记录
@app.route('/api/add', methods=['POST'])
def add_record():
    req = request.json
    location = req.get('location', '').strip()
    shop = req.get('shop', '').strip()
    amount = req.get('amount')
    note = req.get('note', '')

    if not location or not shop or not amount:
        return jsonify({"error": "信息不完整"}), 400

    data = load_data()
    
    # 确保层级存在
    if location not in data:
        data[location] = {}
    if shop not in data[location]:
        data[location][shop] = []

    new_record = {
        "id": str(uuid.uuid4()),
        "amount": amount,
        "note": note,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"), # 系统自动生成时间
        "is_paid": False # 默认为未还款
    }

    data[location][shop].insert(0, new_record) # 新记录放最前面
    save_data(data)
    return jsonify({"success": True})

# 3. 标记状态 (还钱/划掉)
@app.route('/api/toggle_status', methods=['POST'])
def toggle_status():
    req = request.json
    loc = req['location']
    shop = req['shop']
    r_id = req['id']

    data = load_data()
    records = data.get(loc, {}).get(shop, [])
    
    for r in records:
        if r['id'] == r_id:
            r['is_paid'] = not r['is_paid'] # 状态取反
            break
    
    save_data(data)
    return jsonify({"success": True})

# 4. 删除记录 (以防手误)
@app.route('/api/delete', methods=['POST'])
def delete_record():
    req = request.json
    loc = req['location']
    shop = req['shop']
    r_id = req['id']

    data = load_data()
    records = data.get(loc, {}).get(shop, [])
    
    # 过滤掉要删除的那一条
    data[loc][shop] = [r for r in records if r['id'] != r_id]
    
    # 如果店铺空了，删除店铺；如果镇空了，删除镇 (清理垃圾数据)
    if not data[loc][shop]:
        del data[loc][shop]
    if not data[loc]:
        del data[loc]

    save_data(data)
    return jsonify({"success": True})

if __name__ == '__main__':
    # host='0.0.0.0' 让局域网内其他手机也能访问
    app.run(debug=True, host='0.0.0.0', port=5000)