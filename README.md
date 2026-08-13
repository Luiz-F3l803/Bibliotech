# Sistema de Biblioteca Escolar

Projeto de Desenvolvimento de Sistemas — back-end em Python (Flask) + banco de dados SQLite, rodando em `localhost`.

## O que o sistema faz

- Cadastro de alunos, professores e funcionários da biblioteca
- Cadastro e controle de disponibilidade dos livros do acervo
- Criação, devolução e exclusão de fichas de empréstimo
- Monitoramento automático de atrasos (atualizado a cada acesso à Home e aos Relatórios)
- Aviso visual de empréstimos atrasados na tela inicial
- Busca de livros por título, autor ou categoria
- Histórico de empréstimos por aluno/professor
- Relatórios de empréstimos, devoluções e livros mais utilizados
- Login de funcionários com senha criptografada (hash), protegendo o acesso ao sistema

## Como rodar no seu computador (ou nos computadores da escola)

### 1. Pré-requisitos
- Python 3.9 ou superior instalado ([python.org](https://www.python.org/downloads/))

### 2. Instalar as dependências

Abra um terminal dentro da pasta do projeto e rode:

```bash
pip install -r requirements.txt
```

Se o computador tiver Python 2 e 3 instalados, pode ser necessário usar `pip3` e `python3` em vez de `pip` e `python`.

### 3. Executar o sistema

```bash
python app.py
```

Você verá uma mensagem no terminal parecida com:

```
Usuário padrão criado -> usuário: admin | senha: admin123
 * Running on http://127.0.0.1:5000
```

### 4. Acessar pelo navegador

Abra o navegador (Chrome, Firefox, Edge...) e acesse:

```
http://localhost:5000
```

Faça login com:
- **Usuário:** admin
- **Senha:** admin123

> ⚠️ Recomenda-se cadastrar um novo funcionário com senha própria e, se possível, remover/alterar o usuário `admin` padrão depois do primeiro uso.

## Como usar

1. **Login** — tela inicial, acesso restrito aos funcionários.
2. **Início (Home)** — mostra os empréstimos ativos, avisos de atraso, e os botões para:
   - Criar uma nova ficha de empréstimo
   - Ir para os cadastros (alunos, professores, funcionários, livros)
   - Devolver ou excluir uma ficha diretamente na lista
3. **Nova ficha de empréstimo** — escolha se é aluno ou professor, selecione a pessoa, o livro e a data de devolução.
4. **Cadastros** — abas para cadastrar e listar alunos, professores, funcionários e livros (com exclusão).
5. **Buscar livros** — pesquisa rápida por título, autor ou categoria, mostrando a disponibilidade.
6. **Relatórios** — total de empréstimos, devoluções, atrasos e os livros mais emprestados.

## Sobre o banco de dados

O sistema usa **SQLite**, um banco de dados leve que não precisa de instalação separada — ele é criado automaticamente como o arquivo `biblioteca.db` na primeira execução, dentro da própria pasta do projeto. Isso facilita a instalação nos computadores da escola, sem depender de servidores externos.

## Estrutura do projeto

```
biblioteca/
├── app.py                 # back-end Flask (rotas, modelos, lógica)
├── requirements.txt        # dependências do projeto
├── biblioteca.db           # banco de dados (criado automaticamente)
├── templates/               # telas HTML (login, home, cadastro, etc.)
│   ├── base.html
│   ├── login.html
│   ├── home.html
│   ├── criar_ficha.html
│   ├── cadastro.html
│   ├── buscar.html
│   ├── historico.html
│   └── relatorios.html
└── static/
    └── style.css            # estilo visual do sistema
```

## Observações para a apresentação/entrega

- A senha dos funcionários é armazenada com **hash** (não em texto puro), atendendo ao requisito de segurança no armazenamento das informações.
- O controle de disponibilidade dos livros é automático: ao criar uma ficha, a quantidade disponível diminui; ao devolver ou excluir a ficha, ela volta a aumentar.
- O status de cada ficha muda automaticamente para "Atrasado" quando a data prevista de devolução passa, sem precisar de nenhuma ação manual.
- Por rodar em `localhost` com SQLite, o sistema funciona sem internet, adequado para os computadores da escola.
