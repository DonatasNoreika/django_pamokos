from django.db import models
from django.urls import reverse  # Papildome imports
import uuid
from django.contrib.auth.models import User
from datetime import date
from tinymce.models import HTMLField
from PIL import Image
from django.utils.translation import gettext_lazy as _
import datetime


# Create your models here.
class Genre(models.Model):
    name = models.CharField('Pavadinimas', max_length=200, help_text='Įveskite knygos žanrą (pvz. detektyvas)')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Žanras'
        verbose_name_plural = 'Žanrai'


# class Book(models.Model):
#     """Modelis reprezentuoja knygą (bet ne specifinę knygos kopiją)"""
#     title = models.CharField(_('Pavadinimas'), max_length=200)
#     author = models.ForeignKey(_('Author'), on_delete=models.SET_NULL, null=True, related_name='books')
#     summary = models.TextField(_('Aprašymas'), max_length=1000, help_text=_('Trumpas knygos aprašymas'))
#     isbn = models.CharField('ISBN', max_length=13,
#                             help_text='13 Simbolių <a href="https://www.isbn-international.org/content/what-isbn">ISBN kodas</a>')
#     genre = models.ManyToManyField(Genre, help_text=_('Išrinkite žanrą(us) šiai knygai'))
#     cover = models.ImageField(_('Viršelis'), upload_to='covers', null=True)

class Book(models.Model):
    """Modelis reprezentuoja knygą (bet ne specifinę knygos kopiją)"""
    title = models.CharField(_('Title'), max_length=200)
    author = models.ForeignKey('Author', verbose_name=_("Author"), on_delete=models.SET_NULL, null=True,
                               related_name='books')
    summary = models.TextField(_('Summary'), max_length=1000, help_text=_('Short book summary'))
    isbn = models.CharField('ISBN', max_length=13,
                            help_text='13 Simbolių <a href="https://www.isbn-international.org/content/what-isbn">ISBN kodas</a>')
    genre = models.ManyToManyField(Genre, help_text=_('Please choose genres'))
    # genre = models.ForeignKey('Žanras', Genre)
    cover = models.ImageField(_('Cover'), upload_to='covers', null=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """Nurodo konkretaus aprašymo galinį adresą"""
        return reverse('book-detail', args=[str(self.id)])

    def display_genre(self):
        return ', '.join(genre.name for genre in self.genre.all()[:3])

    display_genre.short_description = 'Žanras'

    class Meta:
        verbose_name = 'Knyga'
        verbose_name_plural = 'Knygos'


class BookInstance(models.Model):
    """Modelis, aprašantis konkrečios knygos kopijos būseną"""
    uuid = models.UUIDField(default=uuid.uuid4, help_text='Unikalus ID knygos kopijai')
    book = models.ForeignKey('Book', on_delete=models.SET_NULL, null=True)
    due_back = models.DateField('Bus prieinama', null=True, blank=True)
    reader = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    LOAN_STATUS = (
        ('a', 'Administruojama'),
        ('p', 'Paimta'),
        ('g', 'Galima paimti'),
        ('r', 'Rezervuota'),
    )

    @property
    def is_overdue(self):
        if self.due_back and date.today() > self.due_back:
            return True
        return False

    status = models.CharField(
        max_length=1,
        choices=LOAN_STATUS,
        blank=True,
        default='p',
        help_text='Statusas',
    )

    class Meta:
        ordering = ['due_back']
        verbose_name = 'Knygos egzempliorius'
        verbose_name_plural = 'Knygų egzemplioriai'

    def __str__(self):
        return f'{self.id} ({self.book.title})'


class Author(models.Model):
    """Model representing an author."""
    first_name = models.CharField('Vardas', max_length=100)
    last_name = models.CharField('Pavardė', max_length=100)
    description = HTMLField("Aprašymas")

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'Autorius'
        verbose_name_plural = 'Autoriai'

    def get_absolute_url(self):
        """Returns the url to access a particular author instance."""
        return reverse('author-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.last_name} {self.first_name}'

    def display_books(self):
        return ', '.join(book.title for book in self.books.all()[:3])

    display_books.short_description = 'Knygos'


class BookReview(models.Model):
    book = models.ForeignKey('Book', on_delete=models.SET_NULL, null=True, blank=True)
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    content = models.TextField('Atsiliepimas', max_length=2000)

    class Meta:
        verbose_name = 'Atsiliepimas'
        verbose_name_plural = 'Atsiliepimai'


class Profilis(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nuotrauka = models.ImageField(default="default.png", upload_to="profile_pics")

    def __str__(self):
        return f"{self.user.username} profilis"

    def crop_center(self, pil_img, crop_width, crop_height):
        img_width, img_height = pil_img.size
        return pil_img.crop(((img_width - crop_width) // 2,
                             (img_height - crop_height) // 2,
                             (img_width + crop_width) // 2,
                             (img_height + crop_height) // 2))

    def save(self):
        super().save()
        img = Image.open(self.nuotrauka.path)
        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img = self.crop_center(img, min(img.size), min(img.size))
            img.thumbnail(output_size)
            img.save(self.nuotrauka.path)


