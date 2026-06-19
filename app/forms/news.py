import re

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (BooleanField, HiddenField, SelectMultipleField, StringField,
                     SubmitField, TextAreaField, widgets)
from wtforms.validators import DataRequired, Length, Optional


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[àáâãä]', 'a', text)
    text = re.sub(r'[èéêë]', 'e', text)
    text = re.sub(r'[ìíîï]', 'i', text)
    text = re.sub(r'[òóôõö]', 'o', text)
    text = re.sub(r'[ùúûü]', 'u', text)
    text = re.sub(r'[ç]', 'c', text)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text)
    return text


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class NewsForm(FlaskForm):
    title = StringField(
        'Título',
        validators=[DataRequired(), Length(max=255)],
    )
    slug = StringField(
        'Slug',
        validators=[Optional(), Length(max=255)],
        description='Deixe em branco para gerar automaticamente.',
    )
    summary = TextAreaField(
        'Resumo',
        validators=[Optional(), Length(max=500)],
    )
    # O conteúdo rico vem como JSON (string) do editor no front-end
    content_json = TextAreaField(
        'Conteúdo',
        validators=[DataRequired()],
    )
    featured_image = FileField(
        'Imagem de destaque',
        validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Imagens apenas.')],
    )
    featured_image_size = HiddenField('Tamanho da imagem', default='banner')
    categories = MultiCheckboxField('Categorias', coerce=int)
    tags_input = StringField(
        'Tags',
        validators=[Optional()],
        description='Separe por vírgula. Ex: tecnologia, rh, evento',
    )
    is_published = BooleanField('Publicar imediatamente')
    submit = SubmitField('Salvar')


class CategoryForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired(), Length(max=100)])
    slug = StringField('Slug', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Salvar')
