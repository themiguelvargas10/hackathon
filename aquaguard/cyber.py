"""Correlación temporal para revisión; nunca atribuye ataques."""
from datetime import datetime

def correlate(alerts):
    numeric = [a for a in alerts if a['numeric_alert']]
    events = []
    matched = set()
    for ot in (a for a in alerts if a['ot_alert']):
        related = [n for n in numeric if n['site'] == ot['site'] and
                   abs((datetime.fromisoformat(n['timestamp']) -
                        datetime.fromisoformat(ot['timestamp'])).total_seconds()) <= 3600]
        matched.update(n['id'] for n in related)
        events.append(dict(event_id=ot['id'], site=ot['site'], timestamp=ot['timestamp'],
                           status='combined_review' if related else 'ot_only',
                           reasons=ot['reasons'], related_ids=[n['id'] for n in related]))
    return dict(window_hours=1, scope='Solo alertas dentro de los filtros; mismo sitio; ±1 hora inclusive.',
                limitation='Coincidencia temporal, no causalidad ni confirmación de ataque.',
                events=events, combined=sum(e['status']=='combined_review' for e in events),
                ot_only=sum(e['status']=='ot_only' for e in events),
                operational_only_ids=[n['id'] for n in numeric if n['id'] not in matched])
