# -*- coding: utf-8 -*-
"""
Sistema de Biblioteca Escolar
Trabalho de Desenvolvimento de Sistemas
Back-end: Python + Flask + SQLite (via SQLAlchemy)
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
from functools import wraps
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'troque-esta-chave-antes-de-usar-em-producao'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'biblioteca.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =========================================================
#  MODELOS (TABELAS DO BANCO DE DADOS)
# =========================================================

class Funcionario(db.Model):
    __tablename__ = 'funcionario'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    cargo = db.Column(db.String(80), nullable=False, default='Bibliotecário(a)')
    usuario = db.Column(db.String(60), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def checar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)


class Aluno(db.Model):
    __tablename__ = 'aluno'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    matricula = db.Column(db.String(40), unique=True, nullable=False)
    turma = db.Column(db.String(40))

    def __repr__(self):
        return self.nome


class Turma(db.Model):
    __tablename__ = 'turma'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(40), unique=True, nullable=False)
    turno = db.Column(db.String(20))

    def __repr__(self):
        return self.nome


class Professor(db.Model):
    __tablename__ = 'professor'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    disciplina = db.Column(db.String(80))

    def __repr__(self):
        return self.nome


CATEGORIAS_LIVRO = [
    'Romance', 'Fantasia', 'Ficção científica', 'Suspense',
    'Terror', 'Biografia', 'Autoajuda'
]


class Fileira(db.Model):
    __tablename__ = 'fileira'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(40), unique=True, nullable=False)
    descricao = db.Column(db.String(160))

    def __repr__(self):
        return self.codigo


class Livro(db.Model):
    __tablename__ = 'livro'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(160), nullable=False)
    autor = db.Column(db.String(120))
    categoria = db.Column(db.String(80))
    prateleira = db.Column(db.String(40))
    quantidade_total = db.Column(db.Integer, nullable=False, default=1)
    quantidade_disponivel = db.Column(db.Integer, nullable=False, default=1)


class Emprestimo(db.Model):
    __tablename__ = 'emprestimo'
    id = db.Column(db.Integer, primary_key=True)
    pessoa_tipo = db.Column(db.String(20), nullable=False)   # 'Aluno' ou 'Professor'
    pessoa_nome = db.Column(db.String(120), nullable=False)  # nome guardado na ficha
    pessoa_ref = db.Column(db.String(60))                    # matrícula ou identificação

    livro_id = db.Column(db.Integer, db.ForeignKey('livro.id'), nullable=False)
    livro = db.relationship('Livro', backref='emprestimos')

    data_emprestimo = db.Column(db.Date, nullable=False, default=date.today)
    data_devolucao_prevista = db.Column(db.Date, nullable=False)
    data_devolucao_real = db.Column(db.Date, nullable=True)

    status = db.Column(db.String(20), nullable=False, default='Ativo')  # Ativo / Devolvido / Atrasado

    funcionario_id = db.Column(db.Integer, db.ForeignKey('funcionario.id'))


# =========================================================
#  AUTENTICAÇÃO / DECORATOR
# =========================================================

def login_obrigatorio(f):
    @wraps(f)
    def decorada(*args, **kwargs):
        if 'funcionario_id' not in session:
            flash('Faça login para acessar o sistema.', 'aviso')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorada


@app.context_processor
def injetar_usuario():
    nome = session.get('funcionario_nome')
    return dict(usuario_logado=nome)


# =========================================================
#  FUNÇÕES AUXILIARES
# =========================================================

def atualizar_atrasos():
    """Monitoramento automático: marca como 'Atrasado' fichas cuja data prevista já passou."""
    hoje = date.today()
    ativos_vencidos = Emprestimo.query.filter(
        Emprestimo.status == 'Ativo',
        Emprestimo.data_devolucao_prevista < hoje
    ).all()
    for emp in ativos_vencidos:
        emp.status = 'Atrasado'
    if ativos_vencidos:
        db.session.commit()
    return ativos_vencidos


# =========================================================
#  ROTAS - LOGIN / LOGOUT
# =========================================================

@app.route('/')
def index():
    if 'funcionario_id' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario', '').strip()
        senha = request.form.get('senha', '')
        func = Funcionario.query.filter_by(usuario=usuario).first()
        if func and func.checar_senha(senha):
            session['funcionario_id'] = func.id
            session['funcionario_nome'] = func.nome
            flash(f'Bem-vindo(a), {func.nome}!', 'sucesso')
            return redirect(url_for('home'))
        flash('Usuário ou senha inválidos.', 'erro')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu do sistema.', 'aviso')
    return redirect(url_for('login'))


# =========================================================
#  ROTA - HOME
# =========================================================

@app.route('/home')
@login_obrigatorio
def home():
    atrasados_agora = atualizar_atrasos()

    fichas = Emprestimo.query.filter(
        Emprestimo.status.in_(['Ativo', 'Atrasado'])
    ).order_by(Emprestimo.data_devolucao_prevista.asc()).all()

    total_livros = db.session.query(db.func.sum(Livro.quantidade_total)).scalar() or 0
    total_disponiveis = db.session.query(db.func.sum(Livro.quantidade_disponivel)).scalar() or 0
    total_emprestimos_ativos = Emprestimo.query.filter_by(status='Ativo').count()
    total_atrasados = Emprestimo.query.filter_by(status='Atrasado').count()

    return render_template(
        'home.html',
        fichas=fichas,
        total_livros=total_livros,
        total_disponiveis=total_disponiveis,
        total_emprestimos_ativos=total_emprestimos_ativos,
        total_atrasados=total_atrasados,
        hoje=date.today(),
        houve_novo_atraso=len(atrasados_agora) > 0
    )


# =========================================================
#  ROTAS - FICHAS DE EMPRÉSTIMO
# =========================================================

@app.route('/ficha/nova', methods=['GET', 'POST'])
@login_obrigatorio
def nova_ficha():
    if request.method == 'POST':
        pessoa_tipo = request.form.get('pessoa_tipo')
        pessoa_id = request.form.get('pessoa_id')
        livro_id = request.form.get('livro_id')
        dias_prazo = request.form.get('data_devolucao')  # data no formato yyyy-mm-dd

        if not (pessoa_tipo and pessoa_id and livro_id and dias_prazo):
            flash('Preencha todos os campos da ficha.', 'erro')
            return redirect(url_for('nova_ficha'))

        livro = Livro.query.get(livro_id)
        if not livro or livro.quantidade_disponivel < 1:
            flash('Este livro não está disponível no momento.', 'erro')
            return redirect(url_for('nova_ficha'))

        if pessoa_tipo == 'Aluno':
            pessoa = Aluno.query.get(pessoa_id)
            pessoa_ref = pessoa.matricula if pessoa else ''
        else:
            pessoa = Professor.query.get(pessoa_id)
            pessoa_ref = pessoa.disciplina if pessoa else ''

        if not pessoa:
            flash('Pessoa não encontrada.', 'erro')
            return redirect(url_for('nova_ficha'))

        try:
            data_prevista = datetime.strptime(dias_prazo, '%Y-%m-%d').date()
        except ValueError:
            flash('Data de devolução inválida.', 'erro')
            return redirect(url_for('nova_ficha'))

        ficha = Emprestimo(
            pessoa_tipo=pessoa_tipo,
            pessoa_nome=pessoa.nome,
            pessoa_ref=pessoa_ref,
            livro_id=livro.id,
            data_emprestimo=date.today(),
            data_devolucao_prevista=data_prevista,
            status='Ativo',
            funcionario_id=session.get('funcionario_id')
        )
        livro.quantidade_disponivel -= 1
        db.session.add(ficha)
        db.session.commit()
        flash('Ficha de empréstimo criada com sucesso!', 'sucesso')
        return redirect(url_for('home'))

    alunos = Aluno.query.order_by(Aluno.nome).all()
    professores = Professor.query.order_by(Professor.nome).all()
    livros = Livro.query.filter(Livro.quantidade_disponivel > 0).order_by(Livro.titulo).all()
    prazo_sugerido = date.today() + timedelta(days=14)

    return render_template(
        'criar_ficha.html',
        alunos=alunos,
        professores=professores,
        livros=livros,
        prazo_sugerido=prazo_sugerido.isoformat(),
        hoje=date.today().isoformat()
    )


@app.route('/ficha/<int:ficha_id>/devolver', methods=['POST'])
@login_obrigatorio
def devolver_ficha(ficha_id):
    ficha = Emprestimo.query.get_or_404(ficha_id)
    ficha.status = 'Devolvido'
    ficha.data_devolucao_real = date.today()
    ficha.livro.quantidade_disponivel += 1
    db.session.commit()
    flash(f'Devolução de "{ficha.livro.titulo}" registrada.', 'sucesso')
    return redirect(url_for('home'))


@app.route('/ficha/<int:ficha_id>/deletar', methods=['POST'])
@login_obrigatorio
def deletar_ficha(ficha_id):
    ficha = Emprestimo.query.get_or_404(ficha_id)
    # Se a ficha ainda estava ativa/atrasada, devolve o exemplar ao acervo
    if ficha.status in ('Ativo', 'Atrasado'):
        ficha.livro.quantidade_disponivel += 1
    db.session.delete(ficha)
    db.session.commit()
    flash('Ficha de empréstimo excluída.', 'aviso')
    return redirect(url_for('home'))


# =========================================================
#  ROTAS - CADASTROS (ALUNOS, PROFESSORES, FUNCIONÁRIOS, LIVROS)
# =========================================================

@app.route('/cadastro')
@login_obrigatorio
def cadastro():
    aba = request.args.get('aba', 'aluno')
    alunos = Aluno.query.order_by(Aluno.nome).all()
    professores = Professor.query.order_by(Professor.nome).all()
    funcionarios = Funcionario.query.order_by(Funcionario.nome).all()
    livros = Livro.query.order_by(Livro.titulo).all()
    turmas = Turma.query.order_by(Turma.nome).all()
    fileiras = Fileira.query.order_by(Fileira.codigo).all()
    return render_template(
        'cadastro.html',
        aba=aba,
        alunos=alunos,
        professores=professores,
        funcionarios=funcionarios,
        livros=livros,
        categorias=CATEGORIAS_LIVRO,
        turmas=turmas,
        fileiras=fileiras
    )


@app.route('/cadastro/aluno', methods=['POST'])
@login_obrigatorio
def cadastrar_aluno():
    nome = request.form.get('nome', '').strip()
    matricula = request.form.get('matricula', '').strip()
    turma = request.form.get('turma', '').strip()
    if not nome or not matricula:
        flash('Nome e matrícula são obrigatórios.', 'erro')
    elif Aluno.query.filter_by(matricula=matricula).first():
        flash('Já existe um aluno com essa matrícula.', 'erro')
    else:
        db.session.add(Aluno(nome=nome, matricula=matricula, turma=turma))
        db.session.commit()
        flash('Aluno cadastrado com sucesso!', 'sucesso')
    return redirect(url_for('cadastro', aba='aluno'))


@app.route('/cadastro/turma', methods=['POST'])
@login_obrigatorio
def cadastrar_turma():
    nome = request.form.get('nome', '').strip()
    turno = request.form.get('turno', '').strip()
    if not nome:
        flash('Informe o nome da turma.', 'erro')
    elif Turma.query.filter_by(nome=nome).first():
        flash('Já existe uma turma com esse nome.', 'erro')
    else:
        db.session.add(Turma(nome=nome, turno=turno))
        db.session.commit()
        flash('Turma cadastrada com sucesso!', 'sucesso')
    return redirect(url_for('cadastro', aba='turma'))


@app.route('/cadastro/professor', methods=['POST'])
@login_obrigatorio
def cadastrar_professor():
    nome = request.form.get('nome', '').strip()
    disciplina = request.form.get('disciplina', '').strip()
    if not nome:
        flash('Informe o nome do professor.', 'erro')
    else:
        db.session.add(Professor(nome=nome, disciplina=disciplina))
        db.session.commit()
        flash('Professor cadastrado com sucesso!', 'sucesso')
    return redirect(url_for('cadastro', aba='professor'))


@app.route('/cadastro/funcionario', methods=['POST'])
@login_obrigatorio
def cadastrar_funcionario():
    nome = request.form.get('nome', '').strip()
    cargo = request.form.get('cargo', '').strip() or 'Bibliotecário(a)'
    usuario = request.form.get('usuario', '').strip()
    senha = request.form.get('senha', '')
    if not (nome and usuario and senha):
        flash('Preencha nome, usuário e senha.', 'erro')
    elif Funcionario.query.filter_by(usuario=usuario).first():
        flash('Esse nome de usuário já está em uso.', 'erro')
    else:
        novo = Funcionario(nome=nome, cargo=cargo, usuario=usuario)
        novo.set_senha(senha)
        db.session.add(novo)
        db.session.commit()
        flash('Funcionário cadastrado com sucesso!', 'sucesso')
    return redirect(url_for('cadastro', aba='funcionario'))


@app.route('/cadastro/fileira', methods=['POST'])
@login_obrigatorio
def cadastrar_fileira():
    codigo = request.form.get('codigo', '').strip()
    descricao = request.form.get('descricao', '').strip()
    if not codigo:
        flash('Informe o código da fileira.', 'erro')
    elif Fileira.query.filter_by(codigo=codigo).first():
        flash('Já existe uma fileira com esse código.', 'erro')
    else:
        db.session.add(Fileira(codigo=codigo, descricao=descricao))
        db.session.commit()
        flash('Fileira cadastrada com sucesso!', 'sucesso')
    return redirect(url_for('cadastro', aba='fileira'))


@app.route('/cadastro/livro', methods=['POST'])
@login_obrigatorio
def cadastrar_livro():
    titulo = request.form.get('titulo', '').strip()
    autor = request.form.get('autor', '').strip()
    categoria = request.form.get('categoria', '').strip()
    prateleira = request.form.get('prateleira', '').strip()
    try:
        quantidade = int(request.form.get('quantidade', 1))
    except ValueError:
        quantidade = 1

    if not titulo or quantidade < 1:
        flash('Informe ao menos o título e uma quantidade válida.', 'erro')
    elif categoria and categoria not in CATEGORIAS_LIVRO:
        flash('Categoria inválida.', 'erro')
    else:
        db.session.add(Livro(
            titulo=titulo, autor=autor, categoria=categoria, prateleira=prateleira,
            quantidade_total=quantidade, quantidade_disponivel=quantidade
        ))
        db.session.commit()
        flash('Livro cadastrado com sucesso!', 'sucesso')
    return redirect(url_for('cadastro', aba='livro'))


@app.route('/cadastro/<tipo>/<int:item_id>/deletar', methods=['POST'])
@login_obrigatorio
def deletar_cadastro(tipo, item_id):
    modelos = {
        'aluno': Aluno, 'professor': Professor, 'funcionario': Funcionario,
        'livro': Livro, 'turma': Turma, 'fileira': Fileira
    }
    modelo = modelos.get(tipo)
    if not modelo:
        flash('Tipo de cadastro inválido.', 'erro')
        return redirect(url_for('cadastro'))

    item = modelo.query.get_or_404(item_id)

    if tipo == 'livro' and Emprestimo.query.filter_by(livro_id=item_id, status='Ativo').first():
        flash('Não é possível excluir: há empréstimos ativos deste livro.', 'erro')
        return redirect(url_for('cadastro', aba='livro'))

    if tipo == 'funcionario' and item.id == session.get('funcionario_id'):
        flash('Você não pode excluir o próprio usuário logado.', 'erro')
        return redirect(url_for('cadastro', aba='funcionario'))

    if tipo == 'turma' and Aluno.query.filter_by(turma=item.nome).first():
        flash('Não é possível excluir: há alunos cadastrados nessa turma.', 'erro')
        return redirect(url_for('cadastro', aba='turma'))

    if tipo == 'fileira' and Livro.query.filter_by(prateleira=item.codigo).first():
        flash('Não é possível excluir: há livros cadastrados nessa fileira.', 'erro')
        return redirect(url_for('cadastro', aba='fileira'))

    db.session.delete(item)
    db.session.commit()
    flash('Cadastro removido com sucesso.', 'aviso')
    return redirect(url_for('cadastro', aba=tipo))


# =========================================================
#  ROTAS - BUSCA E HISTÓRICO
# =========================================================

@app.route('/buscar')
@login_obrigatorio
def buscar_livros():
    termo = request.args.get('q', '').strip()
    resultados = []
    if termo:
        like = f'%{termo}%'
        resultados = Livro.query.filter(
            (Livro.titulo.ilike(like)) |
            (Livro.autor.ilike(like)) |
            (Livro.categoria.ilike(like)) |
            (Livro.prateleira.ilike(like))
        ).order_by(Livro.titulo).all()
    return render_template('buscar.html', termo=termo, resultados=resultados)


@app.route('/historico/<pessoa_nome>')
@login_obrigatorio
def historico(pessoa_nome):
    fichas = Emprestimo.query.filter_by(pessoa_nome=pessoa_nome).order_by(
        Emprestimo.data_emprestimo.desc()
    ).all()
    return render_template('historico.html', pessoa_nome=pessoa_nome, fichas=fichas)


# =========================================================
#  ROTA - RELATÓRIOS
# =========================================================

@app.route('/relatorios')
@login_obrigatorio
def relatorios():
    atualizar_atrasos()

    total_emprestimos = Emprestimo.query.count()
    total_devolucoes = Emprestimo.query.filter_by(status='Devolvido').count()
    total_atrasados = Emprestimo.query.filter_by(status='Atrasado').count()
    total_ativos = Emprestimo.query.filter_by(status='Ativo').count()

    mais_usados = db.session.query(
        Livro.titulo, db.func.count(Emprestimo.id).label('qtd')
    ).join(Emprestimo, Emprestimo.livro_id == Livro.id) \
     .group_by(Livro.id).order_by(db.desc('qtd')).limit(10).all()

    ultimas_fichas = Emprestimo.query.order_by(Emprestimo.data_emprestimo.desc()).limit(15).all()

    return render_template(
        'relatorios.html',
        total_emprestimos=total_emprestimos,
        total_devolucoes=total_devolucoes,
        total_atrasados=total_atrasados,
        total_ativos=total_ativos,
        mais_usados=mais_usados,
        ultimas_fichas=ultimas_fichas
    )


# =========================================================
#  INICIALIZAÇÃO DO BANCO DE DADOS
# =========================================================

def inicializar_banco():
    with app.app_context():
        db.create_all()
        if Funcionario.query.count() == 0:
            admin = Funcionario(nome='Administrador(a)', cargo='Bibliotecário(a) Chefe', usuario='admin')
            admin.set_senha('admin123')
            db.session.add(admin)
            db.session.commit()
            print('=' * 60)
            print('Usuário padrão criado -> usuário: admin | senha: admin123')
            print('IMPORTANTE: troque essa senha após o primeiro acesso.')
            print('=' * 60)


if __name__ == '__main__':
    inicializar_banco()
    app.run(debug=True, host='0.0.0.0', port=5000)
