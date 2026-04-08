import json
import re

from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, ValidationError


def _slugify(text: str) -> str:
    text = text.lower().strip()
    for src, dst in [('àáâãä','a'),('èéêë','e'),('ìíîï','i'),('òóôõö','o'),('ùúûü','u'),('ç','c')]:
        for c in src:
            text = text.replace(c, dst)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    return re.sub(r'\s+', '-', text).strip('-')


class PageForm(FlaskForm):
    name         = StringField('Nome interno *',
                               validators=[DataRequired(), Length(max=100)],
                               description='Identificador interno, ex: "Sobre a empresa"')
    slug         = StringField('Slug (URL) *',
                               validators=[DataRequired(), Length(max=100)],
                               description='Gerado automaticamente. Ex: sobre-a-empresa')
    title        = StringField('Título da página *',
                               validators=[DataRequired(), Length(max=200)])
    content_json = HiddenField('Conteúdo')
    is_published = BooleanField('Publicada', default=True)
    submit       = SubmitField('Salvar')

    def validate_content_json(self, field):
        if field.data:
            try:
                json.loads(field.data)
            except (json.JSONDecodeError, TypeError):
                raise ValidationError('Conteúdo inválido.')
