import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

import structlog
from structlog.processors import CallsiteParameter, CallsiteParameterAdder
from structlog.typing import EventDict
import settings


LOG_LEVEL = settings.LOG_LEVEL
LOG_ENVIRONMENT = settings.ENVIRONMENT
SERVICE_NAME = settings.SERVICE_NAME

# LOG_DIR: Si viene en env lo usamos, sino default relativo a este archivo
if settings.LOG_DIR_ENV:
    LOG_DIR = Path(settings.LOG_DIR_ENV)
else:
    LOG_DIR = Path(__file__).parent / "logs"

LOG_DIR.mkdir(parents=True, exist_ok=True)

_working_directory = len(os.getcwd()) + 1


class FileWriterProcessor:
    """Procesador que escribe logs al archivo además de consola"""
    def __init__(self, file_handler):
        self.file_handler = file_handler
    
    def __call__(self, logger, method_name, event_dict):
        # Escribir al archivo antes de retornar para consola
        log_line = self._format_for_file(event_dict)
        record = logging.LogRecord(
            name=event_dict.get('module', 'root'),
            level=self._get_level(event_dict.get('level', 'info')),
            pathname='',
            lineno=0,
            msg=log_line,
            args=(),
            exc_info=None
        )
        self.file_handler.emit(record)
        return event_dict
    
    def _format_for_file(self, event_dict):
        """Formatea el event_dict como string legible para archivo"""
        timestamp = event_dict.get('timestamp', '')
        level = event_dict.get('level', 'info').upper()
        event = event_dict.get('event', '')
        
        # Filtrar keys de metadata
        metadata_keys = {'timestamp', 'level', 'event', 'service', 'module', 'function', 'line'}
        extras = {k: v for k, v in event_dict.items() if k not in metadata_keys}
        
        parts = [f"{timestamp} [{level}]", event]
        
        if extras:
            extras_str = ' '.join([f"{k}={v}" for k, v in extras.items()])
            parts.append(extras_str)
        
        location = f"({event_dict.get('module', '?')}:{event_dict.get('function', '?')}:{event_dict.get('line', '?')})"
        parts.append(location)
        
        return ' | '.join(parts)
    
    def _get_level(self, level_str):
        levels = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.CRITICAL,
        }
        return levels.get(level_str.lower(), logging.INFO)


def add_service_name(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    """Add service name to all logs"""
    event_dict['service'] = SERVICE_NAME
    return event_dict


def rename_callsite_keys(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    """Rename callsite parameters to shorter names"""
    if 'pathname' in event_dict:
        event_dict['module'] = event_dict.pop('pathname')[_working_directory:]
    if 'func_name' in event_dict:
        event_dict['function'] = event_dict.pop('func_name')
    if 'lineno' in event_dict:
        event_dict['line'] = event_dict.pop('lineno')
    return event_dict


def get_daily_log_filename():
    """Genera el nombre del archivo de log con fecha actual"""
    return LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d')}_runtime.log"


def configure_logger():
    """
    Configura structlog para:
    - Logging estructurado automático con contextvars
    - Información de módulo/función/línea automática
    - Colores consistentes: cyan para keys, colores por nivel para values
    - Rotación diaria de archivos (nuevo archivo cada día a medianoche)
    """
    
    # Mapeo de niveles
    name_to_level = {
        'CRITICAL': logging.CRITICAL,
        'ERROR': logging.ERROR,
        'WARNING': logging.WARNING,
        'INFO': logging.INFO,
        'DEBUG': logging.DEBUG,
    }
    
    logging_level = name_to_level.get(LOG_LEVEL.upper(), logging.INFO)
    
    # Configure root logger para APScheduler
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)
    root_logger.handlers.clear()
    
    # Rotacion diaria
    file_handler = TimedRotatingFileHandler(
        filename=get_daily_log_filename(),
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    file_handler.setLevel(logging_level)
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setFormatter(logging.Formatter('%(message)s'))
    
    # Además de escribir al archivo, añadir handler a stdout para que
    # `docker logs` capture también todas las entradas.
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging_level)
    stream_handler.setFormatter(logging.Formatter('%(message)s'))

    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)
    
    # Procesadores comunes
    shared_processors = [
        add_service_name,
        CallsiteParameterAdder(
            parameters=[
                CallsiteParameter.PATHNAME,
                CallsiteParameter.FUNC_NAME,
                CallsiteParameter.LINENO,
            ]
        ),
        rename_callsite_keys,
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt='iso', utc=(LOG_ENVIRONMENT == 'prod')),
        FileWriterProcessor(file_handler),  # Escribe al archivo
    ]
    
    if LOG_ENVIRONMENT == 'prod':
        import orjson
        
        structlog.configure(
            processors=shared_processors + [
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(serializer=orjson.dumps),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(logging_level),
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        structlog.configure(
            processors=shared_processors + [
                structlog.dev.ConsoleRenderer(
                    colors=True,
                    exception_formatter=structlog.dev.plain_traceback,
                ),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(logging_level),
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
    
    logger = structlog.get_logger()
    logger.info("logger_configured", environment=LOG_ENVIRONMENT, log_level=LOG_LEVEL)
    
    return logger


# Instancia global
app_logger = configure_logger()
