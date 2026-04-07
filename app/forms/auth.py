from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class LoginForm(FlaskForm):
    email    = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember = BooleanField('Manter conectado')
    submit   = SubmitField('Entrar')


class TwoFactorForm(FlaskForm):
    code   = StringField('Código de verificação',
                         validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField('Verificar')


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
    email  = StringField('E-mail', validators=[DataRequired(), Email()])
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
