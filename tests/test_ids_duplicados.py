# -*- coding: utf-8 -*-
"""Regressão do StreamlitDuplicateElementId: a animação no campo é usada por
várias seções (RHIE em Esforços/WCS/Janelas; esforços em Individual/Por
Posição). Sem `key`, duas chamadas no mesmo run colidem e derrubam a página."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import viz.campo_anim as ca  # noqa: E402


class _FakeSt:
    """Captura as keys passadas a plotly_chart e simula o erro do Streamlit."""

    def __init__(self):
        self.keys = []
        self.session_state = {}

    def plotly_chart(self, fig, **kw):
        _k = kw.get('key')
        if _k in self.keys:                       # é o que o Streamlit faz
            raise RuntimeError('StreamlitDuplicateElementId')
        self.keys.append(_k)

    def info(self, *a, **k):
        pass


def _maps():
    return {'order': ['1T'], 'abs': {'1T': (1000.0, 4000.0)},
            'sorted_by_ts': ['1T'], 'start_min': {'1T': 0.0},
            'atl_offset': lambda _a: 0.0}


def _pos():
    _n = 900
    return {'1T': {'Atleta': {'xs': list(range(_n)), 'ys': [1] * _n,
                              'vel': [5.0] * _n}}}


def _anima(key=None):
    ca._animar_esforco_campo(
        ['Atleta'], 0.0, 1.0, _pos(), _maps(), 'ações',
        '00:00', '01:00', 3, '1T', campo_cfg={'fl': 105, 'fw': 68},
        min_atl=1, key=key)


def test_duas_secoes_com_keys_distintas_nao_colidem(monkeypatch):
    """O cenário do crash: RHIE renderizado em duas abas no mesmo run."""
    fake = _FakeSt()
    monkeypatch.setattr(ca, 'st', fake)
    _anima(key='esforcos_rhie_campo')
    _anima(key='janelas_rhie_campo')             # antes: DuplicateElementId
    assert fake.keys == ['esforcos_rhie_campo', 'janelas_rhie_campo']


def test_sem_key_explicita_deriva_key_do_conteudo(monkeypatch):
    fake = _FakeSt()
    monkeypatch.setattr(ca, 'st', fake)
    _anima()
    assert fake.keys and fake.keys[0].startswith('campoanim_')


def test_key_derivada_e_estavel_entre_reruns(monkeypatch):
    """Mesma entrada → mesma key (o gráfico não pisca a cada rerun)."""
    k = []
    for _ in range(2):
        fake = _FakeSt()
        monkeypatch.setattr(ca, 'st', fake)
        _anima()
        k.append(fake.keys[0])
    assert k[0] == k[1]


def test_conteudos_diferentes_geram_keys_diferentes(monkeypatch):
    fake = _FakeSt()
    monkeypatch.setattr(ca, 'st', fake)
    ca._animar_esforco_campo(['Atleta'], 0.0, 1.0, _pos(), _maps(), 'ações',
                             '00:00', '01:00', 3, '1T',
                             campo_cfg={'fl': 105, 'fw': 68}, min_atl=1)
    ca._animar_esforco_campo(['Atleta'], 0.0, 1.0, _pos(), _maps(), 'ações',
                             '05:00', '06:00', 7, '1T',
                             campo_cfg={'fl': 105, 'fw': 68}, min_atl=1)
    assert len(set(fake.keys)) == 2               # não colidem
