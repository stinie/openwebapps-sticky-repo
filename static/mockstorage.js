function MemoryStorage() {
  var self = {};
  self._storage = {};
  self.open = function (objType) {
    return MemoryStorage.ObjectStorage(self._storage, objType);
  };
  return self;
}

MemoryStorage.ObjectStorage = function (storage, objType) {
  var self = {};
  self._storage = storage;
  self._listeners = {};

  self.get = function (key) {
    return self._storage[key];
  };

  self.put = function (key, value) {
    var canceled = ! self.dispatchEvent('change', {target: key});
    self._storage[key] = value;
  };

  self.remove = function (key) {
    var canceled = ! self.dispatchEvent('delete', {target: key});
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

  self.addEventListener = function (event, callback) {
    if (! event in self._listeners) {
      self._listeners[event] = [];
    }
    self._listeners.push(callback);
  };

  self.removeEventListener = function (event, callback) {
    if (! event in self._listeners) {
      return;
    }
    for (var i=0; i<self._listeners[event].length; i++) {
      if (self._listeners[event][i] === callback) {
        self._listeners.splice(i, 1);
        return;
      }
    }
  };

  self.dispatchEvent = function (name, event) {
    // FIXME: This isn't quite right...
    if (! name in self._listeners) {
      return true;
    }
    var result = true;
    for (var i=0; i<self._listeners.length; i++) {
      if (self._listeners[i](event) === false) {
        result = false;
      }
    }
    return result;
  };

  return self;
};
