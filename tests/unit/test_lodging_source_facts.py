import unittest
from src.vacation_planner.core.planning.ChildAgeRange import ChildAgeRange
from src.vacation_planner.infrastructure.planning.Beds24QuoteEvidence import inventory_evidence,apply_room_evidence
from src.vacation_planner.infrastructure.planning.Beds24ResponsiveQuote import Beds24ResponsiveQuote
from src.vacation_planner.core.planning.TravelOffers import OfferQuery
from src.vacation_planner.infrastructure.planning.TripStore import timestamp
from tests.unit.test_responsive_lodging import fixture
from tests.unit.test_general_lodging import item

class LodgingSourceFactsTests(unittest.TestCase):
 def test_live_observed_english_age_label_has_exact_boundaries(self):
  p=ChildAgeRange.parse('Children ages 4 to 12');self.assertEqual((p.minimum,p.maximum),(4,12))
  self.assertTrue(p.accepts([4,6,12]));self.assertFalse(p.accepts([3]));self.assertFalse(p.accepts([13]))
  self.assertIsNone(ChildAgeRange.parse('Children ages 4 to 12 except weekends'))
 def test_affirmative_features_are_room_scoped_and_rate_exclusions_conflict(self):
  html='<div class="b24-featurewell"><p><span class="glyphicon-ok"></span>Private Bathroom</p></div><div id="roomid718"><div class="b24-featurewell"><p><span class="glyphicon-ok"></span>Breakfast Included</p></div><div id="ajaxroomoffer1-718">Breakfast not included</div></div>'
  evidence=inventory_evidence(html,'718','1','2090-05-10');self.assertNotIn('Frühstück',evidence['facts']);self.assertNotIn('Eigenes Bad',evidence['facts'])
  evidence=inventory_evidence(html.replace('Breakfast not included','Flexible'),'718','1','2090-05-10');self.assertTrue(evidence['facts']['Frühstück'])
 def test_badge_without_affirmative_marker_and_conflicting_bathroom_stay_unknown(self):
  for labels in [['Private Bathroom'],['Private Bathroom','Shared Bathroom']]:
   ticks='' if len(labels)==1 else '<i class="glyphicon-ok"></i>'
   html='<div id="roomid718"><div class="b24-featurewell">'+''.join('<p>'+ticks+x+'</p>' for x in labels)+'</div></div>'
   self.assertNotIn('Eigenes Bad',inventory_evidence(html,'718','1','2090-05-10')['facts'])
 def test_room_evidence_does_not_fill_unknown_mandatory_fees(self):
  q=OfferQuery('Berlin','Town','2090-05-10','2090-05-14',2,1)
  o=Beds24ResponsiveQuote.parse(fixture(q,{'718':(1,2)}),q,item(),{'718':(1,2)},timestamp(),'https://beds24.com/',{'propid':'876543'})
  apply_room_evidence(o,[dict(facts={'Frühstück':True},proof={'Frühstück':'Breakfast Included'})])
  self.assertTrue(o.details['property']['amenities']['Frühstück']);self.assertFalse(o.evidence['fees_complete']);self.assertTrue(o.unresolved)

if __name__=='__main__':unittest.main()
