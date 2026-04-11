import os
import uuid

from PIL import Image
from flask import current_app
from werkzeug.exceptions import BadRequest

from app import db
from app.models.content import Gallery, GalleryItem

_ALLOWED_IMAGE_EXTS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def _save_gallery_image(file_storage, gallery_id: int):
    """Salva imagem original + thumbnail. Retorna (image_path, thumb_path)."""
    ext = os.path.splitext(file_storage.filename)[1].lstrip('.').lower() or 'jpg'
    if ext not in _ALLOWED_IMAGE_EXTS:
        raise BadRequest(f'Tipo de arquivo não permitido: .{ext}')
    upload_dir = os.path.join(current_app.root_path, '..', 'uploads', 'gallery', str(gallery_id))
    thumb_dir  = os.path.join(upload_dir, 'thumbs')
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(thumb_dir,  exist_ok=True)

    filename = f"{uuid.uuid4().hex}.{ext}"

    full_path  = os.path.join(upload_dir, filename)
    thumb_path = os.path.join(thumb_dir,  filename)

    img = Image.open(file_storage)
    img.save(full_path, optimize=True, quality=90)

    thumb = img.copy()
    thumb.thumbnail((400, 400))
    thumb.save(thumb_path, optimize=True, quality=80)

    image_url = f'/uploads/gallery/{gallery_id}/{filename}'
    thumb_url = f'/uploads/gallery/{gallery_id}/thumbs/{filename}'
    return image_url, thumb_url


# ─── Galerias ─────────────────────────────────────────────────────────────────

def list_galleries(page: int = 1, active_only: bool = False):
    q = Gallery.query
    if active_only:
        q = q.filter(Gallery.is_active == True)  # noqa: E712
    return q.order_by(Gallery.created_at.desc()).paginate(page=page, per_page=20, error_out=False)


def active_galleries():
    return (Gallery.query
            .filter(Gallery.is_active == True)  # noqa: E712
            .order_by(Gallery.created_at.desc())
            .all())


def get_gallery_or_404(gallery_id: int) -> Gallery:
    return db.get_or_404(Gallery, gallery_id)


def create_gallery(form, actor_id: int, force_inactive: bool = False) -> Gallery:
    gallery = Gallery(
        title       = form.title.data.strip(),
        description = form.description.data or None,
        is_active   = False if force_inactive else form.is_active.data,
        created_by  = actor_id,
    )
    db.session.add(gallery)
    db.session.commit()
    return gallery


def update_gallery(gallery: Gallery, form) -> Gallery:
    gallery.title       = form.title.data.strip()
    gallery.description = form.description.data or None
    gallery.is_active   = form.is_active.data
    db.session.commit()
    return gallery


def delete_gallery(gallery: Gallery) -> None:
    db.session.delete(gallery)
    db.session.commit()


# ─── Itens ────────────────────────────────────────────────────────────────────

def get_item_or_404(item_id: int) -> GalleryItem:
    return db.get_or_404(GalleryItem, item_id)


def add_items(gallery: Gallery, files: list, captions: list, actor_id: int) -> list:
    """Recebe lista de FileStorage e captions paralelas; salva e retorna GalleryItems."""
    items = []
    next_order = (
        db.session.query(db.func.max(GalleryItem.order_position))
        .filter_by(gallery_id=gallery.id)
        .scalar() or 0
    ) + 1

    for i, fs in enumerate(files):
        if not fs or not fs.filename:
            continue
        image_url, thumb_url = _save_gallery_image(fs, gallery.id)
        caption = captions[i] if i < len(captions) else ''
        item = GalleryItem(
            gallery_id     = gallery.id,
            image_path     = image_url,
            thumbnail_path = thumb_url,
            caption        = caption or None,
            order_position = next_order + i,
        )
        db.session.add(item)
        items.append(item)

        # Primeira imagem vira capa se não houver
        if i == 0 and not gallery.cover_image:
            gallery.cover_image = thumb_url

    db.session.commit()
    return items


def delete_item(item: GalleryItem) -> None:
    gallery = item.gallery
    db.session.delete(item)
    # Se era a capa, atualiza para o próximo item disponível
    if gallery.cover_image and (
        gallery.cover_image == item.thumbnail_path or
        gallery.cover_image == item.image_path
    ):
        remaining = (GalleryItem.query
                     .filter_by(gallery_id=gallery.id)
                     .filter(GalleryItem.id != item.id)
                     .order_by(GalleryItem.order_position)
                     .first())
        gallery.cover_image = remaining.thumbnail_path if remaining else None
    db.session.commit()


def set_cover(gallery: Gallery, item: GalleryItem) -> None:
    gallery.cover_image = item.thumbnail_path
    db.session.commit()
