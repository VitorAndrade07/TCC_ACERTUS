from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
import mysql.connector
from mysql.connector import Error
import json
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# CHAVE SECRETA CRÍTICA PARA SESSÕES E SEGURANÇA. MUDE EM PRODUÇÃO!
app.secret_key = 'acertus_super_secret_key_pro'
 
# Configuração do Banco de Dados
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'admin', # Altere com sua senha de banco de dados
    'database': 'acertus_db'
}
 
def get_db_connection():
    """Tenta estabelecer a conexão com o banco de dados."""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
        return None
 
# --- Helpers de Banco de Dados ---
 
def fetch_form_with_questions(form_id, user_id=None):
    """
    Busca um formulário, suas perguntas e opções.
    Esta função garante que o texto da pergunta mais recente seja buscado.
    """
    conn = get_db_connection()
    if not conn: return None, None
    cursor = conn.cursor(dictionary=True)
 
    # 1. Buscar formulário
    cursor.execute("SELECT id, title, description, user_id FROM forms WHERE id = %s", (form_id,))
    form = cursor.fetchone()
   
    if not form:
        conn.close()
        return None, None
 
    # Verifica permissão do usuário (apenas se user_id for fornecido, como na rota de edição)
    if user_id and form['user_id'] != user_id:
        conn.close()
        return None, None
 
    # 2. Buscar perguntas
    # ESSA QUERY RECUPERA O 'question_text' ATUALIZADO
    cursor.execute("""
        SELECT id, form_id, question_text, question_type, is_required FROM questions
        WHERE form_id = %s
        ORDER BY order_index ASC
    """, (form_id,))
    questions = cursor.fetchall()
 
    # 3. Buscar opções para cada pergunta (se aplicável)
    for q in questions:
        q['options'] = []
        if q['question_type'] in ['multiple_choice', 'checkbox']:
            cursor.execute("SELECT id, option_text FROM question_options WHERE question_id = %s ORDER BY id", (q['id'],))
            q['options'] = cursor.fetchall()
   
    conn.close()
    return form, questions
 
# --- Rotas de Autenticação e Dashboard ---
 
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
            flash('Erro de conexão com o banco de dados.', 'danger')
            return render_template('login.html')
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        conn.close()
        # Verificação segura de senha
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
            flash('Erro de conexão com o banco de dados.', 'danger')
            return render_template('register.html')
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        if user:
            flash('Conta já existe com este email!', 'warning')
        else:
            # GERA O HASH SEGURO DA SENHA
            hashed_password = generate_password_hash(password)
            try:
                cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_password))
                conn.commit()
                flash('Conta criada com sucesso! Faça login.', 'success')
                return redirect(url_for('login'))
            except Error as e:
                flash(f'Ocorreu um erro ao registrar: {e}', 'danger')
        conn.close()
    return render_template('register.html')
 
@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('login'))
 
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
   
    conn = get_db_connection()
    if not conn:
        flash('Erro de conexão com o banco de dados.', 'danger')
        return redirect(url_for('logout'))
 
    cursor = conn.cursor(dictionary=True)
   
    # Formulários Criados
    cursor.execute("SELECT * FROM forms WHERE user_id = %s ORDER BY created_at DESC", (session['user_id'],))
    forms_created = cursor.fetchall()
 
    # Formulários Respondidos
    cursor.execute("""
        SELECT f.*, r.submitted_at
        FROM responses r
        JOIN forms f ON r.form_id = f.id
        WHERE r.user_id = %s
        GROUP BY f.id, r.submitted_at
        ORDER BY r.submitted_at DESC
    """, (session['user_id'],))
    forms_answered = cursor.fetchall()
   
    conn.close()
   
    return render_template('dashboard.html',
        user_name=session['user_name'],
        forms_created=forms_created,
        forms_answered=forms_answered
    )
 
# --- Rotas de Gerenciamento de Formulário ---
 
@app.route('/form/create', methods=['GET', 'POST'])
def create_form():
    if 'user_id' not in session:
        return redirect(url_for('login'))
   
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        user_id = session['user_id']
       
        conn = get_db_connection()
        if not conn:
            flash('Erro de conexão com o banco de dados.', 'danger')
            return redirect(url_for('create_form'))
 
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO forms (user_id, title, description) VALUES (%s, %s, %s)",
                           (user_id, title, description))
            conn.commit()
            new_form_id = cursor.lastrowid
            flash('Formulário criado! Agora configure as perguntas.', 'success')
            return redirect(url_for('edit_form', form_id=new_form_id))
        except Error as e:
            flash(f'Ocorreu um erro ao criar o formulário: {e}', 'danger')
        finally:
            conn.close()
           
    return render_template('create_form.html')
 
@app.route('/form/<int:form_id>/edit')
def edit_form(form_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
   
    # Busca o formulário e verifica permissão
    form, questions = fetch_form_with_questions(form_id, session['user_id'])
 
    if not form:
        flash('Formulário não encontrado ou você não tem permissão para editá-lo.', 'danger')
        return redirect(url_for('dashboard'))
   
    # Usa json.dumps para passar opções de forma segura para o front-end
    return render_template('form_editor.html', form=form, questions=questions, json_dump=json.dumps)
 
# --- HTMX/API: Operações no Editor ---
 
@app.route('/question/add/<int:form_id>', methods=['POST'])
def add_question(form_id):
    """Adiciona uma nova pergunta via requisição HTMX e retorna o HTML parcial."""
    if 'user_id' not in session:
        return '', 401
   
    question_type = request.form['type']
   
    # 1. Verifica permissão
    form, _ = fetch_form_with_questions(form_id, session['user_id'])
    if not form:
        return '', 403
 
    conn = get_db_connection()
    if not conn: return '', 500
    cursor = conn.cursor()
   
    try:
        # Pega a próxima ordem
        cursor.execute("SELECT MAX(order_index) FROM questions WHERE form_id = %s", (form_id,))
        max_order = cursor.fetchone()[0]
        new_order = (max_order or 0) + 1
       
        # Insere a nova pergunta
        cursor.execute(
            "INSERT INTO questions (form_id, question_text, question_type, order_index) VALUES (%s, %s, %s, %s)",
            (form_id, f"Nova Pergunta de {question_type.replace('_', ' ').title()}", question_type, new_order)
        )
        conn.commit()
        new_question_id = cursor.lastrowid
 
        # Prepara a pergunta para renderização
        new_question = {
            'id': new_question_id,
            'question_text': f"Nova Pergunta de {question_type.replace('_', ' ').title()}",
            'question_type': question_type,
            'options': [],
            'is_required': 0
        }
 
        # Se for múltipla escolha/checkbox, adiciona uma opção padrão e a retorna
        if question_type in ['multiple_choice', 'checkbox']:
            cursor.execute(
                "INSERT INTO question_options (question_id, option_text) VALUES (%s, %s)",
                (new_question_id, "Opção Padrão 1")
            )
            conn.commit()
            new_option_id = cursor.lastrowid
            new_question['options'].append({'id': new_option_id, 'option_text': 'Opção Padrão 1'})
           
        conn.close()
       
        # Retorna o template parcial para HTMX
        return render_template('question_partial.html', q=new_question, form_id=form_id, json_dump=json.dumps)
       
    except Error as e:
        print(f"Erro ao adicionar pergunta: {e}")
        conn.close()
        return 'Erro interno ao adicionar pergunta', 500
 
@app.route('/question/update/<int:question_id>', methods=['POST'])
def update_question(question_id):
    """
    Atualiza o texto da pergunta e suas opções (via HTMX).
    CORRIGIDO: Utiliza 'questionText' e 'isRequired' (nomes do Alpine.js) e garante o commit.
    """
    if 'user_id' not in session:
        return '', 401
 
    conn = get_db_connection()
    if not conn: return 'Erro de conexão', 500
    cursor = conn.cursor(dictionary=True)
 
    # 1. Obter form_id e verificar permissão (SEGURANÇA CRÍTICA)
    cursor.execute("""
        SELECT f.user_id, q.question_type
        FROM questions q
        JOIN forms f ON q.form_id = f.id
        WHERE q.id = %s
    """, (question_id,))
    question_info = cursor.fetchone()
   
    if not question_info or question_info['user_id'] != session['user_id']:
        conn.close()
        return 'Não autorizado ou pergunta não encontrada', 403
 
    # 2. Coletar dados da requisição (USANDO NOMES CORRETOS DO ALPINE/HTMX)
    new_text = request.form.get('questionText')
    options_data_str = request.form.get('options_data')
    is_required = 1 if request.form.get('isRequired') == 'true' else 0
 
    try:
        # 3. ATUALIZAR texto e obrigação da pergunta no banco de dados
        cursor.execute(
            "UPDATE questions SET question_text = %s, is_required = %s WHERE id = %s",
            (new_text, is_required, question_id)
        )
       
        # 4. Atualizar opções, se aplicável
        if question_info['question_type'] in ['multiple_choice', 'checkbox'] and options_data_str:
            options = json.loads(options_data_str)
           
            # Remove todas as opções existentes
            cursor.execute("DELETE FROM question_options WHERE question_id = %s", (question_id,))
 
            # Insere as novas opções
            for opt in options:
                if opt.get('text', '').strip():
                    cursor.execute(
                        "INSERT INTO question_options (question_id, option_text) VALUES (%s, %s)",
                        (question_id, opt['text'])
                    )
       
        # 5. SALVAR AS MUDANÇAS NO BANCO (CRÍTICO)
        conn.commit()
        conn.close()
        return '<span class="saved-ok">Salvo!</span>', 200
    except Exception as e:
        print(f"Erro ao atualizar pergunta {question_id}: {e}")
        conn.rollback()
        conn.close()
        return 'Erro ao salvar: ' + str(e), 500
   
@app.route('/question/delete/<int:question_id>', methods=['DELETE'])
def delete_question(question_id):
    """Deleta uma pergunta (via HTMX)."""
    if 'user_id' not in session:
        return '', 401
 
    conn = get_db_connection()
    if not conn: return '', 500
    cursor = conn.cursor(dictionary=True)
 
    # 1. Verifica permissão
    cursor.execute("""
        SELECT f.user_id
        FROM questions q
        JOIN forms f ON q.form_id = f.id
        WHERE q.id = %s
    """, (question_id,))
    question_info = cursor.fetchone()
   
    if not question_info or question_info['user_id'] != session['user_id']:
        conn.close()
        return 'Não autorizado', 403
   
    try:
        # A remoção em cascata cuidará das respostas e opções
        cursor.execute("DELETE FROM questions WHERE id = %s", (question_id,))
        conn.commit()
        conn.close()
        return '', 200 # Resposta vazia, pois o HTMX remove o elemento
    except Exception as e:
        print(f"Erro ao deletar pergunta {question_id}: {e}")
        conn.close()
        return 'Erro ao deletar', 500
 
 
# --- Rotas de Submissão de Formulário (Público) ---
 
@app.route('/view/<int:form_id>')
def view_form(form_id):
    """Página pública para preencher o formulário. Usa a função de busca."""
    # Chama a função para buscar os dados ATUALIZADOS do banco
    form, questions = fetch_form_with_questions(form_id)
   
    if not form:
        flash('Formulário não encontrado.', 'danger')
        return redirect(url_for('home'))
       
    return render_template('view_form.html', form=form, questions=questions)
 
@app.route('/form/submit/<int:form_id>', methods=['POST'])
def submit_form(form_id):
    """Lógica para salvar as respostas."""
    form, questions = fetch_form_with_questions(form_id)
    if not form:
        flash('Formulário não encontrado.', 'danger')
        return redirect(url_for('home'))
 
    conn = get_db_connection()
    if not conn:
        flash('Erro de conexão com o banco de dados.', 'danger')
        return redirect(url_for('view_form', form_id=form_id))
       
    cursor = conn.cursor()
    user_id = session.get('user_id')
 
    try:
        # 1. Cria um registro de resposta (response)
        cursor.execute("INSERT INTO responses (form_id, user_id) VALUES (%s, %s)", (form_id, user_id))
        response_id = cursor.lastrowid
       
        # 2. Salva as respostas (answers)
        for q in questions:
           
            # Resposta para perguntas abertas
            if q['question_type'] == 'text':
                answer_text = request.form.get(f"q_{q['id']}_text")
                if answer_text:
                    cursor.execute(
                        "INSERT INTO answers (response_id, question_id, answer_text) VALUES (%s, %s, %s)",
                        (response_id, q['id'], answer_text)
                    )
 
            # Resposta para Múltipla Escolha
            elif q['question_type'] == 'multiple_choice':
                option_id = request.form.get(f"q_{q['id']}_choice")
                if option_id:
                     cursor.execute(
                        "INSERT INTO answers (response_id, question_id, option_id) VALUES (%s, %s, %s)",
                        (response_id, q['id'], option_id)
                    )
 
            # Resposta para Checkbox (pode haver múltiplas)
            elif q['question_type'] == 'checkbox':
                options_selected = request.form.getlist(f"q_{q['id']}_checkbox")
                for selected_id in options_selected:
                     cursor.execute(
                        "INSERT INTO answers (response_id, question_id, option_id) VALUES (%s, %s, %s)",
                        (response_id, q['id'], selected_id)
                    )
 
        conn.commit()
        flash('Sua resposta foi enviada com sucesso! Agradecemos sua participação.', 'success')
        return render_template('form_submitted.html', form=form) # Uma tela de agradecimento
    except Error as e:
        conn.rollback()
        flash(f'Ocorreu um erro ao enviar sua resposta: {e}', 'danger')
        return redirect(url_for('view_form', form_id=form_id))
    finally:
        conn.close()
 
# --- Rotas de Análise e Resultados ---
 
@app.route('/form/<int:form_id>/results')
def form_results(form_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
 
    # Verifica se o usuário é o dono do formulário
    form, questions = fetch_form_with_questions(form_id, session['user_id'])
    if not form:
        flash('Formulário não encontrado ou você não tem permissão.', 'danger')
        return redirect(url_for('dashboard'))
 
    conn = get_db_connection()
    if not conn:
        flash('Erro de conexão com o banco de dados.', 'danger')
        return redirect(url_for('dashboard'))
       
    cursor = conn.cursor(dictionary=True)
   
    # 1. Total de respostas
    cursor.execute("SELECT COUNT(id) AS total FROM responses WHERE form_id = %s", (form_id,))
    total_responses = cursor.fetchone()['total']
 
    # 2. Coletar dados de respostas para todas as perguntas
    results_data = []
    for q in questions:
        q_result = {'question_text': q['question_text'], 'type': q['question_type'], 'id': q['id']}
       
        if q['question_type'] == 'text':
            # Para perguntas abertas, lista as últimas 100 respostas
            cursor.execute("""
                SELECT answer_text FROM answers
                WHERE question_id = %s AND answer_text IS NOT NULL
                ORDER BY id DESC LIMIT 100
            """, (q['id'],))
            q_result['answers'] = cursor.fetchall()
           
        elif q['question_type'] in ['multiple_choice', 'checkbox']:
            # Para perguntas de escolha, faz a contagem de votos
            cursor.execute("""
                SELECT qo.option_text, COUNT(a.id) as vote_count
                FROM question_options qo
                LEFT JOIN answers a ON qo.id = a.option_id
                WHERE qo.question_id = %s
                GROUP BY qo.option_text
                ORDER BY vote_count DESC
            """, (q['id'],))
            q_result['stats'] = cursor.fetchall()
           
        results_data.append(q_result)
 
    conn.close()
   
    return render_template('form_results.html',
        form=form,
        total_responses=total_responses,
        results_data=results_data
    )
 
if __name__ == '__main__':
   app.run(debug=True)
 