"""Explicit local free-text extraction. No persistence, logging or lifecycle."""
import threading
from ...core.planning.SearchRequest import today
from ...core.planning.TravelWishes import analyse_text, model_messages, model_schema, verify_proposals
from .LocalModelClient import LocalModelClient
from .Validation import validate_json


class WishService:
    def __init__(self,client=None):self.client=client

    def evaluate(self,text,cancel=None,current_date=None):
        cancel=cancel or threading.Event();current_date=current_date or today()
        ledger=analyse_text(text,current_date)
        if cancel.is_set():raise InterruptedError('Wunschauswertung abgebrochen.')
        if any(i['kind']=='ambiguous' for i in ledger['issues']):
            return dict(verify_proposals(dict(proposals=[]),text,ledger),client_seconds=None,mode='clarification_without_model')
        client=self.client or LocalModelClient()
        # Do not supply candidate answers or any existing form values to model.
        response=client.chat(model_messages(text,current_date),schema=model_schema(),cancel=cancel)
        if cancel.is_set():raise InterruptedError('Wunschauswertung abgebrochen.')
        parsed=validate_json(response['parsed'],model_schema())
        return dict(verify_proposals(parsed,text,ledger),client_seconds=response.get('client_seconds'))
