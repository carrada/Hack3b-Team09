"""Fila de análisis compartida entre todas las sesiones del proceso (FIFO por proveedor).

Por qué: Ollama atiende UNA petición a la vez en una GPU chica. Si dos análisis se intercalan, cada cambio de
usuario obliga al modelo a reprocesar el contexto y ambos tardan ~3x (medido: 98 s solo vs 326 s cada uno con 2 a la
vez). En fila, el primero termina a los ~98 s y el segundo a los ~196 s.

- `capacidad` = análisis simultáneos por proveedor (ollama=1 en una GPU de 4 GB; la nube aguanta varios).
- Los turnos en espera envían un latido; si una sesión se cierra (pestaña cerrada) su turno caduca solo y no
  bloquea a los demás.
- El historial de duraciones alimenta el tiempo estimado de espera.
"""
from __future__ import annotations

import itertools
import threading
import time
from collections import deque
from dataclasses import dataclass, field

LATIDO_MAX_S = 20          # sin latido por más de esto, un turno en espera se descarta
DURACION_DEFECTO_S = 120   # estimado mientras no haya historial


@dataclass(eq=False)  # identidad, no igualdad de campos
class Turno:
    id: int
    proveedor: str
    llegada: float = field(default_factory=time.monotonic)
    latido: float = field(default_factory=time.monotonic)
    inicio: float | None = None   # cuándo obtuvo lugar (None = sigue esperando)


class Fila:
    def __init__(self, capacidad: dict[str, int]):
        self.capacidad = capacidad
        self._cond = threading.Condition()
        self._esperando: dict[str, list[Turno]] = {}
        self._activos: dict[str, list[Turno]] = {}
        self._historial: dict[str, deque] = {}
        self._ids = itertools.count(1)

    # ------------------------------------------------------------ internos (con el candado tomado)
    def _cap(self, prov: str) -> int:
        return max(1, self.capacidad.get(prov, 1))

    def _purgar(self, prov: str) -> None:
        ahora = time.monotonic()
        cola = self._esperando.get(prov, [])
        vivos = [t for t in cola if ahora - t.latido <= LATIDO_MAX_S]
        if len(vivos) != len(cola):
            self._esperando[prov] = vivos
            self._cond.notify_all()

    def _promover(self, prov: str) -> None:
        self._purgar(prov)  # nunca darle lugar a un turno abandonado
        cola, activos = self._esperando.setdefault(prov, []), self._activos.setdefault(prov, [])
        while cola and len(activos) < self._cap(prov):
            t = cola.pop(0)
            t.inicio = time.monotonic()
            activos.append(t)
            self._cond.notify_all()

    # ------------------------------------------------------------ API
    def entrar(self, prov: str) -> Turno:
        with self._cond:
            t = Turno(id=next(self._ids), proveedor=prov)
            self._esperando.setdefault(prov, []).append(t)
            self._purgar(prov)
            self._promover(prov)
            return t

    def esperar(self, t: Turno, timeout: float = 1.0) -> bool:
        """True cuando el turno ya tiene lugar. Cada llamada cuenta como latido."""
        with self._cond:
            fin = time.monotonic() + timeout
            while True:
                t.latido = time.monotonic()
                if t.inicio is None and t not in self._esperando.get(t.proveedor, []):
                    # caducó (p. ej. la sesión estuvo congelada): vuelve a formarse al final
                    t.llegada = time.monotonic()
                    self._esperando.setdefault(t.proveedor, []).append(t)
                self._purgar(t.proveedor)
                self._promover(t.proveedor)
                if t.inicio is not None:
                    return True
                restante = fin - time.monotonic()
                if restante <= 0:
                    return False
                self._cond.wait(restante)

    def salir(self, t: Turno, completado: bool = False) -> None:
        with self._cond:
            prov = t.proveedor
            if t in self._activos.get(prov, []):
                self._activos[prov].remove(t)
                if completado and t.inicio is not None:
                    self._historial.setdefault(prov, deque(maxlen=10)).append(time.monotonic() - t.inicio)
            elif t in self._esperando.get(prov, []):
                self._esperando[prov].remove(t)
            self._promover(prov)
            self._cond.notify_all()

    def posicion(self, t: Turno) -> int:
        """0 = ya tiene lugar; 1 = es el siguiente; …"""
        with self._cond:
            if t.inicio is not None:
                return 0
            cola = self._esperando.get(t.proveedor, [])
            return cola.index(t) + 1 if t in cola else len(cola) + 1

    def duracion_promedio(self, prov: str) -> float:
        with self._cond:
            h = self._historial.get(prov)
            return sum(h) / len(h) if h else DURACION_DEFECTO_S

    def espera_estimada(self, t: Turno) -> float:
        pos = self.posicion(t)
        if pos == 0:
            return 0.0
        prom = self.duracion_promedio(t.proveedor)
        with self._cond:
            cap = self._cap(t.proveedor)
            ahora = time.monotonic()
            restantes = sorted(max(prom - (ahora - a.inicio), 5.0) for a in self._activos.get(t.proveedor, []))
        # se libera un lugar cuando acaba el activo más próximo; después, una "ola" de `cap` análisis por promedio
        primero = restantes[0] if len(restantes) >= cap else 0.0
        return primero + ((pos - 1) // cap) * prom

    def estado(self, prov: str) -> dict:
        with self._cond:
            self._purgar(prov)
            return {"en_curso": len(self._activos.get(prov, [])), "esperando": len(self._esperando.get(prov, [])),
                    "capacidad": self._cap(prov)}
