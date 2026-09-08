from backend.app import create_app
from backend.local_models import LocalModels, ModelUnavailable, ModelBusy, choose_capability
from tests.test_auth import client, register
import pytest

class FakeModels:
    def __init__(self):self.calls=[];self.failure=None
    def close(self):pass
    def status(self):return [{'id':'fixture','name':'Test fixture','capability':'general','status':'installed'}]
    def generate(self,prompt):
        if self.failure:raise self.failure
        self.calls.append(prompt)
        capability,reason=choose_capability(prompt)
        return {'model_id':capability,'model_name':'Explicit test fixture','capability':capability,'routing_reason':reason,'answer':'Fixture answer, not model output','duration_ms':100,'finish_reason':'stop'}

@pytest.mark.parametrize('prompt,expected',[
 ('Draft an approval note for a review.','general'),
 ('Summarize the inspection findings below.','general'),
 ('Write a Python function converting Celsius to Fahrenheit.','coding'),
 ('Debug this JavaScript code.','coding'),
 ('Write SQL to group results.','coding')])
def test_routing(prompt,expected):assert choose_capability(prompt)[0]==expected

def test_generation_ownership_persistence_and_failure(tmp_path):
    engine=FakeModels();path=tmp_path/'db.sqlite3';app=create_app(path,engine)
    with client(app) as alice, client(app) as bob:
        register(alice);w=alice.post('/api/workspaces',json={'name':'AI'}).json()['id']
        register(bob,'bob')
        url=f'/api/workspaces/{w}/generations'
        assert bob.post(url,json={'prompt':'Private'}).status_code==404
        assert bob.get(url).status_code==404
        assert engine.calls==[]
        assert alice.post(url,json={'prompt':'   '}).status_code==422
        assert alice.post(url,json={'prompt':'Draft a note'},headers={'X-CSRF-Token':'bad'}).status_code==403
        result=alice.post(url,json={'prompt':'Draft a note'})
        assert result.status_code==201
        assert result.json()['capability']=='general'
        assert alice.get(url).json()['generations'][0]['answer']=='Fixture answer, not model output'
        engine.failure=ModelUnavailable('Not installed')
        assert alice.post(url,json={'prompt':'Retry'}).status_code==503
        engine.failure=ModelBusy('Busy')
        assert alice.post(url,json={'prompt':'Retry'}).status_code==429
        assert len(alice.get(url).json()['generations'])==1
    with client(create_app(path,engine)) as fresh:
        from tests.test_auth import PASSWORD
        fresh.post('/api/auth/login',json={'username':'alice','password':PASSWORD})
        assert len(fresh.get(url).json()['generations'])==1

def test_missing_models_no_fallback(tmp_path):
    engine=LocalModels(tmp_path)
    with pytest.raises(ModelUnavailable):engine.generate('Hello')
    assert engine.status()==[]

def test_single_generation_lock(tmp_path):
    engine=LocalModels(tmp_path);engine.lock.acquire()
    try:
        with pytest.raises(ModelBusy):engine.generate('Hello')
    finally:engine.lock.release()
