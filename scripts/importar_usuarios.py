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


BATCH_SIZE = 100  # registros por commit


def importar():
    app = create_app()

    with app.app_context():
        criados = 0
        ignorados = 0
        erros = 0

        # Carrega CPFs e e-mails existentes de uma só vez — evita N queries
        cpfs_existentes = {r[0] for r in db.session.execute(
            db.text('SELECT cpf FROM users WHERE cpf IS NOT NULL')
        )}
        emails_existentes = {r[0] for r in db.session.execute(
            db.text('SELECT email FROM users WHERE email IS NOT NULL')
        )}

        lote: list = []

        def _commit_lote():
            nonlocal criados, erros
            try:
                db.session.bulk_save_objects(lote)
                db.session.commit()
                criados += len(lote)
            except Exception as exc:
                db.session.rollback()
                print(f'[ERRO LOTE] {exc}')
                erros += len(lote)
            finally:
                lote.clear()
                db.session.expire_all()

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

                if cpf in cpfs_existentes:
                    print(f'[LINHA {linha}] CPF {cpf} já existe, pulando.')
                    ignorados += 1
                    continue

                email = gerar_email(cpf)

                if email in emails_existentes:
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
                usuario.set_password(cpf)

                lote.append(usuario)
                cpfs_existentes.add(cpf)
                emails_existentes.add(email)
                print(f'[OK] {nome} ({cpf})')

                if len(lote) >= BATCH_SIZE:
                    _commit_lote()

        if lote:
            _commit_lote()

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
