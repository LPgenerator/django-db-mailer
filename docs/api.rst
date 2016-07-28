.. _api:

API
===

Objective-C example
-------------------

.. code-block:: objective-c

    NSURL *url = [NSURL URLWithString:@"http://127.0.0.1:8000/dbmail/api/"];
    NSString *postString = @"api_key=ZzriUzE&slug=welcome&recipient=root@local.host";
    NSData *returnData = [[NSData alloc]init];

    NSMutableURLRequest *request = [[NSMutableURLRequest alloc] initWithURL:url];
    [request setHTTPMethod:@"POST"];
    [request setValue:[NSString stringWithFormat:@"%lu", (unsigned long)[postString length]] forHTTPHeaderField:@"Content-length"];
    [request setHTTPBody:[postString dataUsingEncoding:NSUTF8StringEncoding]];
    returnData = [NSURLConnection sendSynchronousRequest: request returningResponse: nil error: nil];

    NSString *response = [[NSString alloc] initWithBytes:[returnData bytes] length:[returnData length] encoding:NSUTF8StringEncoding];
    NSLog(@"Response >>>> %@",response);


Java example
------------

.. code-block:: java

    httpClient client = new DefaultHttpClient();
    HttpPost post = new HttpPost("http://127.0.0.1:8000/dbmail/api/");

    List<NameValuePair> pairs = new ArrayList<NameValuePair>();
    pairs.add(new BasicNameValuePair("api_key", "ZzriUzE"));
    pairs.add(new BasicNameValuePair("slug", "welcome"));
    pairs.add(new BasicNameValuePair("recipient", "root@local.host"));
    post.setEntity(new UrlEncodedFormEntity(pairs));

    client.execute(post);


Python example
--------------

.. code-block:: python

    from httplib import HTTPConnection
    from urlparse import urlparse
    from urllib import urlencode

    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        "User-Agent": "DBMail Cli",
    }

    data = {
        "api_key": "ZzriUzE",
        "slug": "welcome",
        "recipient": "root@local.host"
    }

    uri = urlparse("http://127.0.0.1:8000/dbmail/api/")

    http = HTTPConnection(uri.netloc)
    http.request(
        "POST", uri.path,
        headers=headers,
        body=urlencode(data)
    )
    print http.getresponse().read()



Go example
----------

.. code-block:: go

    package main

    import (
        "net/http"
        "net/url"
        "bytes"
        "fmt"
    )

    func main() {
        uri := "http://127.0.0.1:8000/dbmail/api/"

        data := url.Values{}
        data.Add("api_key", "ZzriUzE")
        data.Add("slug", "welcome")
        data.Add("recipient", "root@local.host")

        client := &http.Client{}
        r, _ := http.NewRequest("POST", uri, bytes.NewBufferString(data.Encode()))
        r.Header.Set("Content-Type", "application/x-www-form-urlencoded")
        resp, _ := client.Do(r)
        fmt.Println(resp.Body)
    }


PHP example
-----------

.. code-block:: php

    <?php
    $url = 'http://127.0.0.1:8000/dbmail/api/';
    $data = array(
        'api_key' => 'ZzriUzE', 'slug' => 'welcome', 'recipient' => 'root@local.host');
    $options = array(
            'http' => array(
            'header'  => "Content-type: application/x-www-form-urlencoded\r\n",
            'method'  => 'POST',
            'content' => http_build_query($data),
        )
    );

    file_get_contents($url, false, stream_context_create($options));


*using Curl*

.. code-block:: php

    <?php
    $url = 'http://127.0.0.1:8000/dbmail/api/';
    $data = array(
        'api_key' => 'ZzriUzE', 'slug' => 'welcome', 'recipient' => 'root@local.host');

    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_POST, 1);
    curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($data));
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, 1);
    curl_setopt($ch, CURLOPT_HEADER, 0);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);

    curl_exec($ch);


Ruby example
------------

.. code-block:: ruby

    require "net/http"
    require 'net/https'
    require "uri"

    uri = URI.parse("http://127.0.0.1:8000/dbmail/api/")
    https = Net::HTTP.new(uri.host,uri.port)
    req = Net::HTTP::Post.new(uri.path)

    button = {
        "api_key" => "ZzriUzE",
        "slug" => "welcome",
        "recipient" => "root@local.host"
    }
    req.set_form_data(button)
    https.request(req)


Node.js example
---------------

.. code-block:: js

    var request = require('request');

    var uri = 'http://127.0.0.1:8000/dbmail/api/';
    var data = {
        api_key: 'ZzriUzE',
        slug: 'welcome',
        recipient: 'root@local.host'
    };

    request.post({
        headers: {'content-type': 'application/x-www-form-urlencoded'},
        url: uri, form: data
    }, function (error, response, body) {
        console.log(body);
    });
