"""Real Tk editor and ordinary request/snapshot path; no public price claims."""
import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from src.vacation_planner.entrypoints.gui.SurprisePlannerApplication import SurprisePlannerApplication
from src.vacation_planner.infrastructure.planning.TripStore import TripStore
from tests.unit.test_surprise_planning import FixtureProvider,fixture_trip

@unittest.skipIf(tk.TkVersion<8.6,'Modern Tk required')
class RoomPartyDesktopTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.store=TripStore(Path(self.temp.name)/'trips.db')
        self.app=SurprisePlannerApplication(self.store,FixtureProvider());self.root=self.app.create_window();self.root.withdraw()
    def tearDown(self):
        self.app.close();self.temp.cleanup()
    def test_editor_form_save_reload_and_old_format(self):
        app=self.app;t=fixture_trip();app.populate_request(t['request'])
        app.vars['adults'].set('3');app.vars['rooms'].set('2');app.vars['children_ages'].set('5, 9')
        app.edit_room_assignments();editor=app.room_assignment_window;editor.window.withdraw()
        for (adult,child),n,ages in zip(editor.entries,[2,1],['5','9']):adult.set(str(n));child.set(ages)
        editor.save();request=app.read_request()
        self.assertEqual(request.room_occupancy(),[3,2]);self.assertEqual(request.children_ages,[5,9])
        t['request']=request.to_dict();saved=self.store.save('Family',t);loaded=self.store.load(saved)
        app.populate_request(loaded['request']);self.assertEqual(app.read_request().to_dict(),request.to_dict())
        old=dict(t['request']);old.pop('children_ages');old.pop('room_assignments')
        app.populate_request(old);self.assertEqual(app.read_request().children_ages,[]);self.assertEqual(app.room_assignments,[])
    def test_changed_group_cannot_reuse_stale_explicit_rooms(self):
        app=self.app;app.vars['adults'].set('2');app.vars['rooms'].set('1')
        app.set_room_assignments([dict(adults=2,children_ages=[])])
        app.vars['children_ages'].set('7')
        with self.assertRaises(ValueError):app.read_request()
        app.set_room_assignments([]);self.assertEqual(app.read_request().persons,3)

    def test_source_support_uses_selected_property_for_any_destination(self):
        from unittest.mock import patch
        from tests.unit.test_general_lodging import item
        self.app.active=fixture_trip();self.app.active['destination']['name']='Any new destination';self.app.active['lodgings']=[item()];self.app.active['selected_lodging']=0
        self.app.price_category.set('Unterkunft')
        with patch('webbrowser.open') as opened:self.app.support_source();opened.assert_called_once_with(item()['url'])

if __name__=='__main__':unittest.main()
