"""No model downloads or real Ollama instance needed for these contract tests."""
from dataclasses import replace
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from src.vacation_planner.infrastructure.local_ai.Config import LocalAIConfig
from src.vacation_planner.infrastructure.local_ai.Runtime import LocalAIRuntime,api
from src.vacation_planner.infrastructure.local_ai.LocalModelClient import LocalModelClient
from src.vacation_planner.infrastructure.local_ai.Validation import validate_json


class LocalAIConfigTests(unittest.TestCase):
    def test_loopback_only_and_explicit_local_tag(self):
        for endpoint in ['https://example.org:11434','http://192.168.1.1:11434','http://localhost:11434','http://127.0.0.1:11434/x','http://x:y@127.0.0.1:11434','http://127.0.0.1:11434?x=y']:
            with self.subTest(endpoint=endpoint),self.assertRaises(ValueError):LocalAIConfig(endpoint=endpoint).validate()
        with self.assertRaises(ValueError):LocalAIConfig(model='qwen3:cloud').validate()
        self.assertEqual(LocalAIConfig().validate().parallel_requests,1)
        with self.assertRaises(ValueError):LocalAIConfig(parallel_requests=2).validate()

    def test_low_level_model_api_also_rejects_external_hosts(self):
        with self.assertRaises(ValueError):api('https://example.org','/api/chat',{'prompt':'nicht senden'})

    def test_persistent_config_is_not_silently_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            config=LocalAIConfig();config.save(folder)
            self.assertEqual(LocalAIConfig.load(folder),config)
            with self.assertRaises(FileExistsError):config.save(folder)
            (Path(folder)/'config.json').write_text('{"unknown":1}')
            with self.assertRaises(ValueError):LocalAIConfig.load(folder)

    def test_forged_or_stale_ownership_never_stops_foreign_process(self):
        with tempfile.TemporaryDirectory() as folder:
            runtime=LocalAIRuntime(folder)
            runtime.state.write_text(json.dumps(dict(pid=1,process_identity='wrong',endpoint=runtime.config.endpoint)))
            with patch('os.kill') as kill:
                with self.assertRaises(ValueError):runtime.stop()
                kill.assert_not_called()

    def test_schema_rejects_missing_extra_wrong_types_and_unsupported_rules(self):
        s=dict(type='object',properties=dict(adults=dict(type=['integer','null'],minimum=1)),required=['adults'],additionalProperties=False)
        self.assertEqual(validate_json({'adults':None},s),{'adults':None})
        for value in ({},{'adults':True},{'adults':'5'},{'adults':0},{'adults':5,'price':0}):
            with self.subTest(value=value),self.assertRaises(ValueError):validate_json(value,s)
        with self.assertRaises(ValueError):validate_json('x',{'pattern':'x'})


class LocalAITransportTests(unittest.TestCase):
    def setUp(self):
        state=self.state=dict(chat_delay=0,show_delay=0,show_status=200,remote=False,content='{"value":null}',done_reason='stop',calls=[],active=0,max_active=0)
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                body=json.loads(self.rfile.read(int(self.headers.get('Content-Length',0))))
                state['calls'].append((self.path,body))
                if self.path=='/api/show':
                    time.sleep(state['show_delay']);status=state['show_status'];data=dict(details=dict(format='gguf'),capabilities=['completion'])
                    if state['remote']:data['remote_host']='https://example.org'
                else:
                    state['active']+=1;state['max_active']=max(state['max_active'],state['active'])
                    time.sleep(state['chat_delay']);state['active']-=1
                    status=200;data=dict(message=dict(content=state['content']),done=True,done_reason=state['done_reason'])
                raw=json.dumps(data).encode()
                try:
                    self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
                except (BrokenPipeError,ConnectionResetError):pass
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.config=LocalAIConfig(endpoint='http://127.0.0.1:'+str(self.server.server_port),timeout_seconds=3)
        self.client=LocalModelClient(self.config);self.messages=[dict(role='user',content='Künstlicher Test')]
        self.schema=dict(type='object',properties=dict(value=dict(type=['integer','null'])),required=['value'],additionalProperties=False)
    def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join(2)

    def test_schema_and_bounded_parameters_are_sent_and_validated(self):
        response=self.client.chat(self.messages,self.schema)
        self.assertIsNone(response['parsed']['value'])
        request=self.state['calls'][-1][1]
        self.assertEqual(request['options']['num_ctx'],4096);self.assertFalse(request['stream']);self.assertNotIn('tools',request)
        self.assertEqual(request['messages'][0]['role'],'system');self.assertIn('Ausgabevertrag',request['messages'][0]['content'])
        self.assertEqual(len(self.messages),1)
        self.assertEqual(self.messages[0]['role'],'user')

    def test_missing_model_and_remote_model_are_rejected_before_generation(self):
        self.state['show_status']=404
        with self.assertRaisesRegex(ValueError,'Modell fehlt'):self.client.chat(self.messages)
        self.state.update(show_status=200,remote=True)
        with self.assertRaisesRegex(ValueError,'Cloud'):self.client.chat(self.messages)
        self.assertFalse(any(path=='/api/chat' for path,_ in self.state['calls']))

    def test_bad_structured_content_and_truncated_response_are_rejected(self):
        for text in ('kein JSON','{"value":"erfunden"}','{"value":null,"extra":1}'):
            self.state['content']=text
            with self.assertRaises(ValueError):self.client.chat(self.messages,self.schema)
        self.state.update(content='{"value":null}',done_reason='length')
        with self.assertRaisesRegex(ValueError,'abgeschnitten'):self.client.chat(self.messages,self.schema)

    def test_total_timeout_including_model_metadata(self):
        self.state['chat_delay']=.5
        began=time.monotonic()
        with self.assertRaises(TimeoutError):self.client.chat(self.messages,timeout=.15)
        self.assertLess(time.monotonic()-began,.6)
        self.state['show_delay']=.5
        with self.assertRaises(TimeoutError):self.client.chat(self.messages,timeout=.1)

    def test_running_request_is_cancellable_without_stopping_daemon(self):
        self.state['chat_delay']=1;cancel=threading.Event();errors=[]
        def call():
            try:self.client.chat(self.messages,cancel=cancel)
            except Exception as exc:errors.append(exc)
        thread=threading.Thread(target=call);thread.start();time.sleep(.15);cancel.set();thread.join(.4)
        self.assertFalse(thread.is_alive());self.assertIsInstance(errors[0],InterruptedError)
        self.state['chat_delay']=0
        self.assertTrue(self.client.chat(self.messages)['done'])

    def test_clients_share_one_request_slot_per_endpoint(self):
        self.state['chat_delay']=.15;errors=[]
        def call():
            try:LocalModelClient(self.config).chat(self.messages)
            except Exception as exc:errors.append(exc)
        threads=[threading.Thread(target=call) for _ in range(2)]
        for t in threads:t.start()
        for t in threads:t.join(2)
        self.assertFalse(errors);self.assertEqual(self.state['max_active'],1)

    def test_no_service_is_a_clear_error(self):
        config=replace(self.config,endpoint='http://127.0.0.1:1')
        with self.assertRaisesRegex(OSError,'nicht erreichbar'):LocalModelClient(config).chat(self.messages)

    def test_pre_cancel_and_oversized_input_never_generate(self):
        cancel=threading.Event();cancel.set()
        with self.assertRaises(InterruptedError):self.client.chat(self.messages,cancel=cancel)
        with self.assertRaisesRegex(ValueError,'Kontext'):self.client.chat([dict(role='user',content='x'*20000)])
        self.assertFalse(self.state['calls'])
