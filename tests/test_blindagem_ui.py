# -*- coding: utf-8 -*-
"""Blindagem global contra StreamlitDuplicateElementId nos gráficos."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ui_theme  # noqa: E402


class _St:
    def __init__(self):
        self.session_state = {}
        self.usadas = []

    def plotly_chart(self, fig, **kw):
        _k = kw.get('key')
        if _k in self.usadas:
            raise RuntimeError('StreamlitDuplicateElementId')
        self.usadas.append(_k)


def _preparar(monkeypatch):
    fake = _St()
    monkeypatch.setattr(ui_theme, '_st_bl', fake)
    ui_theme.blindar_elementos_duplicados()
    ui_theme.preparar_run()
    return fake


def test_dois_graficos_iguais_nao_colidem(monkeypatch):
    """O crash real: mesma figura renderizada 2x no mesmo run."""
    fake = _preparar(monkeypatch)
    fig = {'igual': True}
    fake.plotly_chart(fig, use_container_width=True)
    fake.plotly_chart(fig, use_container_width=True)   # antes: derrubava a página
    assert len(set(fake.usadas)) == 2


def test_respeita_key_explicita(monkeypatch):
    fake = _preparar(monkeypatch)
    fake.plotly_chart({}, key='minha_key')
    assert fake.usadas == ['minha_key']


def test_contador_zera_a_cada_run(monkeypatch):
    """Chaves estáveis entre runs: o 1º gráfico é sempre _pltauto_1."""
    fake = _preparar(monkeypatch)
    fake.plotly_chart({})
    _primeira = fake.usadas[0]
    ui_theme.preparar_run()
    fake.usadas.clear()
    fake.plotly_chart({})
    assert fake.usadas[0] == _primeira


def test_blindagem_e_idempotente(monkeypatch):
    """Aplicar 2x não empilha wrappers (o app chama a cada run)."""
    fake = _preparar(monkeypatch)
    _f1 = fake.plotly_chart
    ui_theme.blindar_elementos_duplicados()
    assert fake.plotly_chart is _f1
