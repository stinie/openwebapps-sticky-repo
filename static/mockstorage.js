function MemoryStorage() {
  var self = {};
  self._storage = {};
  self._storageObjs = {};
  self.open = function (objType) {
    if (! (objType in self._storageObjs)) {
      self._storageObjs[objType] = MemoryStorage.ObjectStorage(self, objType);
    }
    return self._storageObjs[objType];
  };
  self.toString = function () {
    return 'MemoryStorage()';
  };
  EventMixin(self);
  return self;
}

MemoryStorage.ObjectStorage = function (storageObj, objType) {
  var self = {};
  self._storageObj = storageObj;
  self._storage = storageObj._storage;
  self._listeners = {};
  self._objType = objType;

  self.toString = function () {
    return "MemoryStorage().open('"+objType+"')";
  };

  self.get = function (key) {
    return self._storage[key];
  };

  self.put = function (key, value) {
    var canceled = ! self._storageObj.dispatchEvent('change', 
		         {eventType: 'change', storageType: self, 
                          target: key, value: value});
    if (! canceled) {
      self._storage[key] = value;
    }
  };

  self.remove = function (key) {
    var canceled = ! self._storageObj.dispatchEvent('delete', 
		         {eventType: 'delete', storageType: self, target: key});
    if (! canceled) {
      delete self._storage[key];
    }
  };

  self.has = function (key) {
    return key in self._storage;
  };

  self.keys = function () {
    var keys = [];
    for (var i in self._storage) {
      keys.push(i);
    }
    return keys;
  };

  self.iterate = function (callback) {
    var keys = self.keys();
    for (var i=0; i<keys.length; i++) {
      var result = callback(keys[i], self.get(keys[i]));
      if (result === false) {
        return;
      }
    }
  };

  return self;
};
