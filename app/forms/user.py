from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (BooleanField, DateField, PasswordField, SelectField,
                     StringField, SubmitField)
from wtforms.validators import (DataRequired, Email, EqualTo, Length,
                                Optional, ValidationError)

from app.models.user import User


class UserForm(FlaskForm):
    """Formulário compartilhado entre criar e editar usuário."""

    name          = StringField('Nome completo',
                                validators=[DataRequired(), Length(max=150)])
    email         = StringField('E-mail corporativo',
                                validators=[DataRequired(), Email(), Length(max=150)])
    role          = SelectField('Perfil',
                                choices=[('user', 'Usuário'), ('editor', 'Editor'),
                                         ('viewer', 'Visualizador'), ('admin', 'Administrador')])
    status        = SelectField('Status',
                                choices=[('active', 'Ativo'), ('inactive', 'Inativo'),
                                         ('blocked', 'Bloqueado')])
    department_id = SelectField('Departamento', coerce=int, validators=[Optional()])
    birth_date    = DateField('Data de nascimento', validators=[Optional()])

    two_factor_mandatory = BooleanField('2FA obrigatório')

    profile_picture = FileField('Foto de perfil',
                                validators=[
                                    Optional(),
                                    FileAllowed(['png', 'jpg', 'jpeg', 'webp'],
                                                'Apenas imagens PNG, JPG ou WEBP.'),
                                ])

    submit = SubmitField('Salvar')

    def __init__(self, departments, user_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user_id = user_id
        dept_choices = [(0, '— Sem departamento —')] + [(d.id, d.name) for d in departments]
        self.department_id.choices = dept_choices

    def validate_email(self, field):
        query = User.query.filter_by(email=field.data)
        if self._user_id:
            query = query.filter(User.id != self._user_id)
        if query.first():
            raise ValidationError('Este e-mail já está cadastrado.')


class InviteUserForm(FlaskForm):
    """Convida um novo colaborador gerando a senha via e-mail."""

    name          = StringField('Nome completo',
                                validators=[DataRequired(), Length(max=150)])
    email         = StringField('E-mail corporativo',
                                validators=[DataRequired(), Email(), Length(max=150)])
    role          = SelectField('Perfil',
                                choices=[('user', 'Usuário'), ('editor', 'Editor'),
                                         ('viewer', 'Visualizador'), ('admin', 'Administrador')])
    department_id = SelectField('Departamento', coerce=int, validators=[Optional()])
    submit        = SubmitField('Enviar convite')

    def __init__(self, departments, *args, **kwargs):
        super().__init__(*args, **kwargs)
        dept_choices = [(0, '— Sem departamento —')] + [(d.id, d.name) for d in departments]
        self.department_id.choices = dept_choices

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Este e-mail já está cadastrado.')


class BlockedIpForm(FlaskForm):
    ip_address = StringField('Endereço IP', validators=[DataRequired(), Length(max=45)])
    reason     = StringField('Motivo', validators=[Optional(), Length(max=255)])
    submit     = SubmitField('Bloquear IP')


class AdminSetPasswordForm(FlaskForm):
    password  = PasswordField('Nova senha *',
                              validators=[DataRequired(), Length(min=8, max=128)])
    password2 = PasswordField('Confirmar senha *',
                              validators=[DataRequired(),
                                          EqualTo('password', message='As senhas não conferem.')])
    force_change = BooleanField('Exigir troca no próximo login', default=True)
    submit    = SubmitField('Salvar senha')
