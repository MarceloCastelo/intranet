from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError
import re


def _validate_cpf(form, field):
    """Valida formato e dígitos verificadores do CPF."""
    raw = re.sub(r'\D', '', field.data or '')
    if len(raw) != 11 or len(set(raw)) == 1:
        raise ValidationError('CPF inválido.')
    # Primeiro dígito verificador
    total = sum(int(raw[i]) * (10 - i) for i in range(9))
    d1 = 0 if (total * 10 % 11) >= 10 else (total * 10 % 11)
    # Segundo dígito verificador
    total = sum(int(raw[i]) * (11 - i) for i in range(10))
    d2 = 0 if (total * 10 % 11) >= 10 else (total * 10 % 11)
    if int(raw[9]) != d1 or int(raw[10]) != d2:
        raise ValidationError('CPF inválido.')
    field.data = raw  # normaliza para só dígitos


def _normalize_cpf(form, field):
    """Para login: apenas normaliza (remove pontos/traços) e valida o tamanho."""
    raw = re.sub(r'\D', '', field.data or '')
    if len(raw) != 11:
        raise ValidationError('CPF deve conter 11 dígitos.')
    field.data = raw


class LoginForm(FlaskForm):
    cpf      = StringField('CPF', validators=[DataRequired(), _normalize_cpf])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember = BooleanField('Manter conectado')
    submit   = SubmitField('Entrar')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Senha atual', validators=[DataRequired()])
    new_password     = PasswordField(
        'Nova senha',
        validators=[DataRequired(), Length(min=8, message='Mínimo de 8 caracteres.')],
    )
    confirm_password = PasswordField(
        'Confirmar nova senha',
        validators=[DataRequired(), EqualTo('new_password', message='As senhas não coincidem.')],
    )
    submit = SubmitField('Alterar senha')


class SetPasswordForm(FlaskForm):
    """Usado no primeiro login (sem pedir senha atual)."""
    new_password = PasswordField(
        'Nova senha',
        validators=[DataRequired(), Length(min=8, message='Mínimo de 8 caracteres.')],
    )
    confirm_password = PasswordField(
        'Confirmar nova senha',
        validators=[DataRequired(), EqualTo('new_password', message='As senhas não coincidem.')],
    )
    submit = SubmitField('Definir senha')


class ForgotPasswordForm(FlaskForm):
    cpf    = StringField('CPF', validators=[DataRequired(), _validate_cpf])
    submit = SubmitField('Enviar instruções')


class ResetPasswordForm(FlaskForm):
    new_password = PasswordField(
        'Nova senha',
        validators=[DataRequired(), Length(min=8, message='Mínimo de 8 caracteres.')],
    )
    confirm_password = PasswordField(
        'Confirmar nova senha',
        validators=[DataRequired(), EqualTo('new_password', message='As senhas não coincidem.')],
    )
    submit = SubmitField('Redefinir senha')
