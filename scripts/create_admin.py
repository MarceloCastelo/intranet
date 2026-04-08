"""
Script de uso único para criar o primeiro usuário admin.
Execute com: docker exec -e PYTHONPATH=/app portal_app python scripts/create_admin.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.user import Department, User

app = create_app()

with app.app_context():
    # Departamento padrão
    dep = Department.query.filter_by(name='TI').first()
    if not dep:
        dep = Department(name='TI')
        db.session.add(dep)
        db.session.flush()

    # Usuário admin
    if User.query.filter_by(email='admin@adtsa.com.br').first():
        print('Usuário admin já existe.')
    else:
        u = User(
            name='Administrador',
            email='admin@adtsa.com.br',
            role='admin',
            status='active',
            department_id=dep.id,
            first_login=False,
            two_factor_mandatory=False,
            two_factor_enabled=False,
        )
        u.set_password('Admin@1234')
        db.session.add(u)
        db.session.commit()
        print(f'Admin criado: {u.email}  /  senha: Admin@1234')
