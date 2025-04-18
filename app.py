from flask import Flask, render_template, request, redirect, session
import json
import os

app = Flask(__name__)

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///estoque.db'
app.secret_key = 'minha_chave_secreta'

estoque = {}

def carregar_usuarios():
    # Tenta abrir o arquivo JSON de usuários, caso contrário, retorna um dicionário vazio
    try:
        with open('usuarios.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def salvar_usuarios(usuarios):
    # Salva os usuários no arquivo JSON
    with open('usuarios.json', 'w') as f:
        json.dump(usuarios, f, indent=4)

# Função para verificar se algum produto está com estoque baixo
def verificar_estoque_baixo():
    estoque_baixo = []
    for codigo, produto in estoque.items():
        if produto['quantidade'] <= 10:  # Definindo que o estoque baixo é quando o produto tem 10 ou menos unidades
            estoque_baixo.append(produto)
    return estoque_baixo

@app.route('/login', methods=['GET', 'POST'])
def login():
    usuarios = carregar_usuarios()
    if request.method == 'POST':
        user = request.form['usuario']
        senha = request.form['senha']
        if user in usuarios and usuarios[user]["senha"] == senha:
            session['usuario'] = user
            session['tipo'] = usuarios[user]["tipo"]
            return redirect('/')
        else:
            return "Usuário ou senha inválidos"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/')
def home():
    if 'usuario' not in session:
        return redirect('/login')

    # Chama a função para verificar estoque baixo
    produtos_baixo = verificar_estoque_baixo()

    return render_template('index.html', estoque=estoque, usuario=session['usuario'], tipo=session['tipo'], produtos_baixo=produtos_baixo)

@app.route('/adicionar', methods=['POST'])
def adicionar():
    if session.get('tipo') != 'admin':
        return "Acesso negado"
    codigo = request.form['codigo']
    nome = request.form['nome']
    quantidade = int(request.form['quantidade'])
    valor = float(request.form['valor'])
    estoque[codigo] = {
        "nome": nome,
        "quantidade": quantidade,
        "valor": valor,
        "vendido": 0,
        "vendas_por_funcionario": {}
    }
    return redirect('/')

@app.route('/remover/<codigo>')
def remover(codigo):
    if session.get('tipo') != 'admin':
        return "Acesso negado"
    if codigo in estoque:
        del estoque[codigo]
    return redirect('/')

@app.route('/vender/<codigo>', methods=['POST'])
def vender(codigo):
    if 'usuario' not in session:
        return redirect('/login')
    
    usuario = session['usuario']
    if codigo in estoque:
        quantidade_venda = int(request.form['quantidade'])
        if estoque[codigo]["quantidade"] >= quantidade_venda:
            estoque[codigo]["quantidade"] -= quantidade_venda

            # Atualiza total vendido
            estoque[codigo]["vendido"] += quantidade_venda

            # Atualiza vendas por funcionário
            if usuario not in estoque[codigo]["vendas_por_funcionario"]:
                estoque[codigo]["vendas_por_funcionario"][usuario] = 0
            estoque[codigo]["vendas_por_funcionario"][usuario] += quantidade_venda
    return redirect('/')

@app.route('/imprimir')
def imprimir():
    if 'usuario' not in session:
        return redirect('/login')
    return render_template('imprimir.html', estoque=estoque)

@app.route('/usuarios', methods=['GET', 'POST'])
def gerenciar_usuarios():
    if session.get('tipo') != 'admin':
        return "Acesso negado"
    usuarios = carregar_usuarios()
    if request.method == 'POST':
        nome = request.form['nome']
        nova_funcao = request.form['tipo']
        if nome in usuarios:
            usuarios[nome]["tipo"] = nova_funcao
            salvar_usuarios(usuarios)
    return render_template('usuarios.html', usuarios=usuarios)

if __name__ == '__main__':
    app.run(debug=True)
