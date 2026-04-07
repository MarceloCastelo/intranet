from flask_wtf import FlaskForm
from wtforms import (BooleanField, IntegerField, SelectField, StringField,
                     SubmitField, TextAreaField, URLField)
from wtforms.validators import DataRequired, Length, NumberRange, Optional, URL

COLOR_CHOICES = [
    ('blue',   'Azul'),
    ('indigo', 'Índigo'),
    ('violet', 'Violeta'),
    ('green',  'Verde'),
    ('emerald','Esmeralda'),
    ('teal',   'Turquesa'),
    ('orange', 'Laranja'),
    ('red',    'Vermelho'),
    ('pink',   'Rosa'),
    ('amber',  'Âmbar'),
    ('slate',  'Cinza'),
]


class ServiceForm(FlaskForm):
    title          = StringField('Título *', validators=[DataRequired(), Length(max=150)])
    url            = URLField('URL *', validators=[DataRequired(), URL(), Length(max=500)])
    description    = StringField('Descrição', validators=[Optional(), Length(max=255)])
    category       = StringField('Categoria',
                                 validators=[Optional(), Length(max=100)],
                                 render_kw={'placeholder': 'Ex.: TI, RH, Financeiro…'})
    color          = SelectField('Cor do card', choices=COLOR_CHOICES, default='blue')
    icon_url       = URLField('URL do ícone/logo', validators=[Optional(), Length(max=500)],
                              render_kw={'placeholder': 'https://…'})
    target_blank   = BooleanField('Abrir em nova aba', default=True)
    order_position = IntegerField('Ordem', default=0,
                                  validators=[Optional(), NumberRange(min=0)])
    is_active      = BooleanField('Ativo', default=True)
    submit         = SubmitField('Salvar')
