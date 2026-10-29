from ...core.planning.TravelOffers import OfferResult


class FlightAccessDiagnostics:
    """Explicit unresolved access report, deliberately not a functioning flight adapter."""
    name='Flugquellen · Zugangsdiagnose';category='flight'

    def search(self,query,trip,context):
        context.check()
        return OfferResult(self.name,self.category,'access_missing',query.to_dict(),message=(
            'Flugpreisabruf weiterhin offen: Norwegian und Transavia verweigerten den Zugriff (HTTP 403); '
            'easyJet untersagt automatisierte Extraktion, Ryanair sperrt Such-/API-Pfade in robots.txt. '
            'Amadeus-Produktion berechnet Überschreitungen automatisch; Aviasales Search verlangt 50.000 aktive Nutzer/Monat. '
            'Kein belegter kostenlos nutzbarer Zugang zu aktuellen Gruppenpreisen integriert. Manuelle Prüfung im Browser möglich; andere Kategorien laufen weiter.'),sources=[
            'https://www.norwegian.com/en/','https://www.transavia.com/home/en-eu',
            'https://www.easyjet.com/en/help-centre/policy-terms-and-conditions/acceptable-use-policy',
            'https://www.ryanair.com/robots.txt',
            'https://support.travelpayouts.com/hc/en-us/articles/210995808-How-to-get-access-to-the-Aviasales-Search-API',
            'https://admin.developers.amadeus.com/self-service/apis-docs/guides/developer-guides/faq/'])
