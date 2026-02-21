"""
Capa de abstracción de almacenamiento - ArqueoTrack v4.0
Soporta almacenamiento local (desarrollo) y S3/MinIO (producción).

Uso:
    storage = get_storage()
    path = storage.save('uploads/foto.jpg', file_data)
    url  = storage.url(path)
    storage.delete(path)
"""

import os
import uuid
import hashlib
from abc import ABC, abstractmethod
from typing import BinaryIO, Optional
from pathlib import Path
from datetime import datetime

import structlog

log = structlog.get_logger(__name__)


# ── Interfaz base ──────────────────────────────────────────────────────────────

class StorageBackend(ABC):
    """Interfaz abstracta para backends de almacenamiento."""

    @abstractmethod
    def save(self, file_obj: BinaryIO, folder: str, filename: Optional[str] = None,
             content_type: str = 'application/octet-stream') -> str:
        """
        Guarda un archivo y devuelve la ruta relativa (key) del archivo guardado.

        Args:
            file_obj: Objeto de archivo (stream binario).
            folder: Carpeta/prefijo donde guardar (ej: 'hallazgos/fotos').
            filename: Nombre de archivo deseado. Si None, se genera uno único.
            content_type: MIME type del archivo.

        Returns:
            Ruta/key del archivo guardado.
        """

    @abstractmethod
    def delete(self, path: str) -> bool:
        """Elimina un archivo. Retorna True si tuvo éxito."""

    @abstractmethod
    def url(self, path: str) -> str:
        """Devuelve la URL pública del archivo."""

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Comprueba si un archivo existe."""

    @staticmethod
    def _safe_filename(original: str) -> str:
        """Genera un nombre de archivo seguro con UUID para evitar colisiones."""
        ext = Path(original).suffix.lower() if original else ''
        return f'{uuid.uuid4().hex}{ext}'


# ── Backend local ──────────────────────────────────────────────────────────────

class LocalStorage(StorageBackend):
    """
    Almacenamiento local en disco.
    Ideal para desarrollo y despliegues sin S3.
    """

    def __init__(self, base_path: str, base_url: str = '/uploads'):
        self.base_path = Path(base_path)
        self.base_url = base_url.rstrip('/')
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save(self, file_obj: BinaryIO, folder: str, filename: Optional[str] = None,
             content_type: str = 'application/octet-stream') -> str:
        if not filename:
            filename = self._safe_filename(getattr(file_obj, 'filename', 'file'))
        else:
            filename = self._safe_filename(filename)

        dest_dir = self.base_path / folder
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / filename
        rel_path = f'{folder}/{filename}'

        try:
            if hasattr(file_obj, 'save'):
                file_obj.save(str(dest_path))
            else:
                with open(dest_path, 'wb') as f:
                    while chunk := file_obj.read(65536):
                        f.write(chunk)
            log.info('storage.saved', backend='local', path=rel_path)
            return rel_path
        except OSError as exc:
            log.error('storage.save_error', backend='local', error=str(exc))
            raise

    def delete(self, path: str) -> bool:
        full_path = self.base_path / path
        try:
            full_path.unlink(missing_ok=True)
            log.info('storage.deleted', backend='local', path=path)
            return True
        except OSError as exc:
            log.warning('storage.delete_error', backend='local', path=path, error=str(exc))
            return False

    def url(self, path: str) -> str:
        return f'{self.base_url}/{path}'

    def exists(self, path: str) -> bool:
        return (self.base_path / path).exists()


# ── Backend S3 / MinIO ─────────────────────────────────────────────────────────

class S3Storage(StorageBackend):
    """
    Almacenamiento en AWS S3 o MinIO (API compatible).
    Requiere boto3: pip install boto3
    """

    def __init__(self, bucket: str, region: str = 'eu-west-1',
                 endpoint_url: Optional[str] = None,
                 access_key: Optional[str] = None,
                 secret_key: Optional[str] = None,
                 public_base_url: Optional[str] = None):
        try:
            import boto3
            from botocore.exceptions import BotoCoreError, ClientError
        except ImportError:
            raise ImportError('boto3 es necesario para S3Storage: pip install boto3')

        self.bucket = bucket
        self.public_base_url = public_base_url
        self._boto3 = boto3
        self._BotoCoreError = BotoCoreError
        self._ClientError = ClientError

        session = boto3.Session(
            aws_access_key_id=access_key or os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=secret_key or os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=region,
        )
        self.client = session.client('s3', endpoint_url=endpoint_url)

    def save(self, file_obj: BinaryIO, folder: str, filename: Optional[str] = None,
             content_type: str = 'application/octet-stream') -> str:
        if not filename:
            filename = self._safe_filename(getattr(file_obj, 'filename', 'file'))
        else:
            filename = self._safe_filename(filename)

        key = f'{folder.strip("/")}/{filename}'
        try:
            data = file_obj.read() if hasattr(file_obj, 'read') else file_obj
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
            log.info('storage.saved', backend='s3', bucket=self.bucket, key=key)
            return key
        except (self._BotoCoreError, self._ClientError) as exc:
            log.error('storage.s3_error', key=key, error=str(exc))
            raise

    def delete(self, path: str) -> bool:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=path)
            log.info('storage.deleted', backend='s3', key=path)
            return True
        except (self._BotoCoreError, self._ClientError) as exc:
            log.warning('storage.s3_delete_error', key=path, error=str(exc))
            return False

    def url(self, path: str) -> str:
        if self.public_base_url:
            return f'{self.public_base_url.rstrip("/")}/{path}'
        return self.client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': path},
            ExpiresIn=3600,
        )

    def exists(self, path: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=path)
            return True
        except Exception:
            return False


# ── Factory ───────────────────────────────────────────────────────────────────

_instance: Optional[StorageBackend] = None


def get_storage() -> StorageBackend:
    """
    Retorna la instancia singleton del backend de almacenamiento
    configurado por variables de entorno.

    Variables de entorno:
        STORAGE_BACKEND: 'local' (default) | 's3' | 'minio'
        STORAGE_LOCAL_PATH: Directorio base para almacenamiento local.
        STORAGE_LOCAL_URL: URL base para archivos locales.
        AWS_S3_BUCKET: Nombre del bucket S3/MinIO.
        AWS_REGION: Región AWS (default: eu-west-1).
        AWS_ENDPOINT_URL: Endpoint para MinIO (ej: http://minio:9000).
        AWS_PUBLIC_BASE_URL: URL pública para MinIO sin presigned URLs.
    """
    global _instance
    if _instance is not None:
        return _instance

    backend = os.environ.get('STORAGE_BACKEND', 'local').lower()

    if backend == 'local':
        base_path = os.environ.get('STORAGE_LOCAL_PATH', 'uploads')
        base_url = os.environ.get('STORAGE_LOCAL_URL', '/uploads')
        _instance = LocalStorage(base_path=base_path, base_url=base_url)
        log.info('storage.init', backend='local', path=base_path)

    elif backend in ('s3', 'minio'):
        bucket = os.environ['AWS_S3_BUCKET']
        region = os.environ.get('AWS_REGION', 'eu-west-1')
        endpoint = os.environ.get('AWS_ENDPOINT_URL')  # MinIO
        public_url = os.environ.get('AWS_PUBLIC_BASE_URL')
        _instance = S3Storage(
            bucket=bucket,
            region=region,
            endpoint_url=endpoint,
            public_base_url=public_url,
        )
        log.info('storage.init', backend=backend, bucket=bucket)

    else:
        raise ValueError(f'STORAGE_BACKEND desconocido: {backend!r}. Usa "local", "s3" o "minio".')

    return _instance


def reset_storage():
    """Resetea el singleton. Útil en tests."""
    global _instance
    _instance = None
