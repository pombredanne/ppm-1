var http = require("http"),
    request = require('request'),
    url = require("url"),
    path = require("path"),
    fs = require("fs");

var PACKAGES_FOLDER_NAME = "packages";
var MAP_FILE = "urlmap.json";

if (process.argv.length != 3) {
    console.log("invalid command line arguments, you should pass only a json file adress(on the registry server) containing the urls to download");
    process.exit(1);
}

// downloading urls list
var a = url.parse(process.argv[2]);
var options = {
  host: a.hostname,
  port: a.port,
  path: a.pathname
};
http.get(options, function (response) {
    var body = '';
    response.on('data', function (chunk) {
        body += chunk;
    });
    response.on('end', function () {
        process_urls(parse_remote_urllist(body));
    });
});


var process_urls = function (urls) {
    var mapfile = path.join(process.cwd(), PACKAGES_FOLDER_NAME, MAP_FILE);
    var map = {};
    if (fs.existsSync(mapfile)){
    	map = JSON.parse(fs.readFileSync(mapfile, 'utf8'));
    }
    
    var download_dir = path.join(process.cwd(), PACKAGES_FOLDER_NAME);

    for (var i = 0; i < urls.length; i++) {
        if (map[urls[i]] == undefined) {
            download(urls[i], download_dir, function (url, filename) {
                map[url] = filename;
                fs.writeFileSync(mapfile, JSON.stringify(map));
            });
        }
    }
}

var parse_remote_urllist = function(respBody) {
	data = JSON.parse(respBody);
	urls = [];
	for (var i =0; i < data.rows.length; i++) {
		urls = urls.concat(data.rows[i].value);
	}
	return urls;
}

var download = function (url, download_dir, cb) {
	console.log("downloading ",url)
    var req = request(url);
    req.on('response', function (res) {
        if (res.headers["Content-Disposition"])
            var filename = res.headers["Content-Disposition"]
        else
            var filename = path.basename(url)
        savePath = path.join(download_dir, filename)
        //TODO: check for file extension
        //TODO : check for file existence
        fileStream = fs.createWriteStream(savePath)
        res.pipe(fileStream);
        fileStream.on('finish', function () {
            fileStream.close();
            cb(url, filename);
        });

    });
}