from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
import mysql.connector
from mysql.connector import Error
import json
from werkzeug.security import generate_password_hash, check_password_hash
import requests # Para fazer requisições à API FastAPI
from typing import List, Dict, Any

app = Flask(__name__)
# CHAVE SECRETA CRÍTICA PARA SESSÕES E SEGURANÇA.
app.secret_key = 'acertus_super_secret_key_pro'

# --- Configurações ---

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'admin', # Altere com sua senha
    'database': 'acertus_db'
}

# URL base do servidor FastAPI
FASTAPI_BASE_URL = "http://localhost:8000"  

# --- Funções Auxiliares (IA e Banco) ---

def get_db_connection():
    """Tenta estabelecer a conexão com o banco de dados."""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
        return None

def fetch_form_with_questions(form_id, user_id=None):
    """Busca formulário e perguntas."""
    conn = get_db_connection()
    if not conn: return None, None
    cursor = conn.cursor(dictionary=True)

    # 1. Buscar formulário
    cursor.execute("SELECT id, title, description, user_id FROM forms WHERE id = %s", (form_id,))
    form = cursor.fetchone()
    
    if not form:
        conn.close()
        return None, None

    # Verifica permissão (se user_id for passado)
    if user_id and form['user_id'] != user_id:
        conn.close()
        return None, None

    # 2. Buscar perguntas
    cursor.execute("""
        SELECT id, form_id, question_text, question_type, is_required FROM questions
        WHERE form_id = %s
        ORDER BY order_index ASC
    """, (form_id,))
    questions = cursor.fetchall()

    # 3. Buscar opções
    for q in questions:
        q['options'] = []
        if q['question_type'] in ['multiple_choice', 'checkbox']:
            cursor.execute("SELECT id, option_text FROM question_options WHERE question_id = %s ORDER BY id", (q['id'],))
            q['options'] = cursor.fetchall()
    
    conn.close()
    return form, questions

def call_fastapi_full_analysis(texts: List[str]) -> Dict[str, Any]:
    """Chama a API FastAPI unificada para análise."""
    url = f"{FASTAPI_BASE_URL}/analyze/full"
    
    if not texts:
        return {
            "sentiment": {"positive": 0.0, "neutral": 0.0, "negative": 0.0},
            "summary": {"summary_text": "Sem respostas suficientes para análise."}
        }

    try:
        response = requests.post(url, json=texts, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"ERRO DE CONEXÃO com o FastAPI: {e}")
        return {
            "sentiment": {"positive": 0.0, "neutral": 0.0, "negative": 0.0},
            "summary": {"summary_text": f"ERRO ao conectar ao servidor de IA: {e}"}
        }

# --- Rotas de Autenticação ---

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        if not conn:
            flash('Erro de conexão com o banco.', 'danger')
            return render_template('login.html')
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            return redirect(url_for('dashboard'))
        else:
            flash('Email ou senha incorretos!', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        if not conn:
            return render_template('register.html')
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        
        if cursor.fetchone():
            flash('Conta já existe!', 'warning')
        else:
            hashed_password = generate_password_hash(password)
            try:
                cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_password))
                conn.commit()
                flash('Conta criada! Faça login.', 'success')
                return redirect(url_for('login'))
            except Error as e:
                flash(f'Erro: {e}', 'danger')
        conn.close()
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('login'))

# --- DASHBOARD (Com CORREÇÃO DE SQL) ---

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if not conn:
        flash('Erro de conexão com o banco.', 'danger')
        return redirect(url_for('logout'))

    cursor = conn.cursor(dictionary=True)
    user_id = session['user_id']
    
    # 1. Buscar Listas de Formulários
    cursor.execute("""
        SELECT f.*, 
        (SELECT COUNT(*) FROM responses r WHERE r.form_id = f.id) as response_count
        FROM forms f 
        WHERE f.user_id = %s 
        ORDER BY f.created_at DESC
    """, (user_id,))
    forms_created = cursor.fetchall()

    cursor.execute("""
        SELECT f.*, r.submitted_at
        FROM responses r
        JOIN forms f ON r.form_id = f.id
        WHERE r.user_id = %s
        GROUP BY f.id, r.submitted_at
        ORDER BY r.submitted_at DESC
    """, (user_id,))
    forms_answered = cursor.fetchall()

    # 2. CALCULAR ESTATÍSTICAS (STATS) para o novo HTML
    
    # A. Totais Simples
    total_forms_created = len(forms_created)
    total_forms_answered = len(forms_answered)
    total_responses_received = sum(f['response_count'] for f in forms_created)
    
    # Pendentes (Exemplo: Total Forms no sistema que não são meus e eu não respondi)
    cursor.execute("""
        SELECT COUNT(f.id) as pending
        FROM forms f
        WHERE f.user_id != %s 
        AND f.id NOT IN (SELECT form_id FROM responses WHERE user_id = %s)
    """, (user_id, user_id))
    pending_forms_count = cursor.fetchone()['pending']

    # B. Gráfico 1: Respostas por Mês (CORRIGIDO: ORDER BY MIN)
    cursor.execute("""
        SELECT DATE_FORMAT(r.submitted_at, '%b') as month_name, COUNT(r.id) as count
        FROM responses r
        JOIN forms f ON r.form_id = f.id
        WHERE f.user_id = %s
        GROUP BY DATE_FORMAT(r.submitted_at, '%Y-%m'), month_name
        ORDER BY MIN(r.submitted_at) ASC
        LIMIT 6
    """, (user_id,))
    month_data = cursor.fetchall()
    
    graph_labels = [row['month_name'] for row in month_data]
    graph_values = [row['count'] for row in month_data]
    
    if not graph_labels:
        graph_labels = ['Sem dados']
        graph_values = [0]

    # C. Montar objeto STATS
    stats = {
        'total_forms': total_forms_created,
        'total_responses': total_responses_received,
        'forms_answered_count': total_forms_answered,
        'forms_to_answer_count': pending_forms_count,
        
        'responses_by_month': {
            'labels': graph_labels,
            'data': graph_values
        },
        'forms_answered_distribution': {
            'labels': ['Respondidos', 'Pendentes'],
            'data': [total_forms_answered, pending_forms_count]
        }
    }
    
    conn.close()
    
    return render_template('dashboard.html',
        user_name=session['user_name'],
        forms_created=forms_created,
        forms_answered=forms_answered,
        stats=stats 
    )

# --- Gerenciamento de Formulários (CRUD + HTMX) ---

@app.route('/form/create', methods=['GET', 'POST'])
def create_form():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO forms (user_id, title, description) VALUES (%s, %s, %s)",
                           (session['user_id'], title, description))
            conn.commit()
            new_id = cursor.lastrowid
            conn.close()
            return redirect(url_for('edit_form', form_id=new_id))
            
    return render_template('create_form.html')

@app.route('/form/<int:form_id>/edit')
def edit_form(form_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    form, questions = fetch_form_with_questions(form_id, session['user_id'])
    if not form:
        flash('Acesso negado ou não encontrado.', 'danger')
        return redirect(url_for('dashboard'))
    return render_template('form_editor.html', form=form, questions=questions, json_dump=json.dumps)

@app.route('/form/<int:form_id>/delete', methods=['DELETE'])
def delete_form(form_id):
    if 'user_id' not in session: return jsonify({'error': '401'}), 401
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT user_id FROM forms WHERE id=%s", (form_id,))
        form = cursor.fetchone()
        if form and form['user_id'] == session['user_id']:
            cursor.execute("DELETE FROM forms WHERE id=%s", (form_id,))
            conn.commit()
            conn.close()
            return ('', 204) # Sucesso HTMX
        conn.close()
    return jsonify({'error': 'Erro'}), 500

# --- HTMX para Perguntas (Editor) ---

@app.route('/question/add/<int:form_id>', methods=['POST'])
def add_question(form_id):
    if 'user_id' not in session: return '', 401
    q_type = request.form['type']
    
    # Verifica dono do form
    form, _ = fetch_form_with_questions(form_id, session['user_id'])
    if not form: return '', 403

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT MAX(order_index) FROM questions WHERE form_id=%s", (form_id,))
    max_order = cursor.fetchone()[0] or 0
    
    cursor.execute("INSERT INTO questions (form_id, question_text, question_type, order_index) VALUES (%s, %s, %s, %s)",
                   (form_id, f"Nova Pergunta ({q_type})", q_type, max_order+1))
    conn.commit()
    new_qid = cursor.lastrowid
    
    new_q = {'id': new_qid, 'question_text': f"Nova Pergunta ({q_type})", 'question_type': q_type, 'options': [], 'is_required': 0}

    if q_type in ['multiple_choice', 'checkbox']:
        cursor.execute("INSERT INTO question_options (question_id, option_text) VALUES (%s, 'Opção 1')", (new_qid,))
        conn.commit()
        new_q['options'].append({'id': cursor.lastrowid, 'option_text': 'Opção 1'})
    
    conn.close()
    return render_template('question_partial.html', q=new_q, form_id=form_id, json_dump=json.dumps)

@app.route('/question/update/<int:question_id>', methods=['POST'])
def update_question(question_id):
    if 'user_id' not in session: return '', 401
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Verifica permissão
    cursor.execute("SELECT f.user_id FROM questions q JOIN forms f ON q.form_id=f.id WHERE q.id=%s", (question_id,))
    row = cursor.fetchone()
    if not row or row['user_id'] != session['user_id']:
        conn.close()
        return 'Erro', 403

    # Atualiza
    text = request.form.get('questionText')
    req = 1 if request.form.get('isRequired') == 'true' else 0
    opts = request.form.get('options_data')
    
    cursor.execute("UPDATE questions SET question_text=%s, is_required=%s WHERE id=%s", (text, req, question_id))
    
    if opts:
        import json
        options = json.loads(opts)
        cursor.execute("DELETE FROM question_options WHERE question_id=%s", (question_id,))
        for o in options:
            if o.get('text', '').strip():
                cursor.execute("INSERT INTO question_options (question_id, option_text) VALUES (%s, %s)", (question_id, o['text']))
    
    conn.commit()
    conn.close()
    return '<span class="saved-ok">Salvo!</span>', 200

@app.route('/question/delete/<int:question_id>', methods=['DELETE'])
def delete_question(question_id):
    if 'user_id' not in session: return '', 401
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT f.user_id FROM questions q JOIN forms f ON q.form_id=f.id WHERE q.id=%s", (question_id,))
    row = cursor.fetchone()
    if row and row['user_id'] == session['user_id']:
        cursor.execute("DELETE FROM questions WHERE id=%s", (question_id,))
        conn.commit()
        conn.close()
        return '', 200
    conn.close()
    return '', 403

# --- Área Pública (Responder e Ver Minha Resposta) ---

@app.route('/view/<int:form_id>')
def view_form(form_id):
    form, questions = fetch_form_with_questions(form_id)
    if not form:
        flash('Formulário não encontrado.', 'danger')
        return redirect(url_for('home'))
    return render_template('view_form.html', form=form, questions=questions)

@app.route('/form/submit/<int:form_id>', methods=['POST'])
def submit_form(form_id):
    form, questions = fetch_form_with_questions(form_id)
    if not form: return redirect(url_for('home'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    user_id = session.get('user_id')
    
    try:
        cursor.execute("INSERT INTO responses (form_id, user_id) VALUES (%s, %s)", (form_id, user_id))
        resp_id = cursor.lastrowid
        
        for q in questions:
            qid = q['id']
            if q['question_type'] == 'text':
                val = request.form.get(f"q_{qid}_text")
                if val: cursor.execute("INSERT INTO answers (response_id, question_id, answer_text) VALUES (%s,%s,%s)", (resp_id, qid, val))
            
            elif q['question_type'] == 'multiple_choice':
                val = request.form.get(f"q_{qid}_choice")
                if val: cursor.execute("INSERT INTO answers (response_id, question_id, option_id) VALUES (%s,%s,%s)", (resp_id, qid, val))
            
            elif q['question_type'] == 'checkbox':
                vals = request.form.getlist(f"q_{qid}_checkbox")
                for v in vals:
                    cursor.execute("INSERT INTO answers (response_id, question_id, option_id) VALUES (%s,%s,%s)", (resp_id, qid, v))
        
        conn.commit()
        return render_template('form_submitted.html', form=form)
    except Exception as e:
        conn.rollback()
        flash(f'Erro ao enviar: {e}', 'danger')
        return redirect(url_for('view_form', form_id=form_id))
    finally:
        conn.close()

# Rota para ver minha resposta
@app.route('/form/<int:form_id>/my-response')
def view_my_response(form_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    form, questions = fetch_form_with_questions(form_id)
    if not form: return redirect(url_for('dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Busca respostas do usuário
    cursor.execute("""
        SELECT a.question_id, a.answer_text, a.option_id
        FROM answers a
        JOIN responses r ON a.response_id = r.id
        WHERE r.form_id = %s AND r.user_id = %s
    """, (form_id, session['user_id']))
    raw_answers = cursor.fetchall()
    conn.close()

    user_answers = {}
    for ans in raw_answers:
        qid = ans['question_id']
        if qid not in user_answers: user_answers[qid] = {'text': None, 'options': []}
        if ans['answer_text']: user_answers[qid]['text'] = ans['answer_text']
        if ans['option_id']: user_answers[qid]['options'].append(ans['option_id'])

    return render_template('view_my_response.html', form=form, questions=questions, user_answers=user_answers)

# --- Resultados e Análise IA ---

@app.route('/form/<int:form_id>/results')
def form_results(form_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    # Apenas renderiza, o JS chama a API abaixo
    form, _ = fetch_form_with_questions(form_id, session['user_id'])
    if not form: return redirect(url_for('dashboard'))
    return render_template('form_results.html', form=form)

@app.route('/api/form/<int:form_id>/analysis', methods=['GET'])
def get_form_analysis_data(form_id):
    if 'user_id' not in session: return jsonify({"error": "401"}), 401
    
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Error"}), 500
    cursor = conn.cursor(dictionary=True)

    # Verifica permissão
    cursor.execute("SELECT id, title FROM forms WHERE id=%s AND user_id=%s", (form_id, session['user_id']))
    form = cursor.fetchone()
    if not form:
        conn.close()
        return jsonify({"error": "404"}), 404

    # Conta respostas atuais
    cursor.execute("SELECT COUNT(id) AS total FROM responses WHERE form_id=%s", (form_id,))
    total_resp = cursor.fetchone()['total']

    # Checa Cache
    cursor.execute("SELECT response_count, analysis_data FROM analysis_cache WHERE form_id=%s", (form_id,))
    cached = cursor.fetchone()
    
    if cached and cached['response_count'] == total_resp:
        conn.close()
        data = cached['analysis_data']
        if isinstance(data, str): data = json.loads(data)
        return jsonify(data)

    # GERA NOVA ANÁLISE
    _, questions = fetch_form_with_questions(form_id, session['user_id'])
    results = {
        "form_id": form['id'],
        "form_title": form['title'],
        "total_responses": total_resp,
        "questions_analysis": []
    }

    for q in questions:
        q_an = {"question_id": q['id'], "question_title": q['question_text'], "question_type": q['question_type'], "analysis_data": {}}
        
        if q['question_type'] == 'text':
            cursor.execute("SELECT answer_text FROM answers WHERE question_id=%s AND answer_text IS NOT NULL", (q['id'],))
            texts = [row['answer_text'] for row in cursor.fetchall() if row['answer_text'].strip()]
            
            # Chama IA
            ai_data = call_fastapi_full_analysis(texts) if texts else {"sentiment": {"positive":0,"neutral":0,"negative":0}, "summary": {"summary_text": "Sem dados"}}
            q_an['analysis_data'] = {"summary_text": ai_data['summary']['summary_text'], "sentiment": ai_data['sentiment'], "raw_responses": texts}

        elif q['question_type'] in ['multiple_choice', 'checkbox']:
            cursor.execute("""
                SELECT qo.option_text, COUNT(a.id) as cnt 
                FROM question_options qo 
                LEFT JOIN answers a ON qo.id=a.option_id 
                WHERE qo.question_id=%s GROUP BY qo.option_text ORDER BY cnt DESC
            """, (q['id'],))
            stats = cursor.fetchall()
            total_votes = sum(s['cnt'] for s in stats)
            q_an['analysis_data'] = {
                "chart_data": {
                    "labels": [s['option_text'] for s in stats],
                    "data": [round((s['cnt']/total_votes)*100, 1) if total_votes else 0 for s in stats]
                }
            }
        results['questions_analysis'].append(q_an)

    # Salva Cache
    try:
        json_data = json.dumps(results)
        cursor.execute("""
            INSERT INTO analysis_cache (form_id, response_count, analysis_data) VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE response_count=VALUES(response_count), analysis_data=VALUES(analysis_data)
        """, (form_id, total_resp, json_data))
        conn.commit()
    except Exception as e:
        print(f"Erro cache: {e}")

    conn.close()
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)