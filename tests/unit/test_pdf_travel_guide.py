import copy
import tempfile
import unittest
from pathlib import Path

from pypdf import PdfReader

from src.vacation_planner.infrastructure.planning.PdfTripPresenter import PdfTripPresenter
from src.vacation_planner.infrastructure.planning.TripPdfExporter import TripPdfExporter
from src.vacation_planner.infrastructure.planning.TripEnrichmentService import TripEnrichmentService
from src.vacation_planner.core.planning.SearchContext import SearchContext
from src.vacation_planner.infrastructure.planning.TripStore import TripStore
from tests.unit.test_surprise_planning import fixture_trip


class PdfTravelGuideTests(unittest.TestCase):
    def test_completeness_and_cost_labels(self):
        trip=fixture_trip();model=PdfTripPresenter.present(trip)
        self.assertFalse(model['complete']);self.assertEqual(model['cost']['title'],'Bekannte Kosten')
        self.assertIn('Unterkunftspreis ist nicht geprüft',model['issues'])
        empty=copy.deepcopy(trip);empty['lodgings']=[];empty['cost_summary']={'coverage':0,'missing':['Unterkunft']}
        self.assertIn('Keine Unterkunft vorhanden',PdfTripPresenter.completeness(empty).issues)

    def test_selection_order_three_lodgings_eight_activities_and_deduped_links(self):
        trip=fixture_trip();trip['selected_lodging']=2
        trip['activities']=(trip['activities']*2)[:12]
        model=PdfTripPresenter.present(trip)
        self.assertEqual(model['lodgings'][0]['name'],trip['lodgings'][2]['name'])
        self.assertEqual(len(model['lodgings']),3);self.assertEqual(len(model['activities']),8)
        self.assertEqual(len({x['url'] for x in model['sources']}),len(model['sources']))

    def test_group_and_person_cost_are_consistent(self):
        trip=fixture_trip();trip['request']['adults']=5
        trip['cost_summary']={'coverage':1,'low':'500.00','high':'600.00','missing':[],'status':'Schätzspanne'}
        model=PdfTripPresenter.present(trip)
        self.assertEqual(model['cost']['group'],'500,00 € bis 600,00 €')
        self.assertEqual(model['cost']['per_person'],'100,00 € bis 120,00 €')

    def test_single_multi_and_old_snapshot_export(self):
        trip=fixture_trip();second=copy.deepcopy(trip);second['id']='zweite';second['destination']=dict(second['destination'],name='Hřensko – České Švýcarsko')
        with tempfile.TemporaryDirectory() as folder:
            single=Path(folder)/'single.pdf';multi=Path(folder)/'multi.pdf'
            TripPdfExporter().export_trips(single,[trip]);TripPdfExporter().export_trips(multi,[second,trip])
            single_text='\n'.join(x.extract_text() for x in PdfReader(single).pages)
            multi_reader=PdfReader(multi);multi_text='\n'.join(x.extract_text() for x in multi_reader.pages)
            self.assertIn('Übersichtskarte',single_text);self.assertIn('Reisen vergleichen',multi_text)
            self.assertLess(multi_text.index('Hřensko'),multi_text.index('Bled'))
            self.assertTrue(multi_reader.outline)

    def test_exact_image_offline_and_broken_response_do_not_mutate_original(self):
        class OfflineHttp:
            def get(self,*args):raise OSError('offline')
            def json(self,*args):raise OSError('offline')
        with tempfile.TemporaryDirectory() as folder:
            store=TripStore(Path(folder)/'db.sqlite3');trip=fixture_trip();before=copy.deepcopy(trip)
            result=TripEnrichmentService(store,OfflineHttp()).enrich(trip,SearchContext(seconds=2,budget=2))
            self.assertEqual(trip,before);self.assertNotIn('image',result['destination']);self.assertIn('enriched_at',result)

    def test_map_markers_only_use_known_coordinates(self):
        trip=fixture_trip();trip['activities'][0]['latitude']=None;trip['activities'][0]['longitude']=None
        model=PdfTripPresenter.present(trip)
        self.assertNotIn(trip['activities'][0]['name'],[x['name'] for x in model['map_points']])


if __name__=='__main__':unittest.main()
