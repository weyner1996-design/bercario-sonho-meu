from flask import Flask, request, jsonify, render_template
import json, os, socket
from datetime import datetime

app = Flask(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL', '')
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dados.json')

# ── banco de dados ──────────────────────────────────────────
def get_db():
    if DATABASE_URL:
        try:
            import psycopg2
            return psycopg2.connect(DATABASE_URL)
        except Exception as e:
            print('[DB]', e)
    return None

def init_db():
    conn = get_db()
    if conn:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS storage (
                key TEXT PRIMARY KEY,
                value TEXT,
                ts TIMESTAMP DEFAULT NOW()
            )
        ''')
        conn.commit()
        cur.close()
        conn.close()
        print('[DB] PostgreSQL pronto')
    else:
        print('[DB] Usando arquivo local')

def db_get_all():
    conn = get_db()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('SELECT key, value FROM storage')
            rows = cur.fetchall()
            cur.close()
            conn.close()
            result = {}
            for k, v in rows:
                try:
                    result[k] = json.loads(v)
                except:
                    result[k] = v
            return result
        except Exception as e:
            print('[DB]', e)
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}

def db_set(key, value):
    conn = get_db()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO storage (key, value, ts)
                VALUES (%s, %s, NOW())
                ON CONFLICT (key) DO UPDATE
                SET value = EXCLUDED.value, ts = NOW()
            ''', (key, json.dumps(value, ensure_ascii=False)))
            conn.commit()
            cur.close()
            conn.close()
            return
        except Exception as e:
            print('[DB]', e)
    try:
        dados = {}
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                dados = json.load(f)
        dados[key] = value
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False)
    except Exception as e:
        print('[FILE]', e)

def db_delete(key):
    conn = get_db()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('DELETE FROM storage WHERE key = %s', (key,))
            conn.commit()
            cur.close()
            conn.close()
            return
        except Exception as e:
            print('[DB]', e)
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            dados.pop(key, None)
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(dados, f, ensure_ascii=False)
    except:
        pass

# ── rotas ───────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/load')
def api_load():
    return jsonify(db_get_all())

@app.route('/api/save', methods=['POST'])
def api_save():
    try:
        b = request.get_json(force=True)
        db_set(b['key'], b['value'])
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'erro': str(e)}), 500

@app.route('/api/delete', methods=['POST'])
def api_delete():
    try:
        b = request.get_json(force=True)
        db_delete(b['key'])
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'erro': str(e)}), 500

@app.route('/api/status')
def api_status():
    d = db_get_all()
    return jsonify({
        'ok': True,
        'app': 'Berçário Sonho Meu',
        'banco': 'PostgreSQL' if DATABASE_URL else 'Local',
        'chaves': len(d),
        'ts': datetime.now().isoformat()
    })

# ── inicialização ────────────────────────────────────────────
with app.app_context():
    init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    if port == 5000:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
        except:
            ip = '127.0.0.1'
        print(f'\n🌙 BERÇÁRIO SONHO MEU')
        print(f'  Computador : http://localhost:5000')
        print(f'  Celular    : http://{ip}:5000\n')
    app.run(host='0.0.0.0', port=port, debug=False)
