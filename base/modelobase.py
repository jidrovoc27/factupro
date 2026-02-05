from datetime import datetime
from django.db import models, connection
from django.contrib.auth.models import User

class ModeloBase(models.Model):
    status = models.BooleanField(default=True)
    usuario_creacion = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+', blank=True, null=True)
    fecha_creacion = models.DateTimeField(blank=True, null=True)
    usuario_modificacion = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+', blank=True, null=True)
    fecha_modificacion = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        usuario = None
        if len(args):
            usuario = args[0].user.id
        if self.id:
            self.usuario_modificacion_id = usuario if usuario else 1
            self.fecha_modificacion = datetime.now()
        else:
            self.usuario_creacion_id = usuario if usuario else 1
            self.fecha_creacion = datetime.now()
        models.Model.save(self)

    class Meta:
        abstract = True