from django.db import models


class ArchivoAnalizado(models.Model):
    nombre = models.CharField(max_length=255)
    extension = models.CharField(max_length=20, blank=True) #blank es que el campo puede quedar vacio, el max_length es el tama;o maximo
    tipo_detectado = models.CharField(max_length=50)
    mime = models.CharField(max_length=100, blank=True)
    tamano = models.PositiveBigIntegerField()
    fecha = models.DateTimeField(auto_now_add=True) # django pone la fecha actual de cuando se cree un registro xd

    def __str__(self):
        return self.nombre
        #esto sirve para que salga el registro en texto en vez de como un objeto, mira tu, no tenia idea xd
