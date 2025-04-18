import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, redirect, session
import json
import os

app = Flask(__name__)

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///estoque.db'
app.secret_key = 'minha_chave_secreta'

estoque = {}

def carregar_usuarios():
    try:
        with open('usuarios.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def salvar_usuarios(usuarios):
    with open('usuarios.json', 'w') as f:
        json.dump(usuarios, f, indent=4)

def verificar_estoque_baixo():
    estoque_baixo = []
    for codigo, produto in estoque.items():
        if produto['quantidade'] <= 5:  # Definindo estoque baixo como <= 5 unidades
            estoque_baixo.append(produto)
    return estoque_baixo

def enviar_email_estoque_baixo(produtos_baixo):
    sender_email = "luisgustavobqcustodio07@gmail.com"
    receiver_email = "luisgustavobqcustodio@gmail.com"
    password = "owec clvo uiyv vgar"  # Use a senha de app ou a senha normal se apps menos seguros estiverem habilitados

    subject = "Alerta: Estoque baixo"
    body = "Atenção, os seguintes produtos estão com estoque baixo:\n"
    for produto in produtos_baixo:
        body += f"- {produto['nome']} ({produto['quantidade']} unidades restantes)\n"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.close()
        print("E-mail enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {str(e)}")

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

@app.route('/', methods=['GET', 'POST'])
def home():
    if 'usuario' not in session:
        return redirect('/login')

    # Pesquisa de produto
    pesquisa = request.args.get('pesquisa', '')
    produtos_filtrados = {codigo: produto for codigo, produto in estoque.items() if pesquisa.lower() in produto['nome'].lower() or pesquisa.lower() in codigo.lower()}

    # Chama a função para verificar estoque baixo
    produtos_baixo = verificar_estoque_baixo()
    if produtos_baixo:
        enviar_email_estoque_baixo(produtos_baixo)

    return render_template('index.html', estoque=produtos_filtrados, usuario=session['usuario'], tipo=session['tipo'], produtos_baixo=produtos_baixo, pesquisa=pesquisa)

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
            estoque[codigo]["vendido"] += quantidade_venda

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
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
