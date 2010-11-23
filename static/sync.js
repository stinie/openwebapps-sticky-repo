function Sync(options) {
  var obj = {};
  // FIXME: default?
  obj.url = options.url;
  if (obj.url.search(/\/$/) != -1) {
    obj.url = obj.url.substr(0, obj.url.length-1);
  }
  obj.addHeaders = options.addHeaders;
  obj.defaultError = options.error;
  obj.defautBeforeSend = options.beforeSend;

  obj.clear = function (options) {
    ajax({
      url: userUrl(),
      type: 'DELETE',
      success: function (result) {
        options.success();
      },
      error: options.error
    });
  };

  obj.lastUpdated = function (options) {
    ajax({
      url: userUrl() + '/last_updated',
      success: function (result) {
        // FIXME: proper parsing:
        var value = new Date(result.date);
        options.success(value);
      },
      error: options.error
    });
  };

  obj.fetchUpdates = function (options) {
    var args = {
      url: userUrl() + '?since=' + since,
      addHeaders: {'If-Modified-Since': since.toGMTString()},
      dataType: 'json',
      success: function (result) {
        options.success(result);
      },
      error: options.error
    };
    if (options.since) {
      args.addHeaders = {'If-Modified-Since': options.since.toGMTString()};
    }
    ajax(args);
  };

  obj.pushManifests = function (options) {
    ajax({
      url: userUrl(),
      type: 'POST',
      data: JSON.stringify(options),
      addHeaders: {'Content-Type': 'application/json'},
      dataType: 'json',
      success: function (result) {
        options.success(result);
      },
      error: options.error
    });
  };

  obj.isLoggedIn = function (options) {
    ajax({
      url: obj.url + '/login-status',
      dataType: 'json',
      success: function (result) {
        // In the future, this should be replaced with a simple cookie check
        options.success(result.displayName ? true : false);
      },
      error: options.error
    });
  };

  obj.loginStatus = function (options) {
    ajax({
      url: obj.url + '/login-status',
      dataType: 'json',
      success: function (result) {
        options.success(result);
      },
      error: options.error
    });
  };

  var ajax = function (options) {
    options.error = options.error || obj.defaultError;
    if (options.addHeaders) {
      var headers = mergeObjects(options.addHeaders, obj.addHeaders);
    } else {
      var headers = obj.addHeaders;
    }
    var oldBeforeSend = options.beforeSend || obj.defaultBeforeSend;
    options.beforeSend = function (req) {
      req.url = options.url;
      req.method = options.type || 'GET';
      console.log(req, req.url);
      for (var header in headers) {
        req.setRequestHeader(header, headers[header]);
      }
      if (oldBeforeSend) {
        oldBeforeSend(req);
      }
    };
    $.ajax(options);
  };

  var userUrl = function () {
    return obj.url + '/data/{' + obj.user + '}';
  };

  var mergeObjects = function (ob1, ob2) {
    var newObject = {};
    for (var i in ob1) {
      newObject[i] = ob1[i];
    }
    for (i in ob2) {
      newObject[i] = ob2[i];
    }
    return newObject;
  };

  // FIXME: read a cookie or something
  obj.user = options.forceUser || 'test';

  return obj;
}
