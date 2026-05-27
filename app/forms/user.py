from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (BooleanField, DateField, PasswordField, SelectField,
                     StringField, SubmitField)
from wtforms.validators import (DataRequired, Email, EqualTo, Length,
                                Optional, ValidationError)
import re

from app.models.user import UnitState, User

CORPORATE_DOMAIN = 'pedragon.com.br'


def _validate_corporate_email(field):
    """Garante que o e-mail pertence ao domínio corporativo."""
    email = (field.data or '').strip().lower()
    if not email.endswith(f'@{CORPORATE_DOMAIN}'):
        raise ValidationError(f'Apenas e-mails @{CORPORATE_DOMAIN} são permitidos.')


def _validate_cpf(form, field):
    """Valida formato e dígitos verificadores do CPF."""
    raw = re.sub(r'\D', '', field.data or '')
    if len(raw) != 11 or len(set(raw)) == 1:
        raise ValidationError('CPF inválido.')
    total = sum(int(raw[i]) * (10 - i) for i in range(9))
    d1 = 0 if (total * 10 % 11) >= 10 else (total * 10 % 11)
    total = sum(int(raw[i]) * (11 - i) for i in range(10))
    d2 = 0 if (total * 10 % 11) >= 10 else (total * 10 % 11)
    if int(raw[9]) != d1 or int(raw[10]) != d2:
        raise ValidationError('CPF inválido.')
    field.data = raw  # normaliza para só dígitos


class UserForm(FlaskForm):
    """Formulário compartilhado entre criar e editar usuário."""

    name          = StringField('Nome completo',
                                validators=[DataRequired(), Length(max=150)])
    cpf           = StringField('CPF',
                                validators=[DataRequired(), _validate_cpf])
    email         = StringField('E-mail corporativo',
                                validators=[DataRequired(), Email(), Length(max=150)])
    role          = SelectField('Perfil / área',
                                choices=[('user', 'Usuário'), ('editor', 'Editor'),
                                         ('rh', 'Diretoria'), ('patrimonio', 'Patrimônio'),
                                         ('controladoria', 'Controladoria')])
    is_admin      = BooleanField('Administrador (acesso gerencial)')
    power_bi_access = BooleanField('Acesso ao Power BI (Business Intelligence)')
    ouvidoria_all_states = BooleanField('Visualizar denúncias de todos os estados')
    status        = SelectField('Status',
                                choices=[('active', 'Ativo'), ('inactive', 'Inativo'),
                                         ('blocked', 'Bloqueado')])
    department_id = SelectField('Departamento', coerce=int, validators=[Optional()])
    state_id      = SelectField('Estado (unidade)', coerce=int, validators=[Optional()])
    birth_date    = DateField('Data de nascimento', validators=[Optional()])

    profile_picture = FileField('Foto de perfil',
                                validators=[
                                    Optional(),
                                    FileAllowed(['png', 'jpg', 'jpeg', 'webp'],
                                                'Apenas imagens PNG, JPG ou WEBP.'),
                                ])

    password         = PasswordField('Senha',
                                     validators=[Optional(), Length(min=6, max=128,
                                                 message='A senha deve ter no mínimo 6 caracteres.')])
    password_confirm = PasswordField('Confirmar senha',
                                     validators=[Optional(),
                                                 EqualTo('password',
                                                         message='As senhas não conferem.')])

    submit = SubmitField('Salvar')

    def __init__(self, departments, states=None, user_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user_id = user_id
        dept_choices = [(0, '— Sem departamento —')] + [(d.id, d.name) for d in departments]
        self.department_id.choices = dept_choices
        state_choices = [(0, '— Sem estado —')] + [(s.id, s.name) for s in (states or [])]
        self.state_id.choices = state_choices

    def validate_cpf(self, field):
        query = User.query.filter_by(cpf=field.data)
        if self._user_id:
            query = query.filter(User.id != self._user_id)
        if query.first():
            raise ValidationError('Este CPF já está cadastrado.')

    def validate_email(self, field):
        _validate_corporate_email(field)
        query = User.query.filter_by(email=field.data)
        if self._user_id:
            query = query.filter(User.id != self._user_id)
        if query.first():
            raise ValidationError('Este e-mail já está cadastrado.')

    def validate_password(self, field):
        # Senha obrigatória somente na criação (user_id=None)
        if self._user_id is None and not field.data:
            raise ValidationError('A senha é obrigatória para novos usuários.')


class InviteUserForm(FlaskForm):
    """Convida um novo colaborador gerando a senha via e-mail."""

    name          = StringField('Nome completo',
                                validators=[DataRequired(), Length(max=150)])
    cpf           = StringField('CPF',
                                validators=[DataRequired(), _validate_cpf])
    email         = StringField('E-mail corporativo',
                                validators=[DataRequired(), Email(), Length(max=150)])
    role          = SelectField('Perfil / área',
                                choices=[('user', 'Usuário'), ('editor', 'Editor'),
                                         ('rh', 'Diretoria'), ('patrimonio', 'Patrimônio'),
                                         ('controladoria', 'Controladoria')])
    is_admin      = BooleanField('Administrador (acesso gerencial)')
    department_id = SelectField('Departamento', coerce=int, validators=[Optional()])
    state_id      = SelectField('Estado (unidade)', coerce=int, validators=[Optional()])
    submit        = SubmitField('Enviar convite')

    def __init__(self, departments, states=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        dept_choices = [(0, '— Sem departamento —')] + [(d.id, d.name) for d in departments]
        self.department_id.choices = dept_choices
        state_choices = [(0, '— Sem estado —')] + [(s.id, s.name) for s in (states or [])]
        self.state_id.choices = state_choices

    def validate_cpf(self, field):
        if User.query.filter_by(cpf=field.data).first():
            raise ValidationError('Este CPF já está cadastrado.')

    def validate_email(self, field):
        _validate_corporate_email(field)
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Este e-mail já está cadastrado.')


class AdminSetPasswordForm(FlaskForm):
    password  = PasswordField('Nova senha *',
                              validators=[DataRequired(), Length(min=8, max=128)])
    password2 = PasswordField('Confirmar senha *',
                              validators=[DataRequired(),
                                          EqualTo('password', message='As senhas não conferem.')])
    force_change = BooleanField('Exigir troca no próximo login', default=True)
    submit    = SubmitField('Salvar senha')


class ProfileForm(FlaskForm):
    """Formulário de perfil para o próprio usuário editar."""
    name       = StringField('Nome completo *',
                             validators=[DataRequired(), Length(max=150)])
    email      = StringField('E-mail *',
                             validators=[DataRequired(), Email(), Length(max=150)])
    birth_date = DateField('Data de nascimento', validators=[Optional()])
    profile_picture = FileField('Foto de perfil',
                                validators=[
                                    Optional(),
                                    FileAllowed(['png', 'jpg', 'jpeg', 'webp'],
                                                'Apenas imagens PNG, JPG ou WEBP.'),
                                ])
    submit = SubmitField('Salvar perfil')

    def __init__(self, user_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user_id = user_id

    def validate_email(self, field):
        email = (field.data or '').strip().lower()
        field.data = email
        query = User.query.filter_by(email=email)
        if self._user_id:
            query = query.filter(User.id != self._user_id)
        if query.first():
            raise ValidationError('Este e-mail já está cadastrado.')
