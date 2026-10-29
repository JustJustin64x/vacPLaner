"""One terminal outcome per examined destination; details may have several reasons."""
from collections import Counter
from datetime import datetime, timezone
from uuid import uuid4
import traceback


class SearchDiagnostics:
    def __init__(self, request):
        self.data = dict(search_id=str(uuid4()), started_at=datetime.now(timezone.utc).isoformat(),
                         criteria={k:v for k,v in request.to_dict().items() if k != 'address'},
                         counts=dict(catalog=0, geographic=0, locally_scored=0, examined=0,
                                     online_examined=0, with_lodgings=0, with_activities=0, with_known_transport=0,
                                     matches=0, ideas=0), outcomes=[], errors=[], stop_reason='')

    def outcome(self, destination, status, reasons=()):
        self.data['outcomes'].append(dict(id=destination.get('id',destination['name']),
                                         name=destination['name'], status=status, reasons=list(dict.fromkeys(reasons))))

    def error(self, stage, exc, address=''):
        # No locals or request objects in traceback; redact user address in messages.
        trace=''.join(traceback.format_exception(type(exc),exc,exc.__traceback__))
        if address: trace=trace.replace(address,'[Adresse entfernt]')
        self.data['errors'].append(dict(stage=stage, type=type(exc).__name__, traceback=trace))

    def finish(self, context, reason):
        self.data.update(stop_reason=reason, http_calls=context.calls,
                         finished_at=datetime.now(timezone.utc).isoformat())
        counts=Counter(o['reasons'][0] if o['reasons'] else o['status'] for o in self.data['outcomes'])
        self.data['primary_reasons']=dict(counts)
        c=self.data['counts']
        summary=f"{c['locally_scored']} Ziele lokal bewertet, {c['examined']} näher geprüft: {c['matches']} Filtertreffer, {c['ideas']} Ideen mit offenen Angaben. {reason}"
        if counts: summary+=' Hauptgründe (je Ziel genau einer): '+ '; '.join(f'{n} × {r}' for r,n in counts.items())+'.'
        if 'returned_results' in c:summary+=f" {c['returned_results']} Reisevorschläge ausgegeben; {len(self.data.get('grouped_alternatives',[]))} nahe Alternativen zusammengefasst."
        suggestions=[]
        all_reasons=' '.join(r for o in self.data['outcomes'] for r in o['reasons'])
        if 'Pflichtausstattung' in all_reasons: suggestions.append('Unbelegte Ausstattung als Wunsch statt Pflicht wählen.')
        if 'Reisezeit' in all_reasons: suggestions.append('Reisezeitlimit prüfen oder ein weiteres Verkehrsmittel aktivieren.')
        if 'Unterkunft' in all_reasons: suggestions.append('Umgebungssuche aktivieren oder Unterkunftstypen erweitern.')
        if self.data['errors']: suggestions.append('Quellenprobleme in der Diagnose prüfen; gegebenenfalls später erneut suchen.')
        if c.get('features_unknown'):suggestions.append('Fehlende regionale Interessenmerkmale können unter „Zieldaten einrichten“ ergänzt werden; unbekannt bedeutet nicht ungeeignet.')
        self.data['suggestions']=suggestions
        self.data['summary']=summary+' '+' '.join(suggestions)
        return self.data
