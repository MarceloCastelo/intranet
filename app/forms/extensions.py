from flask_wtf import FlaskForm
from wtforms import (BooleanField, IntegerField, SelectField, StringField,
                     SubmitField, TextAreaField)
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class PhoneExtensionForm(FlaskForm):
    name           = StringField('Nome / Setor *', validators=[DataRequired(), Length(max=150)])
    extension      = StringField('Ramal *', validators=[DataRequired(), Length(max=20)])
    department_id  = SelectField('Departamento', coerce=int, validators=[Optional()])
    user_id        = SelectField('Usuário vinculado', coerce=int, validators=[Optional()])
    notes          = StringField('Observação', validators=[Optional(), Length(max=255)])
    order_position = IntegerField('Ordem', default=0, validators=[Optional(), NumberRange(min=0)])
    is_active      = BooleanField('Ativo', default=True)
    submit         = SubmitField('Salvar')
