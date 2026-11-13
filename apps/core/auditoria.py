from .models import Auditoria


def registrar(usuario, accion: str, objeto, detalle: str = "") -> None:
    """Deja constancia de una acción en la bitácora de auditoría."""
    if hasattr(objeto, "_meta"):
        objeto = f"{objeto._meta.verbose_name} #{objeto.pk}: {objeto}"
    Auditoria.objects.create(
        usuario=usuario if getattr(usuario, "is_authenticated", False) else None,
        accion=accion,
        objeto=str(objeto)[:120],
        detalle=detalle,
    )
