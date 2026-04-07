from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import BooleanField, IntegerField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class GalleryForm(FlaskForm):
    title       = StringField('Título *', validators=[DataRequired(), Length(max=255)])
    description = TextAreaField('Descrição', validators=[Optional()])
    is_active   = BooleanField('Ativa', default=True)
    submit      = SubmitField('Salvar')


class GalleryItemForm(FlaskForm):
    images  = FileField(
        'Imagens *',
        validators=[
            FileRequired(),
            FileAllowed(['jpg', 'jpeg', 'png', 'webp', 'gif'], 'Somente imagens.'),
        ],
    )
    caption        = StringField('Legenda', validators=[Optional(), Length(max=255)])
    order_position = IntegerField('Ordem', default=0, validators=[Optional(), NumberRange(min=0)])
    submit         = SubmitField('Enviar')
