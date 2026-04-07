from flask_wtf import FlaskForm
from wtforms import (BooleanField, DateTimeLocalField, FieldList, FormField,
                     IntegerField, StringField, SubmitField, TextAreaField)
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class PollOptionForm(FlaskForm):
    class Meta:
        csrf = False  # subform — CSRF no form pai

    option_text    = StringField('Opção', validators=[DataRequired(), Length(max=255)])
    order_position = IntegerField('Ordem', default=0, validators=[Optional(), NumberRange(min=0)])


class PollForm(FlaskForm):
    question    = StringField('Pergunta *', validators=[DataRequired(), Length(max=255)])
    description = TextAreaField('Descrição', validators=[Optional()])
    is_multiple = BooleanField('Múltipla escolha', default=False)
    is_active   = BooleanField('Ativa', default=True)
    expires_at  = DateTimeLocalField('Expira em', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    options     = FieldList(FormField(PollOptionForm), min_entries=2)
    submit      = SubmitField('Salvar')
