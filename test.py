
import cPickle
import numpy as np
import redis

from pscache import client
from pscache import publisher


class TestExptClient(object):

    # put some fake data into a local redis db
    # test all fxns in client

    def setup(self):

        self._redis = redis.StrictRedis(host='localhost', port=6379, db=0)


        self.shape = (1,)
        self.type  = 'i8'
        info = '%s-%s' % (str(self.shape), self.type)

        # create instances of the 3 types of keys
        self._redis.sadd('runs', 47)
        self._redis.hset('run47:keys', 'data', info) 
        for i in range(100):
            self._redis.rpush('run47:data', cPickle.dumps(i))

        self.client = client.ExptClient('testexpt', host='localhost')
        
        return


    def test_runs(self):
        r = self.client.runs()
        assert type(r) == set
        assert '47' in r

    def test_keys(self):
        ks = self.client.keys(47)
        assert type(ks) == list
        assert 'data' in ks

    def test_keyinfo(self):
        ki = self.client.keyinfo(47)
        assert type(ki) == dict
        assert 'data' in ki.keys()
        assert ki['data'][0] == self.shape
        assert ki['data'][1] == self.type

    def test_fetch_data(self):
        d = self.client.fetch_data(47, keys=['data'], max_events=50, fmt='list')
        assert type(d) == dict
        assert 'data' in d.keys()
        assert np.all(d['data'] == np.arange(50))
        assert d['data'].dtype == np.dtype(self.type)

    def teardown(self):
        self._redis.delete('runs', 'run47:keyinfo', 'run47:data')


class TestExptPublisher(object):
    
    def setup(self):
        self._redis = redis.StrictRedis(host='localhost', port=6379, db=0)
        self.pub = publisher.ExptPublisher('testexpt', host='localhost')
        return
        
        
    def test_send_data(self):
        
        run  = 47
        key  = 'data'
        data = np.arange(50)
        self.pub._send_data(run, key, data, event_limit=-1)
        
        ret_data = self._redis.lrange('run%d:data' % run, 0, -1)
        assert [cPickle.loads(x) for x in ret_data] == range(50)
        
        keyinfo = self._redis.hgetall('run%d:keyinfo' % run)
        assert keyinfo['data'] == '(1,)-<i8'
        
        return
        
        
    def test_send_smalldata_dict(self):
        
        smd_dict = {'data' : np.arange(50)}
        run = 47
        self.pub.send_dict(smd_dict, run)
        
        ret_data = self._redis.lrange('run%d:data' % run, 0, -1)
        assert [cPickle.loads(x) for x in ret_data] == range(50)
        
        keyinfo = self._redis.hgetall('run%d:keyinfo' % run)
        assert keyinfo['data'] == '(1,)-<i8'
        
        return
        
        
    def test_smalldata_monitor(self):
        
        run = 9999 # TODO
        mon = self.pub.smalldata_monitor()
        
        smd_dict = {'data' : np.arange(50)}
        mon(smd_dict)
        
        ret_data = self._redis.lrange('run%d:data' % run, 0, -1)
        r = [cPickle.loads(x) for x in ret_data]
        assert r == range(50)
        
        keyinfo = self._redis.hgetall('run%d:keyinfo' % run)
        assert keyinfo['data'] == '(1,)-<i8'
        
        return
    

    def teardown(self):
        self._redis.delete('runs', 'run47:keyinfo', 'run47:data',
                           'run9999:keyinfo', 'run9999:data')

