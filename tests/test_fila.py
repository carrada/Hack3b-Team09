"""Fila compartida: FIFO, capacidad por proveedor, caducidad de turnos abandonados y ajustes por sesión."""
import threading
import time
from contextvars import copy_context

from expediente import config, fila
from expediente.fila import Fila


def test_fifo_y_capacidad():
    f = Fila({"ollama": 1, "openai": 2})
    a, b, c = f.entrar("ollama"), f.entrar("ollama"), f.entrar("ollama")
    assert [f.posicion(x) for x in (a, b, c)] == [0, 1, 2]
    assert f.esperar(a, 0) and not f.esperar(b, 0)
    f.salir(a, completado=True)
    assert f.posicion(b) == 0 and f.posicion(c) == 1
    # la nube tiene su propia fila y capacidad
    n1, n2, n3 = f.entrar("openai"), f.entrar("openai"), f.entrar("openai")
    assert [f.posicion(x) for x in (n1, n2, n3)] == [0, 0, 1]
    assert f.estado("ollama") == {"en_curso": 1, "esperando": 1, "capacidad": 1}


def test_salir_de_la_espera_y_estimado():
    f = Fila({"ollama": 1})
    a, b, c = f.entrar("ollama"), f.entrar("ollama"), f.entrar("ollama")
    f.salir(b)  # se fue a la nube
    assert f.posicion(c) == 1
    assert f.espera_estimada(a) == 0
    assert f.espera_estimada(c) > 0


def test_turno_abandonado_caduca(monkeypatch):
    monkeypatch.setattr(fila, "LATIDO_MAX_S", 0.05)
    f = Fila({"ollama": 1})
    a, b, c = f.entrar("ollama"), f.entrar("ollama"), f.entrar("ollama")
    time.sleep(0.1)          # b deja de latir (pestaña cerrada); c sigue latiendo
    f.salir(a, completado=True)
    assert f.esperar(c, 0.5)  # c pasa sin quedar bloqueado detrás de b
    assert f.estado("ollama")["esperando"] == 0


def test_espera_bloqueante_despierta_al_liberar():
    f = Fila({"ollama": 1})
    a, b = f.entrar("ollama"), f.entrar("ollama")
    hilo = threading.Timer(0.1, lambda: f.salir(a, completado=True))
    hilo.start()
    t0 = time.monotonic()
    assert f.esperar(b, 2.0)
    assert time.monotonic() - t0 < 1.0


def test_ajustes_por_sesion_no_se_mezclan(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    vistos = {}

    def sesion(nombre, prov, modelo):
        config.fijar_ajustes(prov, modelo)
        with config.PoolConContexto(max_workers=2) as ex:  # los hilos internos heredan la sesión
            vistos[nombre] = ex.submit(lambda: (config.proveedor(), config.modelo())).result()

    hilos = [threading.Thread(target=copy_context().run, args=(sesion, "A", "ollama", "qwen2.5vl:3b")),
             threading.Thread(target=copy_context().run, args=(sesion, "B", "openai", None))]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    assert vistos["A"] == ("ollama", "qwen2.5vl:3b")
    assert vistos["B"] == ("openai", "gpt-4.1-mini") or vistos["B"][0] == "openai"
    assert config.proveedor() == "openai"  # el proceso no quedó contaminado
