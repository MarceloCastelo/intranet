"""
Script para importar usuários a partir do arquivo CSV.
Usuários são criados com role='user', is_admin=False e first_login=True.
A senha inicial é o próprio CPF (sem formatação).
O admin deverá ajustar roles/permissões manualmente após a importação.

Execute com:
    docker exec -e PYTHONPATH=/app portal_app python scripts/importar_usuarios.py
Ou localmente (com venv ativo):
    python scripts/importar_usuarios.py
"""
import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.user import User

CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'database', 'users', 'pedragon_users.csv',
)

# Domínio fictício para e-mails temporários gerados automaticamente
EMAIL_DOMAIN = 'pedragon.local'


def limpar_cpf(valor: str) -> str:
    """Remove tudo que não for dígito e retorna os 11 primeiros caracteres."""
    return re.sub(r'\D', '', valor)[:11]


def gerar_email(cpf: str) -> str:
    return f'{cpf}@{EMAIL_DOMAIN}'


def importar():
    app = create_app()

    with app.app_context():
        criados = 0
        ignorados = 0
        erros = 0

        with open(CSV_PATH, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for linha, row in enumerate(reader, start=2):  # linha 1 = cabeçalho
                nome = row.get('Nome', '').strip()
                cpf_raw = row.get('CPF', '').strip()

                if not nome or not cpf_raw:
                    print(f'[LINHA {linha}] Dados incompletos, pulando: {row}')
                    ignorados += 1
                    continue

                cpf = limpar_cpf(cpf_raw)

                if len(cpf) != 11:
                    print(f'[LINHA {linha}] CPF inválido "{cpf_raw}", pulando.')
                    erros += 1
                    continue

                # Verifica duplicata por CPF
                if User.query.filter_by(cpf=cpf).first():
                    print(f'[LINHA {linha}] CPF {cpf} já existe, pulando.')
                    ignorados += 1
                    continue

                email = gerar_email(cpf)

                # Verifica duplicata por e-mail (improvável, mas seguro)
                if User.query.filter_by(email=email).first():
                    print(f'[LINHA {linha}] E-mail {email} já existe, pulando.')
                    ignorados += 1
                    continue

                usuario = User(
                    name=nome,
                    cpf=cpf,
                    email=email,
                    role='user',
                    is_admin=False,
                    status='active',
                    first_login=True,
                )
                # Senha inicial = CPF sem formatação
                usuario.set_password(cpf)

                db.session.add(usuario)

                try:
                    db.session.flush()  # valida constraints antes do commit final
                    criados += 1
                    print(f'[OK] {nome} ({cpf})')
                except Exception as exc:
                    db.session.rollback()
                    print(f'[ERRO] {nome} ({cpf}): {exc}')
                    erros += 1

            db.session.commit()

        print()
        print('=' * 50)
        print(f'Importação concluída.')
        print(f'  Criados : {criados}')
        print(f'  Ignorados: {ignorados}')
        print(f'  Erros    : {erros}')
        print('=' * 50)
        print()
        print('ATENÇÃO: a senha inicial de cada usuário é o próprio CPF (sem formatação).')
        print('O admin deve ajustar roles/permissões e solicitar troca de senha.')


if __name__ == '__main__':
    importar()
