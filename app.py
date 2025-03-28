from flask import Flask, jsonify, redirect, request
from flask_pydantic_spec import FlaskPydanticSpec
from datetime import date
from dateutil.relativedelta import relativedelta
from models import db_session, Livros, Emprestimos, Usuarios
from datetime import date
from dateutil.relativedelta import relativedelta
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, desc

app = Flask(__name__)
spec = FlaskPydanticSpec('Flask',
                         title='Flask API',
                         version='1.0.0')
spec.register(app)
app.secret_key = 'chave_secreta'

@app.route('/')
def index():
    return redirect('/consultar_livros')

@app.route('/consultar_livros')
def consultar_livros():
    try:
        lista_livros = select(Livros)
        lista_livros = db_session.execute(lista_livros).scalars()
        result = []
        for livro in lista_livros:
            result.append(livro.get_livro())
        db_session.close()


        result_disponiveis = []
        lista_livros_disponiveis = select(Livros)
        lista_livros_disponiveis = db_session.execute(lista_livros_disponiveis.filter(Livros.status)).scalars()
        for livros in lista_livros_disponiveis:
            result_disponiveis.append(livros.get_livro())
        db_session.close()



        return jsonify({'livros no catalogo da biblioteca': result},
                       {'livros disponiveis para emprestimos': result_disponiveis})
    except IntegrityError as e:
        return jsonify({'error': str(e)})

@app.route('/cadastrar_livro', methods=['POST'])
def cadastrar_livro():
    if request.method == 'POST':

        titulo = request.form.get('titulo')
        autor = request.form.get('autor')
        resumo = request.form.get('resumo')
        isbn = request.form.get('ISBN')
        isbn_existente = select(Livros)
        isbn_existente = db_session.execute(isbn_existente.filter_by(ISBN=isbn)).first()
        if isbn_existente:
            return jsonify({'isbn já existente': isbn_existente})
        if not titulo:
            return jsonify({"error": 'campo titulo vazio'}, 400)
        if not autor:
            return jsonify({"error": 'campo autor vazio'}, 400)
        if not resumo:
            return jsonify({"error": 'campo resumo vazio'}, 400)
        if not isbn:
            return jsonify({"error": 'campo ISBN vazio'}, 400)
        else:
            try:
                isbn = int(isbn)
                livro_salvado = Livros(titulo=titulo,
                                       autor=autor,
                                       resumo=resumo,
                                       ISBN=isbn,
                                       status=True)
                livro_salvado.save()
                if livro_salvado.status:
                    status_emprestimo = 'Está disponivel para emprestimo'
                else:
                    status_emprestimo = 'Livro não está disponivel para emprestimo'
                return jsonify({
                    'titulo': livro_salvado.titulo,
                    'autor': livro_salvado.autor,
                    'resumo': livro_salvado.resumo,
                    'status': status_emprestimo,
                    'ISBN': livro_salvado.ISBN
                })
            except IntegrityError as e:
                return jsonify({'error': str(e)})

@app.route('/cadastrar_usuario', methods=['POST'])
def cadastrar_usuario():
    if request.method == 'POST':
        nome = request.form.get('nome')
        cpf = request.form.get('cpf')
        endereco = request.form.get('endereco')

        cpf_ja_cadastrado = select(Usuarios)
        cpf_ja_cadastrado = db_session.execute(cpf_ja_cadastrado.filter_by(CPF=cpf)).first()
        if cpf_ja_cadastrado:
            return jsonify({"error": 'CPF ja cadastrado'})

        endereco_ja_cadastrado = select(Usuarios)
        endereco_ja_cadastrado = db_session.execute(endereco_ja_cadastrado.filter_by(endereco=endereco)).first()
        if endereco_ja_cadastrado:
            return jsonify({"error": 'endereco ja cadastrado'})
        if not nome:
            return jsonify({"error": 'campo nome vazio'}, 400)
        if not cpf:
            return jsonify({"error": 'campo cpf vazio'}, 400)
        if not endereco:
            return jsonify({"error": 'campo endereco vazio'}, 400)
        else:
            try:
                usuario_salvado = Usuarios(nome=nome,
                                           CPF=cpf,
                                           endereco=endereco)
                usuario_salvado.save()
                return jsonify({
                    'titulo': usuario_salvado.nome,
                    'autor': usuario_salvado.CPF,
                    'resumo': usuario_salvado.endereco})
            except IntegrityError as e:
                return jsonify({'error': str(e)})

@app.route('/cadastrar_emprestimo', methods=['POST'])
def cadastrar_emprestimo():
    if request.method == 'POST':

        data_emprestimo = date.today()
        data_de_devolucao = data_emprestimo + relativedelta(weeks=5)


        isbn = int(request.form.get('isbn'))
        id_usuario = int(request.form.get('id_usuario'))


        isbn_livro = select(Livros)
        db_livros = db_session.execute(isbn_livro).scalars()
        isbn_livro = db_session.execute(isbn_livro.filter_by(ISBN=isbn)).scalar()

        joinLivros_usuarios = (select(Emprestimos, Usuarios)
                               .join(Usuarios, Emprestimos.id_usuario == Usuarios.id))
        resultado_joinLivros_usuarios = db_session.execute(joinLivros_usuarios).fetchall()
        lista = []
        for nome_usuario in resultado_joinLivros_usuarios:
            lista.append({'nome': nome_usuario,'emprestimos': nome_usuario.emprestimo})


        if not isbn_livro:
            return jsonify({'Livro não encontrado': isbn_livro})

        # if not isbn_livro.status:
        #     return jsonify({'livro não está disponivel para emprestimo': isbn_livro})
        else:
            try:
                emprestimo_cadastrado = Emprestimos(data_emprestimo=data_emprestimo,
                                                    data_de_devolucao=data_de_devolucao,
                                                    ISBN_livro=isbn_livro,
                                                    id_usuario=id_usuario)
                emprestimo_cadastrado.save()
                return jsonify({
                    'data em que realizou o emprestimo': emprestimo_cadastrado.data_emprestimo,
                    'data de devolucao do livro': emprestimo_cadastrado.data_de_devolucao,
                    'ISBN do livro': emprestimo_cadastrado.ISBN_livro,
                    'usuario que realizou o emprestimo': emprestimo_cadastrado.id_usuario
                })
            except IntegrityError as e:
                return jsonify({'error': str(e)})


'''
Atendimento à biblioteca: A API deve fornecer funcionalidades para:
a. Cadastro de novos livros; ✅
b. Cadastro de novos usuários;✅
c. Realização de empréstimos;✅
d. Consulta de livros disponíveis e emprestados;✅
e. Consulta de histórico de empréstimos por usuário;❌
f. Atualização de informações de livros e usuários;❌
g. Exclusão de livros e usuários (com regras de negócio adequadas).❌
'''
if __name__ == '__main__':
    app.run(debug=True)