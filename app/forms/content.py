from datetime import date

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (BooleanField, DateField, IntegerField, SelectField,
                     StringField, SubmitField, TextAreaField, TimeField, URLField)
from wtforms.validators import DataRequired, Length, NumberRange, Optional, URL


class BannerForm(FlaskForm):
    title       = StringField('Título', validators=[Optional(), Length(max=100)])
    description = TextAreaField('Descrição', validators=[Optional()])
    image       = FileField(
        'Imagem *',
        validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Imagens apenas.')],
    )
    link_url    = URLField('URL do link', validators=[Optional(), URL()])
    link_text   = StringField('Texto do botão', validators=[Optional(), Length(max=50)])
    target_blank = BooleanField('Abrir em nova aba', default=True)
    order_position = IntegerField('Ordem', validators=[Optional(), NumberRange(min=0)], default=0)
    is_active   = BooleanField('Ativo', default=True)
    start_date  = DateField('Data de início', validators=[Optional()])
    end_date    = DateField('Data de término', validators=[Optional()])
    submit      = SubmitField('Salvar')


class FaqCategoryForm(FlaskForm):
    name           = StringField('Nome', validators=[DataRequired(), Length(max=100)])
    description    = TextAreaField('Descrição', validators=[Optional()])
    order_position = IntegerField('Ordem', validators=[Optional(), NumberRange(min=0)], default=0)
    is_active      = BooleanField('Ativo', default=True)
    submit         = SubmitField('Salvar')


class FaqForm(FlaskForm):
    category_id    = SelectField('Categoria', coerce=int, validators=[Optional()])
    question       = StringField('Pergunta', validators=[DataRequired(), Length(max=255)])
    answer         = TextAreaField('Resposta', validators=[DataRequired()])
    order_position = IntegerField('Ordem', validators=[Optional(), NumberRange(min=0)], default=0)
    is_active      = BooleanField('Ativo', default=True)
    submit         = SubmitField('Salvar')


class EventForm(FlaskForm):
    title       = StringField('Título', validators=[DataRequired(), Length(max=255)])
    description = TextAreaField('Descrição', validators=[Optional()])
    event_date  = DateField('Data *', validators=[DataRequired()])
    event_time  = TimeField('Horário', validators=[Optional()])
    end_date    = DateField('Data de término', validators=[Optional()])
    location    = StringField('Local', validators=[Optional(), Length(max=255)])
    location_url = URLField('Link do local (Maps)', validators=[Optional(), URL()])
    event_type  = SelectField(
        'Tipo',
        choices=[('general','Geral'), ('meeting','Reunião'),
                 ('training','Treinamento'), ('holiday','Feriado'), ('birthday','Aniversário')],
        default='general',
    )
    is_active   = BooleanField('Ativo', default=True)
    submit      = SubmitField('Salvar')


class LinkForm(FlaskForm):
    title          = StringField('Título *', validators=[DataRequired(), Length(max=150)])
    url            = URLField('URL *', validators=[DataRequired(), URL()])
    description    = StringField('Descrição', validators=[Optional(), Length(max=255)])
    icon_class     = StringField('Ícone (CSS class)', validators=[Optional(), Length(max=50)])
    order_position = IntegerField('Ordem', validators=[Optional(), NumberRange(min=0)], default=0)
    target_blank   = BooleanField('Abrir em nova aba', default=True)
    is_active      = BooleanField('Ativo', default=True)
    submit         = SubmitField('Salvar')
